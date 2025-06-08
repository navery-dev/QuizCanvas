import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError, DatabaseError, connection
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Max, Count, FloatField
from django.db.models.functions import Cast
from django.core.validators import validate_email
import re
import os

import jwt

from .models import *
from .utils.file_processors import *
from .services.s3_service import get_s3_service

# Configure logging
logger = logging.getLogger(__name__)

# Import test classes
from .tests import *

class APIResponse:
    """Standardized API response helper"""
    @staticmethod
    def success(data=None, message="Success", status=200):
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if data:
            response['data'] = data
        return JsonResponse(response, status=status)
    
    @staticmethod
    def error(message, error_code=None, status=400, details=None):
        response = {
            'success': False,
            'error': message,
            'timestamp': datetime.now().isoformat()
        }
        if error_code:
            response['error_code'] = error_code
        if details:
            response['details'] = details
        return JsonResponse(response, status=status)

# Utility

def calculate_mastery_level(score):
    """Calculate mastery level based on score"""
    if score >= 90:
        return "Expert"
    elif score >= 80:
        return "Advanced"
    elif score >= 70:
        return "Intermediate"
    elif score >= 60:
        return "Beginner"
    else:
        return "Needs Practice"

def generate_jwt_token(user: Users) -> str:
    """Generate JWT token for user authentication"""
    payload = {
        'user_id': user.userID,
        'username': user.userName,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValidationError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValidationError("Invalid token")

def jwt_required(view_func):
    """Require JWT authentication"""
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return APIResponse.error(
                'Authorization token required',
                error_code='NO_TOKEN',
                status=401
            )
        
        token = auth_header.split(' ')[1]
        
        # Test Case ID: 30
        auth_tests = AuthenticationVerificationTests()
        token_test = auth_tests.test_token_validity(token)
        
        if not token_test['success']:
            # Return error with redirect info if token is invalid/expired
            return JsonResponse(token_test, status=401)
        
        # Test if user session exists
        session_test = auth_tests.test_user_session_exists(token_test['user_id'])
        if not session_test['success']:
            return JsonResponse(session_test, status=401)
        
        # If all tests pass, set user and continue
        request.user = session_test['user']
        return view_func(request, *args, **kwargs)
    return wrapper

## User Management
# Authentication
@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    """
    Test Case ID: 1, 19 - Register New User Account + Cancel Registration Process
    Register a new user with validation and cancellation handling
    """
    try:
        data = json.loads(request.body)
        
        # Check for cancellation flag
        if data.get('action') == 'cancel':
            # RUN TESTS - Test Case ID: 19
            cancellation_tests = RegistrationCancellationTests()
            
            # Test cancellation safety
            cancellation_test = cancellation_tests.test_registration_cancellation(data.get('form_data'))
            
            # Test data cleanup
            cleanup_test = cancellation_tests.test_form_data_cleanup(data.get('session_data'))
            
            return APIResponse.success(
                data={
                    'action': 'cancelled',
                    'cancellation_safe': cancellation_test.get('cancellation_safe', True),
                    'data_cleared': cleanup_test.get('cleanup_successful', True),
                    'session_cleared': cleanup_test.get('session_cleared', True)
                },
                message='Registration cancelled successfully'
            )
        
        # Normal registration process continues...
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # Basic validation
        if not all([username, email, password]):
            return APIResponse.error(
                'Username, email, and password are required',
                error_code='MISSING_FIELDS'
            )
        
        # Test Case ID: 1 - existing registration tests
        test_result = run_registration_tests(username, email, password)
        if not test_result['success']:
            status_code = 500 if test_result.get('error_code') == 'DB_ERROR' else 400
            return JsonResponse(test_result, status=status_code)
        
        # If all tests pass, proceed with registration
        hashed_password = make_password(password)
        
        with transaction.atomic():
            user = Users.objects.create(
                userName=username,
                email=email,
                password=hashed_password
            )
        
        logger.info(f"New user registered: {username}")
        token = generate_jwt_token(user)
        
        return APIResponse.success(
            data={
                'user_id': user.userID,
                'username': user.userName,
                'email': user.email,
                'token': token
            },
            message='User registered successfully',
            status=201
        )
        
    except json.JSONDecodeError:
        return APIResponse.error(
            'Invalid JSON data',
            error_code='INVALID_JSON'
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    """
    Test Case ID: 2 - Authenticate User Login
    Authenticate user and return JWT token with testing
    """
    try:
        data = json.loads(request.body)
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return APIResponse.error(
                'Username and password are required',
                error_code='MISSING_CREDENTIALS'
            )
        
        # Test Case ID: 2
        auth_tests = UserAuthenticationTests()
        
        credential_test = auth_tests.test_user_exists_and_credentials_valid(username, password)
        if not credential_test['success']:
            status_code = 401 if credential_test.get('error_code') == 'INVALID_CREDENTIALS' else 500
            return JsonResponse(credential_test, status=status_code)
        
        # Test session creation
        session_test = auth_tests.test_session_creation(credential_test['user'])
        if not session_test['success']:
            return JsonResponse(session_test, status=500)
        
        try:
            rate_test = auth_tests.test_login_rate_limiting(username, request.META.get('REMOTE_ADDR'))
            if not rate_test['success']:
                return JsonResponse(rate_test, status=429)
        except AttributeError:
            logger.warning("Rate limiting test not implemented yet") #not implemented yet
        
        user = credential_test['user']
        token = session_test['token']
        
        logger.info(f"User logged in: {username}")
        
        return APIResponse.success(
            data={
                'user_id': user.userID,
                'username': user.userName,
                'email': user.email,
                'token': token
            },
            message='Login successful'
        )
        
    except json.JSONDecodeError:
        return APIResponse.error(
            'Invalid JSON data',
            error_code='INVALID_JSON'
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def logout_user(request):
    """
    Test Case ID: 38 - User log out
    Logout user and invalidate session
    """
    try:
        user = request.user
        
        # Session validation before logout
        auth_tests = AuthenticationVerificationTests()
        session_test = auth_tests.test_user_session_exists(user.userID)
        
        if not session_test['success']:
            # User session already invalid, but still allow logout
            logger.warning(f"Logout attempted for invalid session: {user.userID}")
        
        # Log the successful logout
        logger.info(f"User {user.userName} logged out")
        
        return APIResponse.success(
            message='Logged out successfully'
        )
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        # Even if there's an error, should allow logout
        return APIResponse.success(
            message='Logged out successfully'
        )
    
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_user_account_save_options(request):
    """
    Test Case ID: 24 - User Account Save/Cancel Options
    Get available save options for user account modifications
    """
    try:
        user = request.user
        
        # Test Case ID: 24
        account_tests = UserAccountSaveTests()
        
        # Test current user data validation
        current_data = {
            'username': user.userName,
            'email': user.email
        }
        
        # Test save validation with current data
        validation_test = account_tests.test_profile_save_validation(
            user.userID, 
            current_data
        )
        
        # Test cancel functionality
        cancel_test = account_tests.test_cancel_changes_restoration(
            current_data, 
            current_data
        )
        
        return APIResponse.success(
            data={
                'user_info': {
                    'user_id': user.userID,
                    'current_username': user.userName,
                    'current_email': user.email
                },
                'save_options': {
                    'can_save': validation_test.get('ready_to_save', True),
                    'validation_passed': validation_test.get('validation_passed', True),
                    'can_cancel': cancel_test.get('restoration_successful', True)
                },
                'validation_rules': {
                    'username': {
                        'max_length': 10,
                        'required': True,
                        'unique': True
                    },
                    'email': {
                        'max_length': 50,
                        'required': True,
                        'unique': True,
                        'format': 'valid_email'
                    }
                },
                'available_actions': [
                    {
                        'action': 'save',
                        'method': 'PATCH',
                        'endpoint': '/api/auth/profile/',
                        'description': 'Save profile changes'
                    },
                    {
                        'action': 'cancel',
                        'method': 'GET',
                        'endpoint': '/api/auth/save-options/',
                        'description': 'Cancel changes and restore original data'
                    }
                ]
            },
            message='User account save options retrieved'
        )
        
    except Exception as e:
        logger.error(f"Error getting user save options: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

# Password Management
@csrf_exempt
@require_http_methods(["POST"])
def reset_password_request(request):
    """
    Test Case ID: 4, 12 - Reset Forgotten Password + Email Notification Delivery
    Note: Email functionality will be implemented in future version
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return APIResponse.error(
                'Email is required',
                error_code='MISSING_EMAIL'
            )
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return APIResponse.error(
                'Invalid email format',
                error_code='INVALID_EMAIL'
            )
        
        # Check if user exists
        try:
            user = Users.objects.get(email=email)
            logger.info(f"Password reset requested for existing user: {email}")
        except Users.DoesNotExist:
            logger.warning(f"Password reset requested for non-existent email: {email}")
        
        # For now, return success message and log the request
        # TODO: Implement email service in future version
        logger.info(f"Password reset request logged for {email}. Email service not yet implemented.")
        
        return APIResponse.success(
            message='Password reset request received. Email functionality will be available in a future version. Please contact an administrator for password reset assistance.'
        )
        
    except json.JSONDecodeError:
        return APIResponse.error(
            'Invalid JSON data',
            error_code='INVALID_JSON'
        )
    except Exception as e:
        logger.error(f"Error processing password reset request: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )
    
@csrf_exempt
@require_http_methods(["POST"])
def reset_password_confirm(request):
    """
    Test Case ID: 4 - Reset Forgotten Password
    Confirm password reset with token
    """
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not token or not new_password:
            return APIResponse.error(
                'Token and new password are required',
                error_code='MISSING_FIELDS'
            )
        
        # Verify reset token
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            if payload.get('purpose') != 'password_reset':
                raise ValidationError('Invalid token purpose')
                
            user_id = payload['user_id']
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValidationError):
            return APIResponse.error(
                'Invalid or expired reset token',
                error_code='INVALID_TOKEN'
            )
        
        # Get user
        try:
            user = Users.objects.get(userID=user_id)
        except Users.DoesNotExist:
            return APIResponse.error(
                'User not found',
                error_code='USER_NOT_FOUND',
                status=404
            )
        
        # RUN TEST - Validate new password strength
        user_tests = UserRegistrationTests()
        password_test = user_tests.test_password_strength(new_password)
        if not password_test['success']:
            return JsonResponse(password_test, status=400)
        
        # Update password
        try:
            user.password = make_password(new_password)
            user.save()
            
            logger.info(f"Password reset completed for user {user.userName}")
            
            return APIResponse.success(
                message='Password reset successfully. You can now log in with your new password.'
            )
            
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return APIResponse.error(
                'Failed to update password',
                error_code='UPDATE_FAILED',
                status=500
            )
        
    except json.JSONDecodeError:
        return APIResponse.error(
            'Invalid JSON data',
            error_code='INVALID_JSON'
        )
    except Exception as e:
        logger.error(f"Error confirming password reset: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

# Profile Management
@csrf_exempt
@require_http_methods(["GET", "PATCH"])
@jwt_required
def update_user_profile(request):
    """
    Test Case ID: 3 - Modify User Account Information
    Get or update user profile information
    """
    try:
        user = request.user
        
        # return user profile data
        if request.method == "GET":
            return APIResponse.success(
                data={
                    'user_id': user.userID,
                    'username': user.userName,
                    'email': user.email,
                    'dateJoined': user.dateJoined.isoformat(),
                },
                message='User profile retrieved successfully'
            )
        
        data = json.loads(request.body)
        
        # Extract fields to update
        new_username = data.get('username', '').strip()
        new_email = data.get('email', '').strip()
        
        updated_fields = []
        
        user_tests = UserRegistrationTests()
        
        # Validate and update username if provided
        if new_username and new_username != user.userName:
            # Test username length
            if len(new_username) > 10:
                return APIResponse.error(
                    'Username must be 10 characters or less',
                    error_code='USERNAME_TOO_LONG'
                )
            
            # RUN TEST - Check if username already exists
            username_test = user_tests.test_username_already_exists(new_username, user.userID)
            if not username_test['success']:
                return JsonResponse(username_test, status=400)
            
            user.userName = new_username
            updated_fields.append('username')
        
        # Validate and update email if provided
        if new_email and new_email != user.email:
            # Test email length
            if len(new_email) > 50:
                return APIResponse.error(
                    'Email must be 50 characters or less',
                    error_code='EMAIL_TOO_LONG'
                )
            
            # Validate email format
            try:
                validate_email(new_email)
            except ValidationError:
                return APIResponse.error(
                    'Invalid email format',
                    error_code='INVALID_EMAIL'
                )
            
            # RUN TEST - Check if email already exists
            email_test = user_tests.test_email_already_exists(new_email, user.userID)
            if not email_test['success']:
                return JsonResponse(email_test, status=400)
            
            user.email = new_email
            updated_fields.append('email')
        
        # Save changes if any
        if updated_fields:
            try:
                user.save()
                logger.info(f"User {user.userID} updated profile fields: {', '.join(updated_fields)}")
                
                return APIResponse.success(
                    data={
                        'user_id': user.userID,
                        'username': user.userName,
                        'email': user.email,
                        'dateJoined': user.dateJoined.isoformat(),
                        'updated_fields': updated_fields
                    },
                    message='Profile updated successfully'
                )
            except Exception as e:
                logger.error(f"Error saving user profile: {e}")
                return APIResponse.error(
                    'Failed to update profile',
                    error_code='SAVE_FAILED',
                    status=500
                )
        else:
            return APIResponse.success(
                message='No changes detected'
            )
        
    except json.JSONDecodeError:
        return APIResponse.error(
            'Invalid JSON data',
            error_code='INVALID_JSON'
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )
    
## File & Quiz Management
#File Upload
@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_quiz_file(request):
    """
    Test Case IDs: 5, 6, 7, 20, 35 - File Upload Operations with enhanced testing
    """
    try:
        if 'file' not in request.FILES:
            return APIResponse.error(
                'No file uploaded',
                error_code='NO_FILE'
            )
        
        uploaded_file = request.FILES['file']
        user = request.user
        
        logger.info(f"Processing file upload: {uploaded_file.name} by user {user.userName}")
        
        # Store original file content before processing
        uploaded_file.seek(0)
        original_file_content = uploaded_file.read()
        logger.info(f"Read {len(original_file_content)} bytes from uploaded file")
        
        # Reset for processing
        uploaded_file.seek(0)
        
        # RUN FILE UPLOAD TESTS
        from .tests import run_file_upload_tests
        
        upload_test_result = run_file_upload_tests(uploaded_file, user)
        if not upload_test_result['success']:
            logger.warning(f"File upload test failed: {upload_test_result['error']}")
            return APIResponse.error(
                upload_test_result['error'],
                error_code=upload_test_result.get('error_code', 'UPLOAD_TEST_FAILED'),
                status=400
            )
        
        logger.info("File upload tests passed, proceeding with file processing")
        
        # Reset again before processing
        uploaded_file.seek(0)
        
        # Process the file using file processors
        try:
            questions_data, metadata = process_quiz_file(uploaded_file)
            logger.info(f"File processed successfully: {len(questions_data)} questions found")
        except ValidationError as e:
            error_message = str(e.message) if hasattr(e, 'message') else str(e)
            logger.warning(f"File processing error: {error_message}")
            return APIResponse.error(
                error_message,
                error_code='FILE_PROCESSING_ERROR'
            )
        except Exception as e:
            logger.error(f"Unexpected file processing error: {e}")
            return APIResponse.error(
                f'File processing failed: {str(e)}',
                error_code='FILE_PROCESSING_ERROR'
            )
        
        # Create database records and upload to S3
        try:
            with transaction.atomic():
                # Create File record
                file_record = File.objects.create(
                    userID=user,
                    fileName=uploaded_file.name[:50],
                    filePath="",
                    fileType=uploaded_file.name.split('.')[-1].lower()[:4],
                    uploadDate=datetime.now()
                )
                logger.info(f"Created file record: {file_record.fileID}")
                
                # Upload to S3 using original file content
                try:
                    from io import BytesIO
                    
                    # Create a file-like object from the original content
                    file_for_s3 = BytesIO(original_file_content)
                    file_for_s3.name = uploaded_file.name
                    file_for_s3.content_type = uploaded_file.content_type
                    file_for_s3.size = len(original_file_content)
                    
                    logger.info(f"Uploading {len(original_file_content)} bytes to S3")
                    
                    s3_service = get_s3_service()
                    s3_result = s3_service.upload_quiz_file(
                        file_for_s3, 
                        user.userID, 
                        uploaded_file.name
                    )
                    
                    # Update file record with S3 path
                    file_record.filePath = s3_result['s3_key'][:100]
                    file_record.save()
                    
                    logger.info(f"File uploaded to S3 successfully: {s3_result['s3_key']}")
                    
                except Exception as s3_error:
                    logger.error(f"S3 upload failed: {s3_error}")
                    # Fail the upload if S3 fails
                    raise Exception(f"File storage failed: {str(s3_error)}. S3 upload is required for file processing.")
                
                quiz_title = request.POST.get('quiz_title', uploaded_file.name.split('.')[0])[:50]
                quiz_description = request.POST.get('quiz_description', 
                                                 f"Quiz imported from {uploaded_file.name}")[:200]
                
                quiz = Quiz.objects.create(
                    fileID=file_record,
                    title=quiz_title,
                    description=quiz_description
                )
                logger.info(f"Created quiz: {quiz.quizID}")
                
                # Create sections and questions
                sections_created = {}
                questions_created = []
                
                for question_data in questions_data:
                    # Get or create section
                    section_name = question_data['section'][:50] if question_data['section'] else 'General'
                    if section_name not in sections_created:
                        section, created = Section.objects.get_or_create(
                            quizID=quiz,
                            sectionName=section_name,
                            defaults={'sectionDesc': f"Questions for {section_name}"[:200]}
                        )
                        sections_created[section_name] = section
                    else:
                        section = sections_created[section_name]
                    
                    # Create question
                    question = Question.objects.create(
                        quizID=quiz,
                        sectionID=section,
                        questionText=question_data['question_text'][:500],
                        answerOptions=question_data['answer_options'],
                        answerIndex=question_data['answer_index']
                    )
                    questions_created.append(question)
                
                logger.info(f"Successfully created {len(questions_created)} questions")
                
                # RUN FILE CONFIRMATION TESTS
                confirmation_tests = FileConfirmationTests()
                confirmation_test = confirmation_tests.test_upload_confirmation_data(
                    file_record.fileID, 
                    user.userID
                )
                
                if not confirmation_test['success']:
                    logger.warning(f"File confirmation test failed: {confirmation_test}")

        except Exception as e:
            logger.error(f"Error during file upload processing: {e}")
            return APIResponse.error(
                f'Upload processing failed: {str(e)}',
                error_code='PROCESSING_FAILED',
                status=500
            )
        
        # Return success response with confirmation data
        confirmation_data = confirmation_test.get('confirmation_data', {}) if 'confirmation_test' in locals() else {}
        
        return APIResponse.success(
            data={
                'file_id': file_record.fileID,
                'quiz_id': quiz.quizID,
                'quiz_title': quiz.title,
                'total_questions': len(questions_created),
                'sections': list(sections_created.keys()),
                'metadata': metadata,
                's3_info': {
                    'key': s3_result['s3_key'],
                    'size': s3_result['file_size']
                },
                'confirmation': confirmation_data,
                'tests_passed': upload_test_result['success']
            },
            message='File uploaded and processed successfully',
            status=201
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

# Quiz Operations
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_user_quizzes(request):
    """
    Get all quizzes for the authenticated user
    """
    try:
        user = request.user
        
        # Optimize database queries with select_related
        files = File.objects.filter(userID=user).select_related('userID')
        
        quizzes_data = []
        for file in files:
            quizzes = Quiz.objects.filter(fileID=file).select_related('fileID')
            for quiz in quizzes:
                # Count questions
                question_count = Question.objects.filter(quizID=quiz).count()
                
                # Get sections
                sections = Section.objects.filter(quizID=quiz).values_list('sectionName', flat=True)
                
                quizzes_data.append({
                    'quiz_id': quiz.quizID,
                    'title': quiz.title,
                    'description': quiz.description,
                    'file_name': file.fileName,
                    'upload_date': file.uploadDate.isoformat(),
                    'question_count': question_count,
                    'sections': list(sections)
                })
        
        return APIResponse.success(
            data={
                'quizzes': quizzes_data,
                'total_count': len(quizzes_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting user quizzes: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_timed_quiz_status(request, attempt_id):
    """
    Test Case ID: 17 - Timed Quiz Execution
    Get status of a timed quiz attempt
    """
    try:
        user = request.user
        
        # Verify attempt belongs to user
        try:
            quiz_attempt = QuizAttempt.objects.get(attemptID=attempt_id, userID=user)
        except QuizAttempt.DoesNotExist:
            return APIResponse.error(
                'Quiz attempt not found',
                error_code='ATTEMPT_NOT_FOUND',
                status=404
            )
        
        # RUN TESTS - Test Case ID: 17
        timing_tests = TimedQuizTests()
        
        # Test time limit enforcement
        time_limit_test = timing_tests.test_quiz_time_limit_enforcement(attempt_id, 30)  # 30 minutes default
        
        # Test timer display
        timer_test = timing_tests.test_timer_display_accuracy(attempt_id)
        
        return APIResponse.success(
            data={
                'attempt_id': attempt_id,
                'time_status': {
                    'elapsed_minutes': time_limit_test.get('elapsed_minutes', 0),
                    'remaining_minutes': time_limit_test.get('remaining_minutes', 0),
                    'time_limit_exceeded': time_limit_test.get('time_limit_exceeded', False),
                    'should_auto_submit': time_limit_test.get('should_auto_submit', False)
                },
                'timer_display': timer_test.get('timer_display', '00:00'),
                'timer_accurate': timer_test.get('timer_accurate', True)
            },
            message='Timed quiz status retrieved'
        )
        
    except Exception as e:
        logger.error(f"Error getting timed quiz status: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_quiz_details(request, quiz_id):
    """
    Get detailed information about a specific quiz including sections and questions
    """
    try:
        user = request.user
        
        # RUN TESTS - Quiz Access Permission
        quiz_tests = QuizAttemptTests()
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        if not access_test['success']:
            status_code = 404 if access_test.get('error_code') == 'QUIZ_NOT_FOUND' else 403
            return JsonResponse(access_test, status=status_code)
        
        quiz = access_test['quiz']
        
        # Get sections with questions
        sections_data = []
        sections = Section.objects.filter(quizID=quiz).prefetch_related('question_set').order_by('sectionName')
        
        for section in sections:
            questions = section.question_set.all().order_by('questionID')
            questions_data = []
            
            for question in questions:
                questions_data.append({
                    'question_id': question.questionID,
                    'text': question.questionText,
                    'options': question.answerOptions,
                    'section': section.sectionName
                })
            
            sections_data.append({
                'section_id': section.sectionID,
                'name': section.sectionName,
                'description': section.sectionDesc or '',
                'question_count': len(questions_data),
                'questions': questions_data
            })
        
        # Get user's progress on this quiz
        user_progress = Progress.objects.filter(userID=user, quizID=quiz).first()
        user_attempts = QuizAttempt.objects.filter(userID=user, quizID=quiz, completed=True).count()
        
        return APIResponse.success(
            data={
                'quiz': {
                    'quiz_id': quiz.quizID,
                    'title': quiz.title,
                    'description': quiz.description or '',
                    'total_questions': sum(len(s['questions']) for s in sections_data),
                    'total_sections': len(sections_data),
                    'file_name': quiz.fileID.fileName,
                    'upload_date': quiz.fileID.uploadDate.isoformat(),
                    'sections': sections_data
                },
                'user_progress': {
                    'attempts_count': user_attempts,
                    'best_score': user_progress.bestScore if user_progress else None,
                    'last_attempt': user_progress.lastAttemptDate.isoformat() if user_progress and user_progress.lastAttemptDate else None,
                    'mastery_level': user_progress.masteryLevel if user_progress else 'Not Started'
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting quiz details: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["PATCH"])
@jwt_required
def update_quiz_title(request, quiz_id):
    """
    Test Case ID: 25 - Quiz Title Edit Functionality with enhanced testing
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        new_title = data.get('title', '').strip()
        if not new_title:
            return APIResponse.error(
                'Quiz title is required',
                error_code='MISSING_TITLE'
            )
        
        # RUN TESTS - Test Case ID: 25
        test_result = run_quiz_title_edit_tests(user.userID, quiz_id, new_title)
        if not test_result['success']:
            status_code = 404 if test_result.get('error_code') == 'QUIZ_NOT_FOUND' else 400
            return JsonResponse(test_result, status=status_code)
        
        # Get quiz from previous test
        quiz_tests = QuizAttemptTests()
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        quiz = access_test['quiz']
        old_title = quiz.title
        
        # Update the title
        try:
            quiz.title = test_result['cleaned_title']
            quiz.save()
            
            logger.info(f"User {user.userName} updated quiz title from '{old_title}' to '{new_title}'")
            
            return APIResponse.success(
                data={
                    'quiz_id': quiz.quizID,
                    'old_title': old_title,
                    'new_title': quiz.title
                },
                message='Quiz title updated successfully'
            )
            
        except Exception as e:
            logger.error(f"Error updating quiz title: {e}")
            return APIResponse.error(
                'Failed to update quiz title',
                error_code='SAVE_FAILED',
                status=500
            )
        
    except json.JSONDecodeError:
        return APIResponse.error(
            'Invalid JSON data',
            error_code='INVALID_JSON'
        )
    except Exception as e:
        logger.error(f"Error in update quiz title: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required  
def delete_quiz(request, quiz_id):
    """
    Test Case ID: 8 - Remove Quiz and Associated Data
    Delete quiz with live validation and integrity checks
    """
    try:
        user = request.user
        
        # RUN TESTS - Quiz Access Permission
        quiz_tests = QuizAttemptTests()
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        if not access_test['success']:
            status_code = 404 if access_test.get('error_code') == 'QUIZ_NOT_FOUND' else 403
            return JsonResponse(access_test, status=status_code)
        
        quiz = access_test['quiz']
        quiz_title = quiz.title
        file_record = quiz.fileID
        
        integrity_tests = DataIntegrityTests()
        
        # Test cascade analysis
        cascade_test = integrity_tests.test_quiz_deletion_cascade(quiz_id, user.userID)
        if not cascade_test['success']:
            return JsonResponse(cascade_test, status=500)
        
        # Test foreign key constraints
        constraint_test = integrity_tests.test_foreign_key_constraints(quiz_id)
        if not constraint_test['success']:
            logger.warning(f"Data integrity issues detected for quiz {quiz_id}: {constraint_test}")
            # Continue with deletion but log the issues
        
        # Log what will be deleted for audit trail
        deletion_info = cascade_test.get('related_data_counts', {})
        logger.info(f"Deleting quiz {quiz_id} will cascade to: {deletion_info}")
        
        # Delete quiz and all associated data
        with transaction.atomic():
            # Delete in order to avoid foreign key constraints
            Answer.objects.filter(attemptID__quizID=quiz).delete()
            QuizAttempt.objects.filter(quizID=quiz).delete()
            Progress.objects.filter(quizID=quiz).delete()
            Question.objects.filter(quizID=quiz).delete()
            Section.objects.filter(quizID=quiz).delete()
            
            # Delete the quiz itself
            quiz.delete()
            
            # Optionally delete the file record if no other quizzes use it
            if not Quiz.objects.filter(fileID=file_record).exists():
                # Also delete from S3 if needed
                try:
                    s3_service = get_s3_service()
                    s3_service.delete_file(file_record.filePath)
                except Exception as s3_error:
                    logger.warning(f"Failed to delete S3 file: {s3_error}")
                
                file_record.delete()
            
            logger.info(f"User {user.userName} deleted quiz: {quiz_title}")
        
        return APIResponse.success(
            data={
                'deleted_quiz': quiz_title,
                'cascade_summary': deletion_info,
                'integrity_score': cascade_test.get('data_integrity_score', 100)
            },
            message=f'Quiz "{quiz_title}" and all associated data deleted successfully'
        )
        
    except Exception as e:
        logger.error(f"Error deleting quiz: {e}")
        return APIResponse.error(
            'Unable to delete quiz. Please try again.',
            error_code='DELETE_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_quiz_sections(request, quiz_id):
    """
    Test Case ID: 31 - Quiz Sections Retrieval
    Get sections for a specific quiz
    """
    try:
        user = request.user
        
        # RUN TESTS - Quiz Access Permission
        quiz_tests = QuizAttemptTests()
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        if not access_test['success']:
            status_code = 404 if access_test.get('error_code') == 'QUIZ_NOT_FOUND' else 403
            return JsonResponse(access_test, status=status_code)
        
        quiz = access_test['quiz']
        
        # Get sections with question counts
        sections = Section.objects.filter(quizID=quiz).annotate(
            question_count=Count('question')
        ).order_by('sectionName')
        
        sections_data = []
        for section in sections:
            sections_data.append({
                'section_id': section.sectionID,
                'name': section.sectionName,
                'description': section.sectionDesc or '',
                'question_count': section.question_count
            })
        
        return APIResponse.success(
            data={
                'quiz_title': quiz.title,
                'sections': sections_data,
                'total_sections': len(sections_data),
                'total_questions': sum(s['question_count'] for s in sections_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting quiz sections: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_section_questions(request, quiz_id, section_id):
    """
    Get questions for a specific section within a quiz
    """
    try:
        user = request.user
        
        # RUN TESTS - Quiz Access Permission
        quiz_tests = QuizAttemptTests()
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        if not access_test['success']:
            status_code = 404 if access_test.get('error_code') == 'QUIZ_NOT_FOUND' else 403
            return JsonResponse(access_test, status=status_code)
        
        quiz = access_test['quiz']
        
        # Verify section exists
        try:
            section = Section.objects.get(sectionID=section_id, quizID=quiz)
        except Section.DoesNotExist:
            return APIResponse.error(
                'Section not found',
                error_code='SECTION_NOT_FOUND',
                status=404
            )
        
        # Get questions for this section
        questions = Question.objects.filter(sectionID=section).order_by('questionID')
        questions_data = []
        
        for question in questions:
            questions_data.append({
                'question_id': question.questionID,
                'text': question.questionText,
                'options': question.answerOptions,
                'option_count': len(question.answerOptions)
            })
        
        return APIResponse.success(
            data={
                'section': {
                    'section_id': section.sectionID,
                    'name': section.sectionName,
                    'description': section.sectionDesc or ''
                },
                'quiz_title': quiz.title,
                'questions': questions_data,
                'question_count': len(questions_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting section questions: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

##Quiz Taking Functions
# Quiz Attempt
@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def start_quiz_attempt(request, quiz_id):
    """
    Test Case ID: 32 - Concurrent User Attempts
    Start a new quiz attempt for the authenticated user
    """
    try:
        user = request.user
        
        # RUN TESTS - Test Case ID: 32
        quiz_tests = QuizAttemptTests()
        
        # Test quiz access permission
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        if not access_test['success']:
            status_code = 404 if access_test.get('error_code') == 'QUIZ_NOT_FOUND' else 403
            return JsonResponse(access_test, status=status_code)
        
        # Test for concurrent attempts
        concurrent_test = quiz_tests.test_concurrent_attempts(user.userID, quiz_id)
        if not concurrent_test['success']:
            return JsonResponse(concurrent_test, status=409)
        
        # If all tests pass, create new quiz attempt
        quiz = access_test['quiz']
        
        with transaction.atomic():
            quiz_attempt = QuizAttempt.objects.create(
                userID=user,
                quizID=quiz,
                startTime=timezone.now(),
                completed=False
            )
            
            # Get first question
            first_question = Question.objects.filter(quizID=quiz).first()
            if not first_question:
                return APIResponse.error(
                    'No questions found in this quiz',
                    error_code='NO_QUESTIONS'
                )
            
            total_questions = Question.objects.filter(quizID=quiz).count()
            
            logger.info(f"User {user.userName} started quiz {quiz.title}")
            
            return APIResponse.success(
                data={
                    'attempt_id': quiz_attempt.attemptID,
                    'quiz_title': quiz.title,
                    'total_questions': total_questions,
                    'first_question': {
                        'question_id': first_question.questionID,
                        'text': first_question.questionText,
                        'options': first_question.answerOptions,
                        'section': first_question.sectionID.sectionName if first_question.sectionID else 'General'
                    }
                },
                message='Quiz attempt started successfully',
                status=201
            )
            
    except Exception as e:
        logger.error(f"Error starting quiz attempt: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_quiz_question(request, attempt_id, question_number):
    """
    Test Case ID: 26 - Question Display in Quiz
    Get a specific question from a quiz attempt
    """
    try:
        user = request.user
        
        # Verify quiz attempt belongs to user
        try:
            quiz_attempt = QuizAttempt.objects.select_related('userID', 'quizID').get(
                attemptID=attempt_id, 
                userID=user
            )
        except QuizAttempt.DoesNotExist:
            return APIResponse.error(
                'Quiz attempt not found',
                error_code='ATTEMPT_NOT_FOUND',
                status=404
            )
        
        if quiz_attempt.completed:
            return APIResponse.error(
                'Quiz attempt already completed',
                error_code='ATTEMPT_COMPLETED'
            )
        
        nav_tests = QuizNavigationTests()
        bounds_test = nav_tests.test_quiz_navigation_bounds(attempt_id, question_number)
        if not bounds_test['success']:
            return JsonResponse(bounds_test, status=400)
        
        # Get all questions for this quiz in order
        questions = Question.objects.filter(
            quizID=quiz_attempt.quizID
        ).select_related('sectionID').order_by('questionID')
        
        total_questions = questions.count()
        
        # Get the specific question
        question = questions[question_number - 1]
        
        # Check if user already answered this question
        existing_answer = Answer.objects.filter(
            attemptID=quiz_attempt,
            questionID=question
        ).first()
        
        return APIResponse.success(
            data={
                'question': {
                    'question_id': question.questionID,
                    'question_number': question_number,
                    'text': question.questionText,
                    'options': question.answerOptions,
                    'section': question.sectionID.sectionName if question.sectionID else 'General'
                },
                'progress': {
                    'current_question': question_number,
                    'total_questions': total_questions,
                    'percentage': round((question_number / total_questions) * 100, 1)
                },
                'previous_answer': existing_answer.selectedOption if existing_answer else None,
                'navigation': bounds_test.get('navigation_options', {})
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting quiz question: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_randomized_quiz_questions(request, quiz_id):
    """
    Test Case ID: 13 - Question Randomization
    Get quiz questions in randomized order
    """
    try:
        user = request.user
        
        # Verify quiz access
        quiz_tests = QuizAttemptTests()
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        if not access_test['success']:
            status_code = 404 if access_test.get('error_code') == 'QUIZ_NOT_FOUND' else 403
            return JsonResponse(access_test, status=status_code)
        
        # RUN TESTS - Test Case ID: 13
        randomization_tests = QuestionRandomizationTests()
        randomization_test = randomization_tests.test_question_order_randomization(quiz_id)
        
        if not randomization_test['success']:
            return JsonResponse(randomization_test, status=400)
        
        return APIResponse.success(
            data={
                'quiz_id': quiz_id,
                'randomization_available': randomization_test.get('randomization_working', False),
                'total_questions': randomization_test.get('total_questions', 0),
                'sample_order': randomization_test.get('sample_randomized_order', []),
                'original_order': randomization_test.get('original_order', [])
            },
            message='Question randomization test completed'
        )
        
    except Exception as e:
        logger.error(f"Error in question randomization: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def submit_quiz_answer(request, attempt_id, question_id):
    """
    Test Case ID: 9 - Answer Quiz Question
    Submit an answer for a quiz question
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Extract user input
        selected_option = data.get('selected_option')
        response_time = data.get('response_time', 0)
        
        # Basic validation
        if selected_option is None:
            return APIResponse.error(
                'selected_option is required',
                error_code='MISSING_ANSWER'
            )
        
        # Verify quiz attempt belongs to user
        try:
            quiz_attempt = QuizAttempt.objects.select_related('userID', 'quizID').get(
                attemptID=attempt_id, 
                userID=user
            )
        except QuizAttempt.DoesNotExist:
            return APIResponse.error(
                'Quiz attempt not found',
                error_code='ATTEMPT_NOT_FOUND',
                status=404
            )
        
        if quiz_attempt.completed:
            return APIResponse.error(
                'Quiz attempt already completed',
                error_code='ATTEMPT_COMPLETED'
            )
        
        # Get question and verify it belongs to this quiz
        try:
            question = Question.objects.get(questionID=question_id, quizID=quiz_attempt.quizID)
        except Question.DoesNotExist:
            return APIResponse.error(
                'Question not found in this quiz',
                error_code='QUESTION_NOT_FOUND',
                status=404
            )
        
        # RUN TESTS - Test Case ID: 9
        quiz_tests = QuizAttemptTests()
        answer_test = quiz_tests.test_answer_validation(selected_option, question)
        if not answer_test['success']:
            return JsonResponse(answer_test, status=400)
        
        # Validate response time
        if not isinstance(response_time, (int, float)) or response_time < 0:
            response_time = 0  # Default to 0 if invalid
        
        # Check if answer is correct
        is_correct = (selected_option == question.answerIndex)
        
        # Save or update answer
        with transaction.atomic():
            answer, created = Answer.objects.update_or_create(
                attemptID=quiz_attempt,
                questionID=question,
                defaults={
                    'selectedOption': selected_option,
                    'isCorrect': is_correct,
                    'responseTime': int(response_time)  # Store as integer milliseconds
                }
            )
            
            action = "answered" if created else "updated answer for"
            logger.info(f"User {user.userName} {action} question {question_id}: {'correct' if is_correct else 'incorrect'} (response time: {response_time}ms)")
        
        return APIResponse.success(
            data={
                'is_correct': is_correct,
                'correct_answer': question.answerOptions[question.answerIndex],
                'selected_answer': question.answerOptions[selected_option],
                'response_time': response_time,
                'answer_updated': not created
            },
            message='Answer submitted successfully'
        )
        
    except json.JSONDecodeError:
        return APIResponse.error(
            'Invalid JSON data',
            error_code='INVALID_JSON'
        )
    except Exception as e:
        logger.error(f"Error submitting quiz answer: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def complete_quiz_attempt(request, attempt_id):
    """
    Test Case ID: 10, 28 - Complete Quiz Attempt and Score Calculation
    Finalize quiz attempt and calculate results
    """
    try:
        user = request.user
        
        # Verify quiz attempt belongs to user
        try:
            quiz_attempt = QuizAttempt.objects.select_related('userID', 'quizID').get(
                attemptID=attempt_id, 
                userID=user
            )
        except QuizAttempt.DoesNotExist:
            return APIResponse.error(
                'Quiz attempt not found',
                error_code='ATTEMPT_NOT_FOUND',
                status=404
            )
        
        if quiz_attempt.completed:
            return APIResponse.error(
                'Quiz attempt already completed',
                error_code='ATTEMPT_ALREADY_COMPLETED'
            )
        
        # RUN TESTS - Test Case ID: 10, 28
        quiz_tests = QuizAttemptTests()
        score_test = quiz_tests.test_score_calculation(attempt_id)
        if not score_test['success']:
            return JsonResponse(score_test, status=400)
        
        # Get score calculation results
        score = score_test['score']
        correct_answers = score_test['correct_answers']
        total_questions = score_test['total_questions']
        
        # Calculate mastery level
        progress_tests = ProgressTrackingTests()
        mastery_test = progress_tests.test_mastery_level_calculation(score)
        if not mastery_test['success']:
            # Use fallback if calculation fails
            mastery_level = mastery_test.get('fallback_level', 'Beginner')
        else:
            mastery_level = mastery_test['mastery_level']
        
        # Update quiz attempt
        with transaction.atomic():
            quiz_attempt.endTime = timezone.now()
            quiz_attempt.score = score
            quiz_attempt.completed = True
            quiz_attempt.save()
            
            # Update user progress
            progress, created = Progress.objects.update_or_create(
                userID=user,
                quizID=quiz_attempt.quizID,
                defaults={
                    'attemptsCount': QuizAttempt.objects.filter(
                        userID=user, 
                        quizID=quiz_attempt.quizID,
                        completed=True
                    ).count(),
                    'bestScore': max(
                        score,
                        Progress.objects.filter(
                            userID=user, 
                            quizID=quiz_attempt.quizID
                        ).aggregate(Max('bestScore'))['bestScore__max'] or 0
                    ),
                    'lastAttemptDate': timezone.now(),
                    'masteryLevel': mastery_level
                }
            )
            
            logger.info(f"User {user.userName} completed quiz {quiz_attempt.quizID.title} with score {score}%")
        
        return APIResponse.success(
            data={
                'score': round(score, 1),
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'time_taken': str(quiz_attempt.endTime - quiz_attempt.startTime),
                'mastery_level': mastery_level,
                'quiz_title': quiz_attempt.quizID.title,
                'attempts_count': progress.attemptsCount,
                'best_score': progress.bestScore
            },
            message='Quiz completed successfully'
        )
        
    except Exception as e:
        logger.error(f"Error completing quiz attempt: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def resume_quiz_attempt(request, attempt_id):
    """
    Test Case ID: 37 - Quiz Attempt Resume with enhanced testing
    """
    try:
        user = request.user
        
        # RUN TESTS - Test Case ID: 37
        test_result = run_quiz_resume_tests(attempt_id, user.userID)
        if not test_result['success']:
            status_code = 404 if test_result.get('error_code') == 'ATTEMPT_NOT_FOUND' else 400
            return JsonResponse(test_result, status=status_code)
        
        # Get quiz attempt
        try:
            quiz_attempt = QuizAttempt.objects.select_related('userID', 'quizID').get(
                attemptID=attempt_id, 
                userID=user
            )
        except QuizAttempt.DoesNotExist:
            return APIResponse.error(
                'Quiz attempt not found',
                error_code='ATTEMPT_NOT_FOUND',
                status=404
            )
        
        # Get progress information from test results
        total_questions = Question.objects.filter(quizID=quiz_attempt.quizID).count()
        
        if test_result.get('next_question_id'):
            # Find next question to continue with
            next_question = Question.objects.get(questionID=test_result['next_question_id'])
            
            # Calculate next question number
            all_questions = Question.objects.filter(
                quizID=quiz_attempt.quizID
            ).order_by('questionID')
            
            question_number = 1
            for i, q in enumerate(all_questions, 1):
                if q.questionID == next_question.questionID:
                    question_number = i
                    break
            
            return APIResponse.success(
                data={
                    'attempt_id': quiz_attempt.attemptID,
                    'quiz_title': quiz_attempt.quizID.title,
                    'total_questions': total_questions,
                    'progress_percentage': test_result.get('progress_percentage', 0),
                    'next_question': {
                        'question_id': next_question.questionID,
                        'question_number': question_number,
                        'text': next_question.questionText,
                        'options': next_question.answerOptions,
                        'section': next_question.sectionID.sectionName if next_question.sectionID else 'General'
                    }
                },
                message='Quiz attempt resumed successfully'
            )
        else:
            # All questions answered, ready to complete
            return APIResponse.success(
                data={
                    'attempt_id': quiz_attempt.attemptID,
                    'quiz_title': quiz_attempt.quizID.title,
                    'all_answered': True,
                    'total_questions': total_questions,
                    'progress_percentage': 100,
                    'message': 'All questions answered. Ready to submit quiz.'
                },
                message='Quiz attempt resumed - ready to submit'
            )
        
    except Exception as e:
        logger.error(f"Error resuming quiz attempt: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

# Quiz History

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_user_quiz_attempts(request, quiz_id):
    """
    Get all attempts for a specific quiz by the authenticated user
    """
    try:
        user = request.user
        
        # RUN TESTS - Quiz Access Permission
        quiz_tests = QuizAttemptTests()
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        if not access_test['success']:
            status_code = 404 if access_test.get('error_code') == 'QUIZ_NOT_FOUND' else 403
            return JsonResponse(access_test, status=status_code)
        
        quiz = access_test['quiz']
        
        # Get user's attempts for this quiz - optimized query
        attempts = QuizAttempt.objects.filter(
            userID=user, 
            quizID=quiz
        ).select_related('userID', 'quizID').order_by('-startTime')
        
        attempts_data = []
        for attempt in attempts:
            # Get answer statistics for this attempt
            answers = Answer.objects.filter(attemptID=attempt)
            total_answers = answers.count()
            correct_answers = answers.filter(isCorrect=True).count()
            
            attempts_data.append({
                'attempt_id': attempt.attemptID,
                'start_time': attempt.startTime.isoformat(),
                'end_time': attempt.endTime.isoformat() if attempt.endTime else None,
                'score': attempt.score,
                'completed': attempt.completed,
                'total_answers': total_answers,
                'correct_answers': correct_answers,
                'time_taken': str(attempt.endTime - attempt.startTime) if attempt.endTime else None
            })
        
        best_score = max([a['score'] for a in attempts_data if a['score'] is not None], default=0)
        completed_attempts = len([a for a in attempts_data if a['completed']])
        
        return APIResponse.success(
            data={
                'quiz_title': quiz.title,
                'attempts': attempts_data,
                'total_attempts': len(attempts_data),
                'completed_attempts': completed_attempts,
                'best_score': best_score
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting user quiz attempts: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )
    
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_attempt_details(request, attempt_id):
    """
    Get detailed information about a specific quiz attempt
    """
    try:
        user = request.user
        
        # Verify quiz attempt belongs to user
        try:
            quiz_attempt = QuizAttempt.objects.select_related(
                'userID', 'quizID', 'quizID__fileID'
            ).get(attemptID=attempt_id, userID=user)
        except QuizAttempt.DoesNotExist:
            return APIResponse.error(
                'Quiz attempt not found',
                error_code='ATTEMPT_NOT_FOUND',
                status=404
            )
        
        # Get all answers for this attempt
        answers = Answer.objects.filter(
            attemptID=quiz_attempt
        ).select_related('questionID', 'questionID__sectionID').order_by('questionID__questionID')
        
        answer_details = []
        for answer in answers:
            question = answer.questionID
            answer_details.append({
                'question_id': question.questionID,
                'question_text': question.questionText,
                'section': question.sectionID.sectionName if question.sectionID else 'General',
                'options': question.answerOptions,
                'correct_answer_index': question.answerIndex,
                'selected_answer_index': answer.selectedOption,
                'is_correct': answer.isCorrect,
                'response_time': answer.responseTime,
                'correct_answer_text': question.answerOptions[question.answerIndex],
                'selected_answer_text': question.answerOptions[answer.selectedOption]
            })
        
        # Calculate statistics
        total_questions = len(answer_details)
        correct_answers = sum(1 for ans in answer_details if ans['is_correct'])
        total_time = quiz_attempt.endTime - quiz_attempt.startTime if quiz_attempt.endTime else None
        
        return APIResponse.success(
            data={
                'attempt': {
                    'attempt_id': quiz_attempt.attemptID,
                    'quiz_title': quiz_attempt.quizID.title,
                    'start_time': quiz_attempt.startTime.isoformat(),
                    'end_time': quiz_attempt.endTime.isoformat() if quiz_attempt.endTime else None,
                    'completed': quiz_attempt.completed,
                    'score': quiz_attempt.score,
                    'total_time': str(total_time).split('.')[0] if total_time else None
                },
                'statistics': {
                    'total_questions': total_questions,
                    'correct_answers': correct_answers,
                    'incorrect_answers': total_questions - correct_answers,
                    'accuracy': round((correct_answers / total_questions) * 100, 1) if total_questions > 0 else 0,
                    'average_response_time': round(
                        sum(ans['response_time'] for ans in answer_details) / len(answer_details)
                    ) if answer_details else 0
                },
                'answers': answer_details
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting attempt details: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

##Progress & Analytics
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_user_progress(request, quiz_id=None):
    """
    Test Case ID: 11 - Display User Progress Metrics
    Get user's progress data with live validation
    """
    try:
        user = request.user
        
        # RUN TESTS - Test Case ID: 11
        progress_tests = ProgressTrackingTests()
        
        if quiz_id:
            # Get progress for specific quiz
            progress_test = progress_tests.test_progress_data_availability(user.userID, quiz_id)
            
            if not progress_test['success']:
                return JsonResponse(progress_test, status=500)
            
            if progress_test.get('empty_state'):
                return APIResponse.success(
                    data={
                        'has_progress': False,
                        'message': progress_test['message'],
                        'empty_state': True
                    }
                )
            
            # Get actual progress data
            try:
                progress = Progress.objects.get(userID=user, quizID_id=quiz_id)
                attempts = QuizAttempt.objects.filter(
                    userID=user, 
                    quizID_id=quiz_id, 
                    completed=True
                ).order_by('-endTime')
                
                return APIResponse.success(
                    data={
                        'has_progress': True,
                        'quiz_id': quiz_id,
                        'attempts_count': progress.attemptsCount,
                        'best_score': progress.bestScore,
                        'last_attempt': progress.lastAttemptDate.isoformat(),
                        'mastery_level': progress.masteryLevel,
                        'recent_attempts': [
                            {
                                'score': attempt.score,
                                'date': attempt.endTime.isoformat(),
                                'time_taken': str(attempt.endTime - attempt.startTime)
                            } for attempt in attempts[:5]  # Last 5 attempts
                        ]
                    }
                )
                
            except Progress.DoesNotExist:
                return APIResponse.success(
                    data={
                        'has_progress': False,
                        'message': 'No progress data found for this quiz',
                        'empty_state': True
                    }
                )
        
        else:
            # Get overall progress for user across all quizzes
            all_progress = Progress.objects.filter(userID=user).select_related('quizID')
            
            if not all_progress.exists():
                return APIResponse.success(
                    data={
                        'has_progress': False,
                        'message': 'No progress data found. Take some quizzes to see your progress!',
                        'empty_state': True
                    }
                )
            
            progress_data = []
            for progress in all_progress:
                progress_data.append({
                    'quiz_id': progress.quizID.quizID,
                    'quiz_title': progress.quizID.title,
                    'attempts_count': progress.attemptsCount,
                    'best_score': progress.bestScore,
                    'last_attempt': progress.lastAttemptDate.isoformat(),
                    'mastery_level': progress.masteryLevel
                })
            
            return APIResponse.success(
                data={
                    'has_progress': True,
                    'total_quizzes': len(progress_data),
                    'progress': progress_data,
                    'overall_stats': {
                        'total_attempts': sum(p['attempts_count'] for p in progress_data),
                        'average_score': sum(p['best_score'] for p in progress_data) / len(progress_data),
                        'mastery_levels': {
                            level: len([p for p in progress_data if p['mastery_level'] == level])
                            for level in ['Expert', 'Advanced', 'Intermediate', 'Beginner', 'Needs Practice']
                        }
                    }
                }
            )
        
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_quiz_statistics(request, quiz_id):
    """
    Get detailed statistics for a quiz
    """
    try:
        user = request.user
        
        # RUN TESTS - Quiz Access Permission
        quiz_tests = QuizAttemptTests()
        access_test = quiz_tests.test_quiz_access_permission(user.userID, quiz_id)
        if not access_test['success']:
            status_code = 404 if access_test.get('error_code') == 'QUIZ_NOT_FOUND' else 403
            return JsonResponse(access_test, status=status_code)
        
        quiz = access_test['quiz']
        
        # Get quiz statistics
        total_questions = Question.objects.filter(quizID=quiz).count()
        total_attempts = QuizAttempt.objects.filter(quizID=quiz, userID=user).count()
        completed_attempts = QuizAttempt.objects.filter(
            quizID=quiz, 
            userID=user, 
            completed=True
        )
        
        if completed_attempts.exists():
            scores = [attempt.score for attempt in completed_attempts if attempt.score is not None]
            best_score = max(scores) if scores else 0
            average_score = sum(scores) / len(scores) if scores else 0
            latest_attempt = completed_attempts.order_by('-endTime').first()
        else:
            best_score = 0
            average_score = 0
            latest_attempt = None
        
        # Get section statistics
        sections = Section.objects.filter(quizID=quiz).annotate(
            question_count=Count('question')
        )
        
        section_stats = []
        for section in sections:
            # Get section-specific performance
            section_questions = Question.objects.filter(sectionID=section)
            section_answers = Answer.objects.filter(
                questionID__in=section_questions,
                attemptID__userID=user,
                attemptID__completed=True
            )
            
            if section_answers.exists():
                correct_answers = section_answers.filter(isCorrect=True).count()
                total_answers = section_answers.count()
                section_accuracy = (correct_answers / total_answers) * 100 if total_answers > 0 else 0
            else:
                section_accuracy = 0
            
            section_stats.append({
                'section_id': section.sectionID,
                'name': section.sectionName,
                'question_count': section.question_count,
                'accuracy': round(section_accuracy, 1)
            })
        
        return APIResponse.success(
            data={
                'quiz': {
                    'quiz_id': quiz.quizID,
                    'title': quiz.title,
                    'total_questions': total_questions
                },
                'user_stats': {
                    'total_attempts': total_attempts,
                    'completed_attempts': completed_attempts.count(),
                    'best_score': best_score,
                    'average_score': round(average_score, 1),
                    'latest_attempt_date': latest_attempt.endTime.isoformat() if latest_attempt else None
                },
                'section_stats': section_stats,
                'performance_trend': [
                    {
                        'attempt_number': i + 1,
                        'score': attempt.score,
                        'date': attempt.endTime.isoformat()
                    }
                    for i, attempt in enumerate(completed_attempts.order_by('endTime'))
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting quiz statistics: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )
    
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_user_dashboard(request):
    """
    Get dashboard data for the authenticated user with live validation
    """
    try:
        user = request.user
        
        # RUN TESTS - Database connectivity
        db_tests = DatabaseConnectionTests()
        db_health = db_tests.test_connection_health()
        if not db_health['success']:
            return APIResponse.error(
                'Database connectivity issue',
                error_code='DB_ERROR',
                status=503
            )
        
        # RUN TESTS - Progress data validation with correct parameters
        progress_tests = ProgressTrackingTests()
        # Pass user_id and None for quiz_id to show overall progress
        progress_availability = progress_tests.test_progress_data_availability(user.userID, None)
        
        # Get user's quiz count
        total_quizzes = Quiz.objects.filter(fileID__userID=user).count()
        
        # Get recent activity
        recent_attempts = QuizAttempt.objects.filter(
            userID=user, 
            completed=True
        ).select_related('quizID').order_by('-endTime')[:5]
        
        # Get overall progress
        all_progress = Progress.objects.filter(userID=user).select_related('quizID')
        
        # Calculate overall stats
        if all_progress.exists():
            total_attempts = sum(p.attemptsCount for p in all_progress)
            average_score = sum(p.bestScore for p in all_progress) / len(all_progress)
            mastery_distribution = {}
            for level in ['Expert', 'Advanced', 'Intermediate', 'Beginner', 'Needs Practice']:
                mastery_distribution[level] = len([p for p in all_progress if p.masteryLevel == level])
        else:
            total_attempts = 0
            average_score = 0
            mastery_distribution = {level: 0 for level in ['Expert', 'Advanced', 'Intermediate', 'Beginner', 'Needs Practice']}
        
        return APIResponse.success(
            data={
                'user': {
                    'username': user.userName,
                    'email': user.email,
                    'member_since': user.dateJoined.isoformat() if hasattr(user, 'dateJoined') else None
                },
                'stats': {
                    'total_quizzes': total_quizzes,
                    'total_attempts': total_attempts,
                    'average_score': round(average_score, 1),
                    'mastery_distribution': mastery_distribution
                },
                'recent_activity': [
                    {
                        'quiz_title': attempt.quizID.title,
                        'score': attempt.score,
                        'date': attempt.endTime.isoformat(),
                        'quiz_id': attempt.quizID.quizID
                    }
                    for attempt in recent_attempts
                ],
                'system_health': {
                    'database': 'healthy' if db_health['success'] else 'unhealthy',
                    'has_progress_data': progress_availability.get('success', False)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting user dashboard: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )
    
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_quiz_progress_bar(request, attempt_id):
    """
    Test Case ID: 21 - Quiz Results Progress Bar Display
    Get progress bar data for quiz attempt
    """
    try:
        user = request.user
        
        # Verify attempt belongs to user
        try:
            quiz_attempt = QuizAttempt.objects.get(attemptID=attempt_id, userID=user)
        except QuizAttempt.DoesNotExist:
            return APIResponse.error(
                'Quiz attempt not found',
                error_code='ATTEMPT_NOT_FOUND',
                status=404
            )
        
        # Get progress data
        total_questions = Question.objects.filter(quizID=quiz_attempt.quizID).count()
        answered_questions = Answer.objects.filter(attemptID=quiz_attempt).count()
        
        # RUN TESTS - Test Case ID: 21
        progress_tests = ProgressBarTests()
        
        # Test progress calculation
        calculation_test = progress_tests.test_progress_bar_calculation(answered_questions, total_questions)
        if not calculation_test['success']:
            return JsonResponse(calculation_test, status=400)
        
        progress_percentage = calculation_test['progress_percentage']
        
        # Test progress display
        display_test = progress_tests.test_progress_bar_display(progress_percentage)
        
        return APIResponse.success(
            data={
                'attempt_id': attempt_id,
                'progress': {
                    'current_question': answered_questions,
                    'total_questions': total_questions,
                    'percentage': progress_percentage,
                    'display_width': display_test.get('display_width', 0),
                    'display_color': display_test.get('display_color', 'blue'),
                    'display_text': display_test.get('display_text', '0%')
                }
            },
            message='Progress bar data retrieved'
        )
        
    except Exception as e:
        logger.error(f"Error getting progress bar data: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )

##Health & Status

@csrf_exempt
@require_http_methods(["GET"])
def get_faq(request):
    """
    Test Case ID: 33 - FAQ Page Access and Navigation
    Get frequently asked questions
    """
    try:
        faq_data = [
            {
                'id': 1,
                'question': 'How do I upload a quiz file?',
                'answer': 'Navigate to the upload page and select a CSV or JSON file containing your quiz questions. The file should include columns for question text, answer options, correct answer, and section.'
            },
            {
                'id': 2,
                'question': 'What file formats are supported?',
                'answer': 'QuizCanvas supports CSV and JSON file formats. CSV files should have specific column headers, while JSON files should follow our quiz structure format.'
            },
            {
                'id': 3,
                'question': 'How is my score calculated?',
                'answer': 'Your score is calculated as a percentage: (correct answers / total questions) × 100. The system tracks your best score and displays your mastery level based on performance.'
            },
            {
                'id': 4,
                'question': 'Can I retake a quiz?',
                'answer': 'Yes! You can retake any quiz multiple times. The system will track all your attempts and show your progress over time.'
            },
            {
                'id': 5,
                'question': 'What are mastery levels?',
                'answer': 'Mastery levels indicate your proficiency: Expert (90%+), Advanced (80-89%), Intermediate (70-79%), Beginner (60-69%), and Needs Practice (<60%).'
            },
            {
                'id': 6,
                'question': 'How do I delete a quiz?',
                'answer': 'Go to your quiz list, select the quiz you want to delete, and click the delete button. This will remove the quiz and all associated data permanently.'
            },
            {
                'id': 7,
                'question': 'Is my data secure?',
                'answer': 'Yes, your data is secure. We use JWT authentication, encrypted passwords, and secure cloud storage for your quiz files.'
            },
            {
                'id': 8,
                'question': 'Can I edit quiz questions after uploading?',
                'answer': 'Currently, you can edit quiz titles but not individual questions. To modify questions, you would need to upload a new file with the updated content.'
            }
        ]
        
        return APIResponse.success(
            data={
                'faqs': faq_data,
                'total_count': len(faq_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting FAQ data: {e}")
        return APIResponse.error(
            'Internal server error',
            error_code='SERVER_ERROR',
            status=500
        )


def health_check(request):
    """
    Test Case ID: 14 - Database Connection
    Live health check with database connectivity test
    
    Returns:
        JsonResponse with system health status
    """
    # RUN TESTS
    db_tests = DatabaseConnectionTests()
    
    # Test database connection
    db_health = db_tests.test_connection_health()
    
    # Test basic operations
    crud_test = db_tests.test_crud_operations()
    
    response_data = {
        'status': 'healthy' if db_health['success'] and crud_test['success'] else 'unhealthy',
        'timestamp': datetime.now().isoformat(),
        'database': {
            'connection': 'ok' if db_health['success'] else 'failed',
            'operations': 'ok' if crud_test['success'] else 'failed'
        },
        's3_configured': bool(settings.AWS_ACCESS_KEY_ID)
    }
    
    # If database tests fail, include error details
    if not db_health['success']:
        response_data['database']['connection_error'] = db_health.get('error')
    
    if not crud_test['success']:
        response_data['database']['operations_error'] = crud_test.get('error')
    
    status_code = 200 if response_data['status'] == 'healthy' else 503
    
    return JsonResponse(response_data, status=status_code)

@csrf_exempt
@require_http_methods(["GET"])
def check_system_connections(request):
    """
    Test Case IDs: 15, 16 - S3 and EC2 Connection Testing
    Check system connection health
    """
    try:
        # RUN TESTS - Test Cases ID: 15, 16
        s3_tests = S3ConnectionTests()
        ec2_tests = EC2ConnectionTests()
        
        # Test S3 connection
        s3_config_test = s3_tests.test_s3_service_initialization()
        s3_health_test = s3_tests.test_s3_connection_health()
        
        # Test EC2 deployment
        ec2_deployment_test = ec2_tests.test_ec2_deployment_status()
        ec2_resource_test = ec2_tests.test_ec2_resource_availability()
        
        system_status = {
            's3': {
                'configured': s3_config_test.get('success', False),
                'healthy': s3_health_test.get('success', False),
                'bucket_name': s3_config_test.get('bucket_name', 'Not configured')
            },
            'ec2': {
                'deployment_healthy': ec2_deployment_test.get('deployment_status') == 'healthy',
                'resources_healthy': ec2_resource_test.get('resource_healthy', False),
                'running_on_ec2': ec2_deployment_test.get('running_on_ec2', False)
            }
        }
        
        overall_healthy = (
            system_status['s3']['configured'] and 
            system_status['s3']['healthy'] and
            system_status['ec2']['deployment_healthy']
        )
        
        return APIResponse.success(
            data={
                'overall_status': 'healthy' if overall_healthy else 'degraded',
                'systems': system_status,
                'timestamp': datetime.now().isoformat()
            },
            message='System connection check completed'
        )
        
    except Exception as e:
        logger.error(f"Error checking system connections: {e}")
        return APIResponse.error(
            'System connection check failed',
            error_code='CONNECTION_CHECK_ERROR',
            status=500
        )
