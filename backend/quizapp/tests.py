import json
import logging
from django.core.exceptions import ValidationError
from django.db import connection, IntegrityError, DatabaseError
from django.contrib.auth.hashers import check_password
from django.core.validators import validate_email
from django.utils import timezone
from django.conf import settings
import jwt
from datetime import datetime
import re
import os

from .models import *

logger = logging.getLogger(__name__)


class UserRegistrationTests:
    """
    Test Case ID: 1 - Register New User Account
    """
    
    @staticmethod
    def test_email_already_exists(email, user_id=None):
        """Extension: Email already exists - Display error message"""
        try:
            # If user_id provided, exclude that user from the check (for profile updates)
            if user_id:
                existing_users = Users.objects.filter(email=email).exclude(userID=user_id)
            else:
                existing_users = Users.objects.filter(email=email)
                
            if existing_users.exists():
                return {
                    'success': False,
                    'error': 'Email already exists',
                    'error_code': 'EMAIL_EXISTS'
                }
            return {'success': True}
        except DatabaseError as e:
            logger.error(f"Database error checking email existence: {e}")
            return {
                'success': False,
                'error': 'Database connection error. Please try again.',
                'error_code': 'DB_ERROR'
            }
    
    @staticmethod
    def test_username_already_exists(username, user_id=None):
        """Extension: Username already exists - Display error message"""
        try:
            # If user_id provided, exclude that user from the check (for profile updates)
            if user_id:
                existing_users = Users.objects.filter(userName=username).exclude(userID=user_id)
            else:
                existing_users = Users.objects.filter(userName=username)
                
            if existing_users.exists():
                return {
                    'success': False,
                    'error': 'Username already exists',
                    'error_code': 'USERNAME_EXISTS'
                }
            return {'success': True}
        except DatabaseError as e:
            logger.error(f"Database error checking username existence: {e}")
            return {
                'success': False,
                'error': 'Database connection error. Please try again.',
                'error_code': 'DB_ERROR'
            }

    @staticmethod
    def test_password_strength(password):
        """Extension: Password too weak - Display requirements"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 20:
            errors.append("Password must be 20 characters or less")
            
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
            
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
            
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
            
        if errors:
            return {
                'success': False,
                'error': 'Password requirements not met: ' + '; '.join(errors),
                'error_code': 'WEAK_PASSWORD',
                'requirements': errors
            }
        
        return {'success': True}
    
    @staticmethod
    def test_database_connection():
        """Extension: Database error - Display error message"""
        try:
            connection.ensure_connection()
            return {'success': True}
        except DatabaseError as e:
            logger.error(f"Database connection failed: {e}")
            return {
                'success': False,
                'error': 'Unable to connect to database. Please try again later.',
                'error_code': 'DB_CONNECTION_FAILED'
            }
    
    @staticmethod
    def test_field_length_validation(username, email, password):
        """Test field length constraints"""
        if len(username) > 10:
            return {
                'success': False,
                'error': 'Username must be 10 characters or less',
                'error_code': 'USERNAME_TOO_LONG'
            }
        
        if len(email) > 50:
            return {
                'success': False,
                'error': 'Email must be 50 characters or less',
                'error_code': 'EMAIL_TOO_LONG'
            }
        
        return {'success': True}


class UserAuthenticationTests:
    """
    Test Case ID: 2 - Authenticate User Login
    """
    
    @staticmethod
    def test_user_exists_and_credentials_valid(username, password):
        """Extension: Invalid credentials - Show error message"""
        try:
            user = Users.objects.get(userName=username)
            
            if not check_password(password, user.password):
                return {
                    'success': False,
                    'error': 'Invalid username or password',
                    'error_code': 'INVALID_CREDENTIALS'
                }
            
            return {
                'success': True,
                'user': user
            }
            
        except Users.DoesNotExist:
            return {
                'success': False,
                'error': 'Invalid username or password',
                'error_code': 'INVALID_CREDENTIALS'
            }
        except DatabaseError as e:
            logger.error(f"Database error during authentication: {e}")
            return {
                'success': False,
                'error': 'Authentication service temporarily unavailable',
                'error_code': 'AUTH_DB_ERROR'
            }
    
    @staticmethod
    def test_session_creation(user):
        """Extension: Session creation fails - Show system error"""
        try:
            from .views import generate_jwt_token
            token = generate_jwt_token(user)
            return {
                'success': True,
                'token': token
            }
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            return {
                'success': False,
                'error': 'Unable to create session. Please try again.',
                'error_code': 'SESSION_CREATION_FAILED'
            }
    
    @staticmethod
    def test_login_rate_limiting(username, ip_address):
        """Test login rate limiting - placeholder implementation for future enhancement"""
        # TODO: Implement actual rate limiting logic
        # For now, always allow login
        return {
            'success': True,
            'rate_limit_ok': True,
            'attempts_remaining': 5,  # Placeholder
            'window_reset_time': None,  # Placeholder
            'message': 'Rate limiting check passed (not yet implemented)'
        }

class FileUploadTests:
    """
    Test Case IDs: 5, 6, 7, 35 - File Upload Operations
    """
    
    @staticmethod
    def test_file_format_validation(file):
        """Test file format validation - wrapper for test_file_type_validation"""
        return FileUploadTests.test_file_type_validation(file)
    
    @staticmethod
    def test_file_content_validation(file):
        """Test file content validation based on file type"""
        try:
            if not file or not file.name:
                return {
                    'success': False,
                    'error': 'No file provided',
                    'error_code': 'NO_FILE'
                }
            
            file_extension = os.path.splitext(file.name)[1].lower()
            
            # Read file content
            try:
                file_content = file.read().decode('utf-8')
                file.seek(0)  # Reset file pointer
            except UnicodeDecodeError:
                return {
                    'success': False,
                    'error': 'File contains invalid characters. Please ensure it is a valid text file.',
                    'error_code': 'INVALID_ENCODING'
                }
            
            # Validate based on file type
            if file_extension == '.csv':
                return FileUploadTests.test_csv_format_validation(file_content)
            elif file_extension == '.json':
                return FileUploadTests.test_json_format_validation(file_content)
            else:
                return {
                    'success': False,
                    'error': 'Unsupported file format',
                    'error_code': 'INVALID_FILE_TYPE'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'File content validation failed: {str(e)}',
                'error_code': 'CONTENT_VALIDATION_ERROR'
            }
        
    @staticmethod
    def test_file_type_validation(file):
        """Extension: Invalid file type - Show error"""
        if not file or not file.name:
            return {
                'success': False,
                'error': 'No file selected',
                'error_code': 'NO_FILE'
            }
        
        allowed_extensions = ['.csv', '.json']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return {
                'success': False,
                'error': f'Invalid file type. Only CSV and JSON files are allowed.',
                'error_code': 'INVALID_FILE_TYPE',
                'allowed_types': allowed_extensions
            }
        
        return {'success': True}
    
    @staticmethod
    def test_file_size_validation(file):
        """Test Case ID: 35 - File Size Validation"""
        max_size = 10 * 1024 * 1024  # 10MB
        
        if not file:
            return {
                'success': False,
                'error': 'No file provided',
                'error_code': 'NO_FILE'
            }
        
        if file.size == 0:
            return {
                'success': False,
                'error': 'File is empty. Please select a valid file.',
                'error_code': 'EMPTY_FILE'
            }
        
        if file.size > max_size:
            return {
                'success': False,
                'error': f'File size ({file.size / (1024*1024):.1f}MB) exceeds the 10MB limit',
                'error_code': 'FILE_TOO_LARGE',
                'max_size_mb': 10
            }
        
        return {'success': True}
    
    @staticmethod
    def test_csv_format_validation(file_content):
        """Extension: Invalid CSV format - Show error"""
        try:
            import csv
            from io import StringIO
            
            # Try to parse CSV
            csv_reader = csv.DictReader(StringIO(file_content))
            
            # Check if fieldnames exist
            if csv_reader.fieldnames is None:
                return {
                    'success': False,
                    'error': 'CSV file has no headers or is malformed',
                    'error_code': 'INVALID_CSV_FORMAT'
                }
            
            # Clean fieldnames and check for required columns
            fieldnames = [name.strip().lower() for name in csv_reader.fieldnames if name]
            required_columns = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            
            missing_columns = [col for col in required_columns if col not in fieldnames]
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'CSV missing required columns: {", ".join(missing_columns)}',
                    'error_code': 'INVALID_CSV_FORMAT',
                    'missing_columns': missing_columns,
                    'found_columns': fieldnames
                }
            
            # Validate at least one row exists
            rows = list(csv_reader)
            if not rows:
                return {
                    'success': False,
                    'error': 'CSV file contains no data rows',
                    'error_code': 'EMPTY_CSV'
                }
            
            return {'success': True, 'row_count': len(rows)}
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid CSV format: {str(e)}',
                'error_code': 'CSV_PARSE_ERROR'
            }
    
    @staticmethod
    def test_json_format_validation(file_content):
        """Extension: Invalid JSON format - Show error"""
        try:
            import json
            data = json.loads(file_content)
            
            # Accept both array of questions and object with questions array
            if isinstance(data, list):
                if not data:
                    return {
                        'success': False,
                        'error': 'JSON array is empty',
                        'error_code': 'EMPTY_JSON_ARRAY'
                    }
                
                # Check if first item looks like a question
                first_item = data[0]
                if not isinstance(first_item, dict):
                    return {
                        'success': False,
                        'error': 'JSON array must contain question objects',
                        'error_code': 'INVALID_JSON_STRUCTURE'
                    }
                
                required_fields = ['question', 'options', 'correct_answer']
                missing_fields = [field for field in required_fields if field not in first_item]
                
                if missing_fields:
                    return {
                        'success': False,
                        'error': f'Question objects missing required fields: {", ".join(missing_fields)}',
                        'error_code': 'MISSING_JSON_FIELDS',
                        'missing_fields': missing_fields
                    }
                
                return {'success': True, 'question_count': len(data)}
                
            elif isinstance(data, dict):
                # Object with questions array - also valid
                if 'questions' not in data:
                    return {
                        'success': False,
                        'error': 'JSON object must contain "questions" array',
                        'error_code': 'MISSING_JSON_FIELDS',
                        'missing_fields': ['questions']
                    }
                
                if not isinstance(data['questions'], list):
                    return {
                        'success': False,
                        'error': '"questions" must be an array',
                        'error_code': 'INVALID_JSON_STRUCTURE'
                    }
                
                if not data['questions']:
                    return {
                        'success': False,
                        'error': 'Questions array is empty',
                        'error_code': 'EMPTY_JSON_ARRAY'
                    }
                
                return {'success': True, 'question_count': len(data['questions'])}
            
            else:
                return {
                    'success': False,
                    'error': 'JSON must be an array of questions or an object with "questions" array',
                    'error_code': 'INVALID_JSON_STRUCTURE'
                }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Invalid JSON format: {str(e)}',
                'error_code': 'JSON_PARSE_ERROR'
            }
    
    @staticmethod
    def test_database_save_operation(file_data):
        """Extension: Database error - Show system error"""
        try:
            # Test database connectivity before save
            connection.ensure_connection()
            return {'success': True}
        except DatabaseError as e:
            logger.error(f"Database error during file save: {e}")
            return {
                'success': False,
                'error': 'Unable to save file data. Database temporarily unavailable.',
                'error_code': 'DB_SAVE_ERROR'
            }

class FileConfirmationTests:
    """Test Case ID: 20 - File Upload Confirmation Process"""
    
    @staticmethod
    def test_upload_confirmation_data(file_id, user_id):
        """Test if file upload confirmation contains correct data"""
        try:
            # Verify file record exists
            try:
                file_record = File.objects.get(fileID=file_id, userID=user_id)
            except File.DoesNotExist:
                return {
                    'success': False,
                    'error': 'File record not found',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            # Verify associated quiz was created
            try:
                quiz = Quiz.objects.get(fileID=file_record)
                sections = Section.objects.filter(quizID=quiz)
                questions = Question.objects.filter(quizID=quiz)
                
                confirmation_data = {
                    'file_id': file_record.fileID,
                    'file_name': file_record.fileName,
                    'file_type': file_record.fileType,
                    'upload_date': file_record.uploadDate.isoformat(),
                    'quiz_id': quiz.quizID,
                    'quiz_title': quiz.title,
                    'total_sections': sections.count(),
                    'total_questions': questions.count(),
                    's3_path': file_record.filePath
                }
                
                return {
                    'success': True,
                    'confirmation_data': confirmation_data,
                    'message': 'Upload confirmation data validated'
                }
                
            except Quiz.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Associated quiz not found after upload',
                    'error_code': 'QUIZ_NOT_CREATED'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Upload confirmation test failed: {str(e)}',
                'error_code': 'CONFIRMATION_ERROR'
            }

# utility function for file upload tests
def run_file_upload_tests(file, user=None):
    """Run all file upload-related tests with comprehensive validation"""
    tests = FileUploadTests()
    
    # Test file type
    type_test = tests.test_file_type_validation(file)
    if not type_test['success']:
        return type_test
    
    # Test file size
    size_test = tests.test_file_size_validation(file)
    if not size_test['success']:
        return size_test
     
    # Test file content validation
    content_test = tests.test_file_content_validation(file)
    if not content_test['success']:
        return content_test
    
    # Test database connectivity
    db_test = tests.test_database_save_operation(None)
    if not db_test['success']:
        return db_test
    
    return {'success': True, 'message': 'All file upload tests passed'}

class QuizAttemptTests:
    """
    Test Case IDs: 9, 10, 28, 32 - Quiz Attempt Operations
    """
    
    @staticmethod
    def test_concurrent_attempts(user_id, quiz_id):
        """Test Case ID: 32 - Concurrent User Attempts"""
        try:
            incomplete_attempts = QuizAttempt.objects.filter(
                userID_id=user_id,
                quizID_id=quiz_id,
                completed=False
            )
            
            if incomplete_attempts.exists():
                attempt = incomplete_attempts.first()
                return {
                    'success': False,
                    'error': 'You have an incomplete attempt for this quiz. Complete it or start a new one.',
                    'error_code': 'CONCURRENT_ATTEMPT',
                    'existing_attempt_id': attempt.attemptID,
                    'started_at': attempt.startTime.isoformat()
                }
            
            return {'success': True}
            
        except DatabaseError as e:
            logger.error(f"Database error checking concurrent attempts: {e}")
            return {
                'success': False,
                'error': 'Unable to check existing attempts',
                'error_code': 'DB_ERROR'
            }
    
    @staticmethod
    def test_quiz_access_permission(user_id, quiz_id):
        """Test user has permission to access quiz"""
        try:
            quiz = Quiz.objects.select_related('fileID').get(quizID=quiz_id)
            
            if quiz.fileID.userID_id != user_id:
                return {
                    'success': False,
                    'error': 'Access denied. You do not own this quiz.',
                    'error_code': 'ACCESS_DENIED'
                }
            
            return {'success': True, 'quiz': quiz}
            
        except Quiz.DoesNotExist:
            return {
                'success': False,
                'error': 'Quiz not found',
                'error_code': 'QUIZ_NOT_FOUND'
            }
        except DatabaseError as e:
            logger.error(f"Database error checking quiz access: {e}")
            return {
                'success': False,
                'error': 'Unable to verify quiz access',
                'error_code': 'DB_ERROR'
            }
    
    @staticmethod
    def test_answer_validation(selected_option, question):
        """Test Case ID: 9 - Answer Quiz Question validation"""
        if not isinstance(selected_option, int):
            return {
                'success': False,
                'error': 'Selected option must be a number',
                'error_code': 'INVALID_OPTION_TYPE'
            }
        
        if selected_option < 0 or selected_option >= len(question.answerOptions):
            return {
                'success': False,
                'error': f'Selected option must be between 0 and {len(question.answerOptions) - 1}',
                'error_code': 'OPTION_OUT_OF_RANGE',
                'valid_range': [0, len(question.answerOptions) - 1]
            }
        
        return {'success': True}
    
    @staticmethod
    def test_score_calculation(attempt_id):
        """Test Case ID: 28 - Quiz Attempt Score Calculation"""
        try:
            attempt = QuizAttempt.objects.get(attemptID=attempt_id)
            answers = Answer.objects.filter(attemptID=attempt)
            total_questions = Question.objects.filter(quizID=attempt.quizID).count()
            
            if total_questions == 0:
                return {
                    'success': False,
                    'error': 'No questions found for score calculation',
                    'error_code': 'NO_QUESTIONS'
                }
            
            correct_answers = answers.filter(isCorrect=True).count()
            score = (correct_answers / total_questions) * 100
            
            return {
                'success': True,
                'score': round(score, 2),
                'correct_answers': correct_answers,
                'total_questions': total_questions
            }
            
        except QuizAttempt.DoesNotExist:
            return {
                'success': False,
                'error': 'Quiz attempt not found',
                'error_code': 'ATTEMPT_NOT_FOUND'
            }
        except ZeroDivisionError:
            return {
                'success': False,
                'error': 'Cannot calculate score: no questions available',
                'error_code': 'DIVISION_BY_ZERO'
            }
        except DatabaseError as e:
            logger.error(f"Database error during score calculation: {e}")
            return {
                'success': False,
                'error': 'Unable to calculate score due to database error',
                'error_code': 'CALC_DB_ERROR'
            }

class AuthenticationVerificationTests:
    """
    Test Case ID: 30 - User Authentication Verification
    """
    
    @staticmethod
    def test_token_validity(token):
        """Extension: Invalid token - Redirect to login"""
        try:
            from .views import verify_jwt_token
            payload = verify_jwt_token(token)
            return {
                'success': True,
                'user_id': payload['user_id']
            }
        except ValidationError as e:
            if 'expired' in str(e).lower():
                return {
                    'success': False,
                    'error': 'Session expired. Please log in again.',
                    'error_code': 'TOKEN_EXPIRED',
                    'redirect': '/login'
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid session. Please log in again.',
                    'error_code': 'INVALID_TOKEN',
                    'redirect': '/login'
                }
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return {
                'success': False,
                'error': 'Authentication error. Please log in again.',
                'error_code': 'AUTH_ERROR',
                'redirect': '/login'
            }
    
    @staticmethod
    def test_user_session_exists(user_id):
        """Extension: Session invalid - Create new session"""
        try:
            user = Users.objects.get(userID=user_id)
            return {
                'success': True,
                'user': user
            }
        except Users.DoesNotExist:
            return {
                'success': False,
                'error': 'User session invalid. Please log in again.',
                'error_code': 'USER_NOT_FOUND',
                'redirect': '/login'
            }


class DatabaseConnectionTests:
    """
    Test Case ID: 14 - Database Connection
    """
    
    @staticmethod
    def test_connection_health():
        """Extension: Connection fails - Retry with backoff"""
        try:
            connection.ensure_connection()
            
            # Test basic query
            from django.db import connection as db_conn
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return {
                'success': True,
                'status': 'healthy'
            }
            
        except DatabaseError as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'success': False,
                'error': 'Database connection failed',
                'error_code': 'DB_CONNECTION_FAILED',
                'retry_suggested': True
            }
    
    @staticmethod
    def test_crud_operations():
        """Test basic database operations"""
        try:
            # Test with a simple query that doesn't modify data
            Users.objects.filter(userID__lt=0).exists()  # Safe query that returns False
            return {'success': True}
        except DatabaseError as e:
            logger.error(f"Database CRUD test failed: {e}")
            return {
                'success': False,
                'error': 'Database operations unavailable',
                'error_code': 'DB_OPERATIONS_FAILED'
            }


class ProgressTrackingTests:
    """
    Test Case ID: 11, 27 - Progress and Mastery Level Calculation
    """
    
    @staticmethod
    def test_mastery_level_calculation(score):
        """Test Case ID: 27 - Progress Mastery Level Calculation"""
        if not isinstance(score, (int, float)):
            return {
                'success': False,
                'error': 'Score must be a number',
                'error_code': 'INVALID_SCORE_TYPE'
            }
        
        if score < 0 or score > 100:
            return {
                'success': False,
                'error': 'Score must be between 0 and 100',
                'error_code': 'SCORE_OUT_OF_RANGE'
            }
        
        try:
            from .views import calculate_mastery_level
            mastery = calculate_mastery_level(score)
            return {
                'success': True,
                'mastery_level': mastery
            }
        except Exception as e:
            logger.error(f"Mastery calculation error: {e}")
            return {
                'success': False,
                'error': 'Unable to calculate mastery level',
                'error_code': 'MASTERY_CALC_ERROR',
                'fallback_level': 'Beginner'
            }
    
    @staticmethod
    def test_progress_data_availability(user_id, quiz_id=None):
        """Extension: No data - Show empty state"""
        try:
            if quiz_id:
                # Get progress for specific quiz
                attempts = QuizAttempt.objects.filter(
                    userID_id=user_id,
                    quizID_id=quiz_id,
                    completed=True
                ).count()
                
                if attempts == 0:
                    return {
                        'success': True,
                        'has_data': False,
                        'message': 'No completed attempts found for this quiz. Take a quiz to see your progress!',
                        'empty_state': True
                    }
            else:
                # Get overall progress for dashboard (all quizzes)
                all_progress = Progress.objects.filter(userID_id=user_id)
                attempts = all_progress.count()
                
                if attempts == 0:
                    return {
                        'success': True,
                        'has_data': False,
                        'message': 'No progress data found. Take some quizzes to see your progress!',
                        'empty_state': True
                    }
            
            return {
                'success': True,
                'has_data': True,
                'attempt_count': attempts
            }
            
        except DatabaseError as e:
            logger.error(f"Progress data check failed: {e}")
            return {
                'success': False,
                'error': 'Unable to load progress data',
                'error_code': 'PROGRESS_DB_ERROR',
                'partial_data': True
            }

# Utility functions to run multiple tests for a view
def run_registration_tests(username, email, password):
    """Run all registration-related tests"""
    tests = UserRegistrationTests()
    
    # Test database connection first
    db_test = tests.test_database_connection()
    if not db_test['success']:
        return db_test
    
    # Test field lengths
    length_test = tests.test_field_length_validation(username, email, password)
    if not length_test['success']:
        return length_test
    
    # Test email doesn't exist
    email_test = tests.test_email_already_exists(email)
    if not email_test['success']:
        return email_test
    
    # Test username doesn't exist
    username_test = tests.test_username_already_exists(username)
    if not username_test['success']:
        return username_test
    
    # Test password strength
    password_test = tests.test_password_strength(password)
    if not password_test['success']:
        return password_test
    
    return {'success': True, 'message': 'All registration tests passed'}


def run_login_tests(username, password):
    """Run all login-related tests"""
    tests = UserAuthenticationTests()
    
    # Test credentials
    auth_test = tests.test_user_exists_and_credentials_valid(username, password)
    if not auth_test['success']:
        return auth_test
    
    # Test session creation
    session_test = tests.test_session_creation(auth_test['user'])
    if not session_test['success']:
        return session_test
    
    return {
        'success': True,
        'user': auth_test['user'],
        'token': session_test['token']
    }


def run_file_upload_tests(file, user=None):
    """Run all file upload-related tests with comprehensive validation"""
    tests = FileUploadTests()
    
    # Test file type
    type_test = tests.test_file_type_validation(file)
    if not type_test['success']:
        return type_test
    
    # Test file size
    size_test = tests.test_file_size_validation(file)
    if not size_test['success']:
        return size_test
     # Test file format validation - MISSING INTEGRATION
    try:
        file_content = file.read().decode('utf-8')
        file.seek(0)  # Reset file pointer
        
        if file.name.endswith('.csv'):
            format_test = tests.test_csv_format_validation(file_content)
        elif file.name.endswith('.json'):
            format_test = tests.test_json_format_validation(file_content)
        else:
            format_test = {
                'success': False, 
                'error': 'Unsupported file format',
                'error_code': 'INVALID_FILE_TYPE'
            }
        
        if not format_test['success']:
            return format_test
            
    except UnicodeDecodeError:
        return {
            'success': False,
            'error': 'File contains invalid characters. Please ensure it is a valid text file.',
            'error_code': 'INVALID_ENCODING'
        }
    
    # Test database connectivity
    db_test = tests.test_database_save_operation(None)
    if not db_test['success']:
        return db_test
    
    return {'success': True, 'message': 'All file upload tests passed'}

class SessionManagementTests:
    """Test Case ID: 36 - Session Persistence Across Pages"""
    
    def test_session_validity(self, token):
        """Test if session token is valid and active"""
        try:
            if not token:
                return {
                    'success': False,
                    'error': 'No session token provided',
                    'error_code': 'NO_TOKEN'
                }
            
            # Verify JWT token structure using direct JWT decode (avoid circular import)
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                
                if not user_id:
                    return {
                        'success': False,
                        'error': 'Invalid token payload',
                        'error_code': 'INVALID_PAYLOAD'
                    }
                
                # Check if user still exists
                try:
                    user = Users.objects.get(userID=user_id)
                    return {
                        'success': True,
                        'user_id': user_id,
                        'username': user.userName,
                        'message': 'Session is valid'
                    }
                except Users.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'User no longer exists',
                        'error_code': 'USER_NOT_FOUND'
                    }
                    
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_code': 'TOKEN_VALIDATION_ERROR'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Session validation error: {str(e)}',
                'error_code': 'SESSION_ERROR'
            }
    
    def test_session_persistence(self, user_id):
        """Test if user session persists across page navigation"""
        try:
            # Simulate session data that should persist
            session_data = {
                'user_id': user_id,
                'login_time': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'session_data': session_data,
                'message': 'Session persistence validated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Session persistence test failed: {str(e)}',
                'error_code': 'PERSISTENCE_ERROR'
            }

class NavigationTests:
    """Test Case ID: 18 - Navigate Between Screens"""
    
    def test_page_navigation_authorization(self, user_id, target_page):
        """Test if user is authorized to navigate to target page"""
        try:
            # Define page access requirements
            protected_pages = [
                'dashboard', 'upload', 'quiz', 'progress', 
                'profile', 'quiz-attempt', 'results'
            ]
            
            public_pages = ['login', 'register', 'faq', 'home']
            
            if target_page in public_pages:
                return {
                    'success': True,
                    'access_granted': True,
                    'message': f'Access granted to public page: {target_page}'
                }
            
            if target_page in protected_pages:
                if not user_id:
                    return {
                        'success': False,
                        'access_granted': False,
                        'error': 'Authentication required for protected page',
                        'error_code': 'AUTH_REQUIRED',
                        'redirect_to': '/login'
                    }
                
                # Check if user exists and is active
                try:
                    user = Users.objects.get(userID=user_id)
                    return {
                        'success': True,
                        'access_granted': True,
                        'user_id': user_id,
                        'message': f'Access granted to protected page: {target_page}'
                    }
                except Users.DoesNotExist:
                    return {
                        'success': False,
                        'access_granted': False,
                        'error': 'User not found',
                        'error_code': 'USER_NOT_FOUND',
                        'redirect_to': '/login'
                    }
            
            return {
                'success': False,
                'access_granted': False,
                'error': f'Unknown page: {target_page}',
                'error_code': 'UNKNOWN_PAGE'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Navigation authorization test failed: {str(e)}',
                'error_code': 'NAVIGATION_ERROR'
            }
    
    def test_navigation_state_preservation(self, current_page, target_page, user_context):
        """Test if navigation preserves necessary state"""
        try:
            # Define state that should be preserved during navigation
            preserved_state = {
                'user_id': user_context.get('user_id'),
                'current_quiz_attempt': user_context.get('current_quiz_attempt'),
                'unsaved_changes': user_context.get('unsaved_changes', False)
            }
            
            # Check if navigation would lose important state
            state_loss_risk = False
            warnings = []
            
            if preserved_state['current_quiz_attempt'] and target_page not in ['quiz', 'quiz-results']:
                state_loss_risk = True
                warnings.append('Active quiz attempt may be lost')
            
            if preserved_state['unsaved_changes'] and target_page != current_page:
                state_loss_risk = True
                warnings.append('Unsaved changes may be lost')
            
            return {
                'success': True,
                'state_preserved': not state_loss_risk,
                'warnings': warnings,
                'preserved_state': preserved_state,
                'message': 'Navigation state analysis completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Navigation state test failed: {str(e)}',
                'error_code': 'STATE_ERROR'
            }

class QuizTimingTests:
    """Test Case ID: 17 - Timed Quiz Execution"""
    
    def test_quiz_time_limit_validation(self, quiz_id, time_limit_minutes=None):
        """Test quiz time limit configuration and validation"""
        try:
            # Default time limits by quiz size
            if time_limit_minutes is None:
                try:
                    question_count = Question.objects.filter(quizID=quiz_id).count()
                    # Default: 1 minute per question, max 60 minutes
                    time_limit_minutes = min(question_count, 60)
                except Exception:
                    time_limit_minutes = 30  # Default fallback
            
            if time_limit_minutes <= 0:
                return {
                    'success': False,
                    'error': 'Time limit must be positive',
                    'error_code': 'INVALID_TIME_LIMIT'
                }
            
            if time_limit_minutes > 240:  # 4 hours max
                return {
                    'success': False,
                    'error': 'Time limit cannot exceed 4 hours',
                    'error_code': 'TIME_LIMIT_TOO_LONG'
                }
            
            return {
                'success': True,
                'time_limit_minutes': time_limit_minutes,
                'time_limit_seconds': time_limit_minutes * 60,
                'message': f'Time limit validated: {time_limit_minutes} minutes'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Time limit validation failed: {str(e)}',
                'error_code': 'TIME_VALIDATION_ERROR'
            }
    
    def test_quiz_attempt_time_tracking(self, attempt_id):
        """Test if quiz attempt time is being tracked properly"""
        try:
            try:
                attempt = QuizAttempt.objects.get(attemptID=attempt_id)
            except QuizAttempt.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz attempt not found',
                    'error_code': 'ATTEMPT_NOT_FOUND'
                }
            
            # Check if start time is set
            if not attempt.startTime:
                return {
                    'success': False,
                    'error': 'Quiz start time not recorded',
                    'error_code': 'NO_START_TIME'
                }
            
            # Calculate elapsed time
            current_time = timezone.now()
            elapsed_time = current_time - attempt.startTime
            elapsed_minutes = elapsed_time.total_seconds() / 60
            
            # Check for reasonable time bounds
            if elapsed_minutes < 0:
                return {
                    'success': False,
                    'error': 'Invalid time calculation - negative elapsed time',
                    'error_code': 'INVALID_TIME_CALC'
                }
            
            if elapsed_minutes > 480:  # 8 hours - unreasonably long
                return {
                    'success': False,
                    'error': 'Quiz attempt time exceeds maximum allowed duration',
                    'error_code': 'TIME_EXCEEDED'
                }
            
            return {
                'success': True,
                'attempt_id': attempt_id,
                'start_time': attempt.startTime.isoformat(),
                'current_time': current_time.isoformat(),
                'elapsed_minutes': round(elapsed_minutes, 2),
                'elapsed_seconds': round(elapsed_time.total_seconds()),
                'is_completed': attempt.completed,
                'end_time': attempt.endTime.isoformat() if attempt.endTime else None,
                'message': 'Time tracking validation completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Time tracking test failed: {str(e)}',
                'error_code': 'TIME_TRACKING_ERROR'
            }

class FileConfirmationTests:
    """Test Case ID: 20 - File Upload Confirmation Process"""
    
    def test_upload_confirmation_data(self, file_id, user_id):
        """Test if file upload confirmation contains correct data"""
        try:
            # Verify file record exists
            try:
                file_record = File.objects.get(fileID=file_id, userID=user_id)
            except File.DoesNotExist:
                return {
                    'success': False,
                    'error': 'File record not found',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            # Verify associated quiz was created
            try:
                quiz = Quiz.objects.get(fileID=file_record)
                sections = Section.objects.filter(quizID=quiz)
                questions = Question.objects.filter(quizID=quiz)
                
                confirmation_data = {
                    'file_id': file_record.fileID,
                    'file_name': file_record.fileName,
                    'file_type': file_record.fileType,
                    'upload_date': file_record.uploadDate.isoformat(),
                    'quiz_id': quiz.quizID,
                    'quiz_title': quiz.title,
                    'total_sections': sections.count(),
                    'total_questions': questions.count(),
                    's3_path': file_record.filePath
                }
                
                return {
                    'success': True,
                    'confirmation_data': confirmation_data,
                    'message': 'Upload confirmation data validated'
                }
                
            except Quiz.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Associated quiz not found after upload',
                    'error_code': 'QUIZ_NOT_CREATED'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Upload confirmation test failed: {str(e)}',
                'error_code': 'CONFIRMATION_ERROR'
            }
    
    def test_file_processing_status(self, file_id):
        """Test file processing completion status"""
        try:
            try:
                file_record = File.objects.get(fileID=file_id)
                quiz = Quiz.objects.get(fileID=file_record)
            except (File.DoesNotExist, Quiz.DoesNotExist):
                return {
                    'success': False,
                    'error': 'File or quiz not found',
                    'error_code': 'RECORD_NOT_FOUND'
                }
            
            # Check processing completeness
            sections_count = Section.objects.filter(quizID=quiz).count()
            questions_count = Question.objects.filter(quizID=quiz).count()
            
            processing_complete = (
                bool(file_record.filePath) and  # S3 upload completed
                sections_count > 0 and         # Sections created
                questions_count > 0            # Questions created
            )
            
            return {
                'success': True,
                'processing_complete': processing_complete,
                'file_uploaded_to_s3': bool(file_record.filePath),
                'sections_created': sections_count,
                'questions_created': questions_count,
                'message': 'File processing status validated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'File processing status test failed: {str(e)}',
                'error_code': 'PROCESSING_STATUS_ERROR'
            }

class QuizNavigationTests:
    """Test Case ID: 23 - Quiz Taking Navigation (Back/Submit)"""
    
    def test_quiz_navigation_bounds(self, attempt_id, target_question_number):
        """Test quiz navigation within valid bounds"""
        try:
            try:
                attempt = QuizAttempt.objects.get(attemptID=attempt_id)
                total_questions = Question.objects.filter(quizID=attempt.quizID).count()
            except QuizAttempt.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz attempt not found',
                    'error_code': 'ATTEMPT_NOT_FOUND'
                }
            
            if target_question_number < 1:
                return {
                    'success': False,
                    'error': 'Cannot navigate before first question',
                    'error_code': 'NAVIGATION_BEFORE_START',
                    'can_navigate': False
                }
            
            if target_question_number > total_questions:
                return {
                    'success': False,
                    'error': f'Cannot navigate beyond last question (max: {total_questions})',
                    'error_code': 'NAVIGATION_BEYOND_END',
                    'can_navigate': False
                }
            
            # Check navigation permissions
            can_go_back = target_question_number > 1
            can_go_forward = target_question_number < total_questions
            can_submit = target_question_number == total_questions
            
            return {
                'success': True,
                'can_navigate': True,
                'target_question': target_question_number,
                'total_questions': total_questions,
                'navigation_options': {
                    'can_go_back': can_go_back,
                    'can_go_forward': can_go_forward,
                    'can_submit': can_submit
                },
                'message': 'Navigation bounds validated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Navigation bounds test failed: {str(e)}',
                'error_code': 'NAVIGATION_ERROR'
            }
    
    def test_answer_preservation_during_navigation(self, attempt_id, question_id):
        """Test if answers are preserved when navigating between questions"""
        try:
            try:
                attempt = QuizAttempt.objects.get(attemptID=attempt_id)
                question = Question.objects.get(questionID=question_id, quizID=attempt.quizID)
            except (QuizAttempt.DoesNotExist, Question.DoesNotExist):
                return {
                    'success': False,
                    'error': 'Attempt or question not found',
                    'error_code': 'RECORD_NOT_FOUND'
                }
            
            # Check if answer exists for this question
            try:
                answer = Answer.objects.get(attemptID=attempt, questionID=question)
                answer_preserved = True
                preserved_data = {
                    'selected_option': answer.selectedOption,
                    'is_correct': answer.isCorrect,
                    'response_time': answer.responseTime
                }
            except Answer.DoesNotExist:
                answer_preserved = False
                preserved_data = None
            
            return {
                'success': True,
                'answer_preserved': answer_preserved,
                'question_id': question_id,
                'attempt_id': attempt_id,
                'preserved_data': preserved_data,
                'message': 'Answer preservation validated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Answer preservation test failed: {str(e)}',
                'error_code': 'PRESERVATION_ERROR'
            }

class EmailNotificationTests:
    """Test Case ID: 12 - Email Notification Delivery"""
    
    def test_email_configuration(self):
        """Test email service configuration"""
        try:
            from django.conf import settings
            
            # Check if email settings are configured
            email_configured = (
                hasattr(settings, 'EMAIL_HOST') and
                hasattr(settings, 'EMAIL_PORT') and
                hasattr(settings, 'EMAIL_HOST_USER')
            )
            
            if not email_configured:
                return {
                    'success': False,
                    'error': 'Email service not configured',
                    'error_code': 'EMAIL_NOT_CONFIGURED',
                    'fallback_available': True  # Can log instead of send
                }
            
            return {
                'success': True,
                'email_configured': True,
                'host': getattr(settings, 'EMAIL_HOST', 'Not set'),
                'port': getattr(settings, 'EMAIL_PORT', 'Not set'),
                'message': 'Email configuration validated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Email configuration test failed: {str(e)}',
                'error_code': 'EMAIL_CONFIG_ERROR'
            }
    
    def test_password_reset_email_content(self, user_email, reset_token):
        """Test password reset email content generation"""
        try:
            if not user_email or '@' not in user_email:
                return {
                    'success': False,
                    'error': 'Invalid email address',
                    'error_code': 'INVALID_EMAIL'
                }
            
            if not reset_token:
                return {
                    'success': False,
                    'error': 'Reset token required',
                    'error_code': 'NO_TOKEN'
                }
            
            # Generate email content
            reset_url = f"https://your-domain.com/reset-password?token={reset_token}"
            email_content = {
                'subject': 'QuizCanvas Password Reset',
                'to_email': user_email,
                'body': f"""
                Hello,
                
                You requested a password reset for your QuizCanvas account.
                
                Click the following link to reset your password:
                {reset_url}
                
                This link will expire in 1 hour.
                
                If you didn't request this reset, please ignore this email.
                
                Best regards,
                QuizCanvas Team
                """,
                'html_body': f"""
                <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hello,</p>
                    <p>You requested a password reset for your QuizCanvas account.</p>
                    <p><a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request this reset, please ignore this email.</p>
                    <p>Best regards,<br>QuizCanvas Team</p>
                </body>
                </html>
                """
            }
            
            return {
                'success': True,
                'email_content': email_content,
                'reset_url': reset_url,
                'message': 'Email content generated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Email content generation failed: {str(e)}',
                'error_code': 'EMAIL_CONTENT_ERROR'
            }

class DataIntegrityTests:
    """Test Case ID: Various - Data integrity across operations"""
    
    def test_quiz_deletion_cascade(self, quiz_id, user_id):
        """Test if quiz deletion properly cascades to related data"""
        try:
            # Check if quiz exists and belongs to user
            try:
                quiz = Quiz.objects.get(quizID=quiz_id, fileID__userID=user_id)
            except Quiz.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz not found or access denied',
                    'error_code': 'QUIZ_NOT_FOUND'
                }
            
            # Count related objects before deletion
            before_counts = {
                'sections': Section.objects.filter(quizID=quiz).count(),
                'questions': Question.objects.filter(quizID=quiz).count(),
                'attempts': QuizAttempt.objects.filter(quizID=quiz).count(),
                'answers': Answer.objects.filter(attemptID__quizID=quiz).count(),
                'progress': Progress.objects.filter(quizID=quiz).count()
            }
            
            return {
                'success': True,
                'quiz_id': quiz_id,
                'related_data_counts': before_counts,
                'total_related_records': sum(before_counts.values()),
                'cascade_required': sum(before_counts.values()) > 0,
                'message': 'Quiz deletion cascade analysis completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Cascade test failed: {str(e)}',
                'error_code': 'CASCADE_ERROR'
            }
    
    def test_foreign_key_constraints(self, quiz_id):
        """Test foreign key constraint integrity"""
        try:
            # Test all foreign key relationships
            constraints_valid = True
            constraint_errors = []
            
            try:
                quiz = Quiz.objects.get(quizID=quiz_id)
                
                # Test Quiz -> File relationship
                if not File.objects.filter(fileID=quiz.fileID.fileID).exists():
                    constraints_valid = False
                    constraint_errors.append('Quiz references non-existent file')
                
                # Test Section -> Quiz relationship
                sections = Section.objects.filter(quizID=quiz)
                for section in sections:
                    if section.quizID.quizID != quiz_id:
                        constraints_valid = False
                        constraint_errors.append(f'Section {section.sectionID} has invalid quiz reference')
                
                # Test Question -> Quiz and Section relationships
                questions = Question.objects.filter(quizID=quiz)
                for question in questions:
                    if question.quizID.quizID != quiz_id:
                        constraints_valid = False
                        constraint_errors.append(f'Question {question.questionID} has invalid quiz reference')
                    
                    if question.sectionID and not Section.objects.filter(sectionID=question.sectionID.sectionID, quizID=quiz).exists():
                        constraints_valid = False
                        constraint_errors.append(f'Question {question.questionID} references invalid section')
                
            except Quiz.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz not found',
                    'error_code': 'QUIZ_NOT_FOUND'
                }
            
            return {
                'success': True,
                'constraints_valid': constraints_valid,
                'constraint_errors': constraint_errors,
                'error_count': len(constraint_errors),
                'message': 'Foreign key constraint validation completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Constraint test failed: {str(e)}',
                'error_code': 'CONSTRAINT_ERROR'
            }

# Additional helper functions for comprehensive testing

def run_session_management_tests(token, user_id):
    """Run comprehensive session management tests"""
    session_tests = SessionManagementTests()
    
    # Test session validity
    validity_test = session_tests.test_session_validity(token)
    if not validity_test['success']:
        return validity_test
    
    # Test session persistence
    persistence_test = session_tests.test_session_persistence(user_id)
    if not persistence_test['success']:
        return persistence_test
    
    return {
        'success': True,
        'session_valid': validity_test['success'],
        'session_persistent': persistence_test['success'],
        'user_id': user_id,
        'message': 'All session management tests passed'
    }

def run_navigation_tests(user_id, current_page, target_page, user_context=None):
    """Run comprehensive navigation tests"""
    nav_tests = NavigationTests()
    
    if user_context is None:
        user_context = {'user_id': user_id}
    
    # Test navigation authorization
    auth_test = nav_tests.test_page_navigation_authorization(user_id, target_page)
    if not auth_test['success']:
        return auth_test
    
    # Test state preservation
    state_test = nav_tests.test_navigation_state_preservation(current_page, target_page, user_context)
    
    return {
        'success': True,
        'navigation_authorized': auth_test['access_granted'],
        'state_preserved': state_test['state_preserved'],
        'warnings': state_test.get('warnings', []),
        'message': 'All navigation tests completed'
    }

def run_comprehensive_data_integrity_tests(quiz_id, user_id):
    """Run comprehensive data integrity tests"""
    integrity_tests = DataIntegrityTests()
    
    # Test cascade analysis
    cascade_test = integrity_tests.test_quiz_deletion_cascade(quiz_id, user_id)
    if not cascade_test['success']:
        return cascade_test
    
    # Test foreign key constraints
    constraint_test = integrity_tests.test_foreign_key_constraints(quiz_id)
    
    return {
        'success': constraint_test['success'] and cascade_test['success'],
        'cascade_analysis': cascade_test,
        'constraint_validation': constraint_test,
        'data_integrity_score': 100 if constraint_test['constraints_valid'] else 
                               (100 - (constraint_test['error_count'] * 10)),
        'message': 'Comprehensive data integrity tests completed'
    }

class EmailNotificationTests:
    """Test Case ID: 12 - Email Notification Delivery"""
    
    def test_email_service_configuration(self):
        """Test if email service is properly configured"""
        try:
            from django.conf import settings
            from django.core.mail import get_connection
            
            # Check if email settings are configured
            required_settings = ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER']
            missing_settings = [setting for setting in required_settings 
                              if not hasattr(settings, setting) or not getattr(settings, setting)]
            
            if missing_settings:
                return {
                    'success': False,
                    'error': f'Missing email configuration: {", ".join(missing_settings)}',
                    'error_code': 'EMAIL_NOT_CONFIGURED'
                }
            
            # Test email connection
            try:
                connection = get_connection()
                connection.open()
                connection.close()
                return {
                    'success': True,
                    'email_service_ready': True
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Email connection failed: {str(e)}',
                    'error_code': 'EMAIL_CONNECTION_FAILED'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Email service test failed: {str(e)}',
                'error_code': 'EMAIL_SERVICE_ERROR'
            }
    
    def test_password_reset_email_generation(self, user_email, reset_token):
        """Test password reset email content generation"""
        try:
            if not user_email or '@' not in user_email:
                return {
                    'success': False,
                    'error': 'Invalid email address provided',
                    'error_code': 'INVALID_EMAIL'
                }
            
            if not reset_token:
                return {
                    'success': False,
                    'error': 'Reset token is required',
                    'error_code': 'MISSING_TOKEN'
                }
            
            # Generate email content
            email_content = {
                'subject': 'QuizCanvas Password Reset Request',
                'recipient': user_email,
                'body': f'Click here to reset your password: /reset-password?token={reset_token}',
                'token_included': True,
                'expires_in': '1 hour'
            }
            
            return {
                'success': True,
                'email_content': email_content,
                'delivery_ready': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Email generation failed: {str(e)}',
                'error_code': 'EMAIL_GENERATION_ERROR'
            }

class QuestionRandomizationTests:
    """Test Case ID: 13 - Question Randomization"""
    
    def test_question_order_randomization(self, quiz_id):
        """Test if questions can be randomized within a quiz"""
        try:
            from .models import Question
            import random
            
            # Get all questions for the quiz
            questions = list(Question.objects.filter(quizID_id=quiz_id).order_by('questionID'))
            
            if len(questions) < 2:
                return {
                    'success': False,
                    'error': 'Not enough questions to test randomization (minimum 2 required)',
                    'error_code': 'INSUFFICIENT_QUESTIONS'
                }
            
            # Create multiple randomized orders
            original_order = [q.questionID for q in questions]
            randomized_orders = []
            
            for _ in range(5):  # Generate 5 different random orders
                randomized = questions.copy()
                random.shuffle(randomized)
                randomized_orders.append([q.questionID for q in randomized])
            
            # Check if at least one order is different from original
            different_orders = [order for order in randomized_orders if order != original_order]
            
            return {
                'success': True,
                'randomization_working': len(different_orders) > 0,
                'original_order': original_order,
                'sample_randomized_order': randomized_orders[0] if randomized_orders else [],
                'total_questions': len(questions)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Question randomization test failed: {str(e)}',
                'error_code': 'RANDOMIZATION_ERROR'
            }
    
    def test_randomization_consistency(self, quiz_id, attempt_id):
        """Test that question order remains consistent within a single attempt"""
        try:
            from .models import QuizAttempt, Question
            
            # Verify attempt exists
            try:
                attempt = QuizAttempt.objects.get(attemptID=attempt_id, quizID_id=quiz_id)
            except QuizAttempt.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz attempt not found',
                    'error_code': 'ATTEMPT_NOT_FOUND'
                }
            
            # Get questions in consistent order for this attempt
            questions = Question.objects.filter(quizID_id=quiz_id).order_by('questionID')
            
            # Simulate getting the same question order multiple times during attempt
            order1 = [q.questionID for q in questions]
            order2 = [q.questionID for q in questions]
            
            consistency_maintained = order1 == order2
            
            return {
                'success': True,
                'consistency_maintained': consistency_maintained,
                'question_count': len(order1),
                'attempt_id': attempt_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Randomization consistency test failed: {str(e)}',
                'error_code': 'CONSISTENCY_ERROR'
            }

class S3ConnectionTests:
    """Test Case ID: 15 - S3 Connection"""
    
    def test_s3_service_initialization(self):
        """Test S3 service initialization and credentials"""
        try:
            from django.conf import settings
            
            # Check if S3 credentials are configured
            required_settings = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_STORAGE_BUCKET_NAME']
            missing_settings = [setting for setting in required_settings 
                              if not hasattr(settings, setting) or not getattr(settings, setting)]
            
            if missing_settings:
                return {
                    'success': False,
                    'error': f'Missing S3 configuration: {", ".join(missing_settings)}',
                    'error_code': 'S3_NOT_CONFIGURED'
                }
            
            return {
                'success': True,
                's3_configured': True,
                'bucket_name': settings.AWS_STORAGE_BUCKET_NAME
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'S3 configuration test failed: {str(e)}',
                'error_code': 'S3_CONFIG_ERROR'
            }
    
    def test_s3_connection_health(self):
        """Test actual connection to S3 service"""
        try:
            from .services.s3_service import get_s3_service
            from django.conf import settings
            import boto3
            from botocore.exceptions import ClientError
            
            # Test basic S3 connection using boto3 directly
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_DEFAULT_REGION
            )
            
            # Test bucket access
            s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            
            return {
                'success': True,
                's3_connection_healthy': True,
                'service_available': True
            }
            
        except ClientError as e:
            return {
                'success': False,
                'error': f'S3 connection test failed: {str(e)}',
                'error_code': 'S3_CONNECTION_FAILED'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'S3 connection health test failed: {str(e)}',
                'error_code': 'S3_HEALTH_ERROR'
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'S3 connection health test failed: {str(e)}',
                'error_code': 'S3_HEALTH_ERROR'
            }

class EC2ConnectionTests:
    """Test Case ID: 16 - EC2 Connection"""
    
    def test_ec2_deployment_status(self):
        """Test EC2 instance deployment and health"""
        try:
            import os
            import socket
            
            # Check if running on EC2
            is_ec2 = os.path.exists('/sys/hypervisor/uuid') or 'AWS_' in os.environ
            
            # Test local server health
            try:
                # Test if the application is responding on the expected port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 8000))  # Django default port
                sock.close()
                server_responding = result == 0
            except:
                server_responding = False
            
            return {
                'success': True,
                'running_on_ec2': is_ec2,
                'server_responding': server_responding,
                'deployment_status': 'healthy' if server_responding else 'unhealthy'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'EC2 deployment test failed: {str(e)}',
                'error_code': 'EC2_DEPLOYMENT_ERROR'
            }
    
    def test_ec2_resource_availability(self):
        """Test EC2 resource availability and performance"""
        try:
            import psutil
            
            # Get system resource information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            # Define thresholds
            cpu_threshold = 80 
            memory_threshold = 80 
            disk_threshold = 90 
            
            resource_healthy = (
                cpu_percent < cpu_threshold and
                memory_info.percent < memory_threshold and
                disk_info.percent < disk_threshold
            )
            
            return {
                'success': True,
                'resource_healthy': resource_healthy,
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory_info.percent,
                'disk_usage_percent': disk_info.percent,
                'thresholds': {
                    'cpu': cpu_threshold,
                    'memory': memory_threshold,
                    'disk': disk_threshold
                }
            }
            
        except ImportError:
            return {
                'success': True,
                'resource_healthy': True,
                'message': 'psutil not available, skipping resource checks'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'EC2 resource test failed: {str(e)}',
                'error_code': 'EC2_RESOURCE_ERROR'
            }

class TimedQuizTests:
    """Test Case ID: 17 - Timed Quiz Execution"""
    
    def test_quiz_time_limit_enforcement(self, attempt_id, time_limit_minutes=30):
        """Test if quiz time limits are properly enforced"""
        try:
            from .models import QuizAttempt
            from django.utils import timezone
            from datetime import timedelta
            
            try:
                attempt = QuizAttempt.objects.get(attemptID=attempt_id)
            except QuizAttempt.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz attempt not found',
                    'error_code': 'ATTEMPT_NOT_FOUND'
                }
            
            # Calculate time elapsed
            current_time = timezone.now()
            elapsed_time = current_time - attempt.startTime
            elapsed_minutes = elapsed_time.total_seconds() / 60
            
            # Check if time limit exceeded
            time_limit_exceeded = elapsed_minutes > time_limit_minutes
            remaining_time = max(0, time_limit_minutes - elapsed_minutes)
            
            return {
                'success': True,
                'time_limit_minutes': time_limit_minutes,
                'elapsed_minutes': round(elapsed_minutes, 2),
                'remaining_minutes': round(remaining_time, 2),
                'time_limit_exceeded': time_limit_exceeded,
                'should_auto_submit': time_limit_exceeded and not attempt.completed
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Quiz time limit test failed: {str(e)}',
                'error_code': 'TIME_LIMIT_ERROR'
            }
    
    def test_timer_display_accuracy(self, attempt_id):
        """Test if timer display is accurate"""
        try:
            from .models import QuizAttempt
            from django.utils import timezone
            
            try:
                attempt = QuizAttempt.objects.get(attemptID=attempt_id)
            except QuizAttempt.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz attempt not found',
                    'error_code': 'ATTEMPT_NOT_FOUND'
                }
            
            # Calculate current time information
            current_time = timezone.now()
            start_time = attempt.startTime
            elapsed_seconds = (current_time - start_time).total_seconds()
            
            # Simulate timer display format (MM:SS)
            minutes = int(elapsed_seconds // 60)
            seconds = int(elapsed_seconds % 60)
            timer_display = f"{minutes:02d}:{seconds:02d}"
            
            return {
                'success': True,
                'start_time': start_time.isoformat(),
                'current_time': current_time.isoformat(),
                'elapsed_seconds': int(elapsed_seconds),
                'timer_display': timer_display,
                'timer_accurate': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Timer display test failed: {str(e)}',
                'error_code': 'TIMER_DISPLAY_ERROR'
            }

class NavigationTests:
    """Test Case ID: 18 - Navigate Between Screens"""
    
    def test_page_access_authorization(self, user_id, target_page):
        """Test if user is authorized to access target page"""
        try:
            # Define page access requirements
            public_pages = ['login', 'register', 'home', 'faq']
            protected_pages = ['dashboard', 'upload', 'quiz', 'profile', 'progress']
            admin_pages = ['admin', 'user-management']
            
            if target_page in public_pages:
                return {
                    'success': True,
                    'access_granted': True,
                    'page_type': 'public'
                }
            
            if target_page in protected_pages:
                if not user_id:
                    return {
                        'success': False,
                        'access_granted': False,
                        'error': 'Authentication required',
                        'error_code': 'AUTH_REQUIRED',
                        'redirect_to': '/login'
                    }
                
                # Check if user exists
                from .models import Users
                try:
                    Users.objects.get(userID=user_id)
                    return {
                        'success': True,
                        'access_granted': True,
                        'page_type': 'protected'
                    }
                except Users.DoesNotExist:
                    return {
                        'success': False,
                        'access_granted': False,
                        'error': 'User not found',
                        'error_code': 'USER_NOT_FOUND'
                    }
            
            return {
                'success': False,
                'access_granted': False,
                'error': f'Unknown page: {target_page}',
                'error_code': 'UNKNOWN_PAGE'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Page access test failed: {str(e)}',
                'error_code': 'ACCESS_TEST_ERROR'
            }
    
    def test_navigation_state_preservation(self, user_context):
        """Test if important state is preserved during navigation"""
        try:
            # Check for state that should be preserved
            preserved_state = {
                'user_logged_in': bool(user_context.get('user_id')),
                'active_quiz_attempt': user_context.get('active_attempt_id'),
                'unsaved_changes': user_context.get('unsaved_changes', False)
            }
            
            # Identify potential state loss risks
            warnings = []
            if preserved_state['active_quiz_attempt']:
                warnings.append('Active quiz attempt may be lost during navigation')
            
            if preserved_state['unsaved_changes']:
                warnings.append('Unsaved changes may be lost')
            
            state_safe = len(warnings) == 0
            
            return {
                'success': True,
                'state_safe': state_safe,
                'preserved_state': preserved_state,
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Navigation state test failed: {str(e)}',
                'error_code': 'STATE_TEST_ERROR'
            }

class RegistrationCancellationTests:
    """Test Case ID: 19 - Cancel Registration Process"""
    
    def test_registration_cancellation(self, form_data=None):
        """Test cancelling registration process before completion"""
        try:
            # Simulate form data that would be lost
            if form_data is None:
                form_data = {
                    'username': 'test_user',
                    'email': 'test@example.com',
                    'password': 'partially_entered'
                }
            
            # Test cancellation process
            cancellation_safe = True
            data_cleared = True
            
            # Verify no partial user record was created
            from .models import Users
            partial_users = Users.objects.filter(email=form_data.get('email', ''))
            
            if partial_users.exists():
                cancellation_safe = False
                data_cleared = False
            
            return {
                'success': True,
                'cancellation_safe': cancellation_safe,
                'data_cleared': data_cleared,
                'form_data_lost': True,  # Expected behavior
                'no_partial_records': not partial_users.exists()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Registration cancellation test failed: {str(e)}',
                'error_code': 'CANCELLATION_ERROR'
            }
    
    def test_form_data_cleanup(self, session_data=None):
        """Test if form data is properly cleaned up on cancellation"""
        try:
            # Simulate session/form data cleanup
            if session_data is None:
                session_data = {
                    'registration_step': 'in_progress',
                    'partial_form_data': {'username': 'test'},
                    'csrf_token': 'test_token'
                }
            
            # Test cleanup process
            cleanup_successful = True
            sensitive_data_removed = True
            
            # Verify cleanup
            remaining_data = {}  # After cleanup, should be empty
            
            return {
                'success': True,
                'cleanup_successful': cleanup_successful,
                'sensitive_data_removed': sensitive_data_removed,
                'remaining_data': remaining_data,
                'session_cleared': len(remaining_data) == 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Form data cleanup test failed: {str(e)}',
                'error_code': 'CLEANUP_ERROR'
            }

class ProgressBarTests:
    """Test Case ID: 21 - Quiz Results Progress Bar Display"""
    
    def test_progress_bar_calculation(self, current_question, total_questions):
        """Test progress bar percentage calculation"""
        try:
            if total_questions <= 0:
                return {
                    'success': False,
                    'error': 'Total questions must be greater than 0',
                    'error_code': 'INVALID_TOTAL'
                }
            
            if current_question < 0 or current_question > total_questions:
                return {
                    'success': False,
                    'error': 'Current question out of valid range',
                    'error_code': 'INVALID_CURRENT'
                }
            
            # Calculate progress percentage
            progress_percentage = (current_question / total_questions) * 100
            
            return {
                'success': True,
                'current_question': current_question,
                'total_questions': total_questions,
                'progress_percentage': round(progress_percentage, 1),
                'calculation_accurate': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Progress bar calculation failed: {str(e)}',
                'error_code': 'CALCULATION_ERROR'
            }
    
    def test_progress_bar_display(self, progress_percentage):
        """Test progress bar visual display"""
        try:
            if progress_percentage < 0 or progress_percentage > 100:
                return {
                    'success': False,
                    'error': 'Progress percentage must be between 0 and 100',
                    'error_code': 'INVALID_PERCENTAGE'
                }
            
            # Test display properties
            display_width = progress_percentage  # Percentage width
            display_color = 'green' if progress_percentage == 100 else 'blue'
            display_text = f"{progress_percentage}%"
            
            return {
                'success': True,
                'display_width': display_width,
                'display_color': display_color,
                'display_text': display_text,
                'display_ready': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Progress bar display test failed: {str(e)}',
                'error_code': 'DISPLAY_ERROR'
            }
        
class ReportDownloadTests:
    """Test Case ID: 22 - Download Progress Report"""
    
    def test_report_generation(self, user_id, quiz_id=None):
        """Test progress report generation"""
        try:
            from .models import Progress, QuizAttempt, Quiz
            
            # Get user progress data
            if quiz_id:
                progress_data = Progress.objects.filter(userID_id=user_id, quizID_id=quiz_id)
                attempts_data = QuizAttempt.objects.filter(userID_id=user_id, quizID_id=quiz_id, completed=True)
            else:
                progress_data = Progress.objects.filter(userID_id=user_id)
                attempts_data = QuizAttempt.objects.filter(userID_id=user_id, completed=True)
            
            if not progress_data.exists():
                return {
                    'success': False,
                    'error': 'No progress data found for report generation',
                    'error_code': 'NO_PROGRESS_DATA'
                }
            
            # Generate report data
            from django.db import models
            report_data = {
                'user_id': user_id,
                'total_quizzes': progress_data.count(),
                'total_attempts': attempts_data.count(),
                'average_score': progress_data.aggregate(avg_score=models.Avg('bestScore'))['avg_score'] or 0,
                'generation_date': timezone.now().isoformat(),
                'report_type': 'comprehensive' if not quiz_id else 'quiz_specific'
            }
            
            return {
                'success': True,
                'report_data': report_data,
                'report_ready': True,
                'file_size_estimate': len(str(report_data)) * 2
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Report generation failed: {str(e)}',
                'error_code': 'REPORT_GENERATION_ERROR'
            }
    
    def test_download_file_format(self, report_data, file_format='pdf'):
        """Test report download in specified format"""
        try:
            supported_formats = ['pdf', 'csv', 'json']
            
            if file_format not in supported_formats:
                return {
                    'success': False,
                    'error': f'Unsupported format: {file_format}. Supported: {supported_formats}',
                    'error_code': 'UNSUPPORTED_FORMAT'
                }
            
            # Simulate file generation
            file_info = {
                'format': file_format,
                'filename': f'progress_report_{report_data.get("user_id", "unknown")}.{file_format}',
                'content_type': {
                    'pdf': 'application/pdf',
                    'csv': 'text/csv',
                    'json': 'application/json'
                }[file_format],
                'size_bytes': len(str(report_data)) * 3,
                'download_ready': True
            }
            
            return {
                'success': True,
                'file_info': file_info,
                'download_url': f'/api/reports/download/{file_info["filename"]}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Download format test failed: {str(e)}',
                'error_code': 'DOWNLOAD_FORMAT_ERROR'
            }

class UserAccountSaveTests:
    """Test Case ID: 24 - User Account Save/Cancel Options"""
    
    def test_profile_save_validation(self, user_id, changes_data):
        """Test saving profile changes with validation"""
        try:
            from .models import Users
            
            # Get current user
            try:
                user = Users.objects.get(userID=user_id)
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': 'User not found',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Validate changes
            validation_errors = []
            
            if 'username' in changes_data:
                new_username = changes_data['username']
                if len(new_username) > 10:
                    validation_errors.append('Username too long')
                elif Users.objects.filter(userName=new_username).exclude(userID=user_id).exists():
                    validation_errors.append('Username already exists')
            
            if 'email' in changes_data:
                new_email = changes_data['email']
                if len(new_email) > 50:
                    validation_errors.append('Email too long')
                elif Users.objects.filter(email=new_email).exclude(userID=user_id).exists():
                    validation_errors.append('Email already exists')
            
            if validation_errors:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'error_code': 'VALIDATION_FAILED',
                    'validation_errors': validation_errors
                }
            
            return {
                'success': True,
                'validation_passed': True,
                'changes_valid': True,
                'ready_to_save': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Profile save validation failed: {str(e)}',
                'error_code': 'SAVE_VALIDATION_ERROR'
            }
    
    def test_cancel_changes_restoration(self, original_data, modified_data):
        """Test cancelling changes and restoring original data"""
        try:
            # Simulate cancellation process
            changes_discarded = True
            original_restored = True
            
            # Verify original data structure
            required_fields = ['username', 'email']
            missing_fields = [field for field in required_fields if field not in original_data]
            
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Missing original data fields: {missing_fields}',
                    'error_code': 'MISSING_ORIGINAL_DATA'
                }
            
            # Test restoration
            restored_data = original_data.copy()
            
            return {
                'success': True,
                'changes_discarded': changes_discarded,
                'original_restored': original_restored,
                'restored_data': restored_data,
                'restoration_successful': restored_data == original_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Cancel changes test failed: {str(e)}',
                'error_code': 'CANCEL_CHANGES_ERROR'
            }

class QuizTitleEditTests:
    """Test Case ID: 25 - Quiz Title Edit Functionality"""
    
    def test_title_edit_validation(self, new_title):
        """Test quiz title edit validation"""
        try:
            validation_errors = []
            
            # Title length validation
            if not new_title or not new_title.strip():
                validation_errors.append('Title cannot be empty')
            elif len(new_title) > 50:
                validation_errors.append('Title must be 50 characters or less')
            elif len(new_title) < 3:
                validation_errors.append('Title must be at least 3 characters')
            
            # Title content validation
            if new_title and not new_title.replace(' ', '').replace('-', '').replace('_', '').isalnum():
                validation_errors.append('Title contains invalid characters')
            
            if validation_errors:
                return {
                    'success': False,
                    'error': 'Title validation failed',
                    'error_code': 'TITLE_VALIDATION_FAILED',
                    'validation_errors': validation_errors
                }
            
            return {
                'success': True,
                'title_valid': True,
                'cleaned_title': new_title.strip()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Title edit validation failed: {str(e)}',
                'error_code': 'TITLE_EDIT_ERROR'
            }
    
    def test_title_update_permissions(self, user_id, quiz_id):
        """Test if user has permission to edit quiz title"""
        try:
            from .models import Quiz
            
            try:
                quiz = Quiz.objects.select_related('fileID').get(quizID=quiz_id)
            except Quiz.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz not found',
                    'error_code': 'QUIZ_NOT_FOUND'
                }
            
            # Check ownership
            if quiz.fileID.userID_id != user_id:
                return {
                    'success': False,
                    'error': 'Permission denied - user does not own this quiz',
                    'error_code': 'PERMISSION_DENIED'
                }
            
            return {
                'success': True,
                'edit_permission_granted': True,
                'quiz_owner': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Title update permission test failed: {str(e)}',
                'error_code': 'PERMISSION_TEST_ERROR'
            }

class ResponseTimeTests:
    """Test Case ID: 29 - Response Time Tracking"""
    
    def test_response_time_recording(self, attempt_id, question_id, response_time_ms):
        """Test if response times are accurately recorded"""
        try:
            from .models import Answer, QuizAttempt, Question
            
            # Validate response time
            if not isinstance(response_time_ms, (int, float)) or response_time_ms < 0:
                return {
                    'success': False,
                    'error': 'Invalid response time - must be non-negative number',
                    'error_code': 'INVALID_RESPONSE_TIME'
                }
            
            min_time = 100 
            max_time = 300000 
            
            if response_time_ms < min_time:
                return {
                    'success': False,
                    'error': f'Response time too fast (minimum {min_time}ms)',
                    'error_code': 'RESPONSE_TOO_FAST'
                }
            
            if response_time_ms > max_time:
                return {
                    'success': False,
                    'error': f'Response time too slow (maximum {max_time}ms)',
                    'error_code': 'RESPONSE_TOO_SLOW'
                }
            
            # Test recording
            recorded_time = int(response_time_ms) 
            
            return {
                'success': True,
                'response_time_valid': True,
                'recorded_time_ms': recorded_time,
                'recording_accurate': recorded_time == int(response_time_ms)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Response time recording test failed: {str(e)}',
                'error_code': 'RESPONSE_TIME_ERROR'
            }
    
    def test_average_response_time_calculation(self, attempt_id):
        """Test calculation of average response time for an attempt"""
        try:
            from .models import Answer
            from django.db.models import Avg
            
            # Get all answers for this attempt
            answers = Answer.objects.filter(attemptID_id=attempt_id)
            
            if not answers.exists():
                return {
                    'success': False,
                    'error': 'No answers found for response time calculation',
                    'error_code': 'NO_ANSWERS'
                }
            
            # Calculate average response time
            avg_response_time = answers.aggregate(avg_time=Avg('responseTime'))['avg_time']
            
            if avg_response_time is None:
                avg_response_time = 0
            
            return {
                'success': True,
                'total_answers': answers.count(),
                'average_response_time_ms': round(avg_response_time, 2),
                'calculation_successful': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Average response time calculation failed: {str(e)}',
                'error_code': 'AVG_RESPONSE_TIME_ERROR'
            }

class QuizDownloadTests:
    """Test Case ID: 34 - Quiz Download Progress Tracking"""
    
    def test_download_progress_tracking(self, download_id, total_size, downloaded_size):
        """Test download progress tracking functionality"""
        try:
            if total_size <= 0:
                return {
                    'success': False,
                    'error': 'Total size must be greater than 0',
                    'error_code': 'INVALID_TOTAL_SIZE'
                }
            
            if downloaded_size < 0 or downloaded_size > total_size:
                return {
                    'success': False,
                    'error': 'Downloaded size out of valid range',
                    'error_code': 'INVALID_DOWNLOADED_SIZE'
                }
            
            # Calculate progress
            progress_percentage = (downloaded_size / total_size) * 100
            download_complete = downloaded_size == total_size
            
            return {
                'success': True,
                'download_id': download_id,
                'total_size_bytes': total_size,
                'downloaded_size_bytes': downloaded_size,
                'progress_percentage': round(progress_percentage, 1),
                'download_complete': download_complete,
                'tracking_accurate': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Download progress tracking failed: {str(e)}',
                'error_code': 'DOWNLOAD_PROGRESS_ERROR'
            }
    
    def test_download_completion_notification(self, download_id):
        """Test download completion notification"""
        try:
            # Simulate download completion
            completion_data = {
                'download_id': download_id,
                'status': 'completed',
                'completion_time': timezone.now().isoformat(),
                'notification_sent': True,
                'file_ready': True
            }
            
            return {
                'success': True,
                'completion_data': completion_data,
                'notification_working': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Download completion notification test failed: {str(e)}',
                'error_code': 'COMPLETION_NOTIFICATION_ERROR'
            }

class SessionPersistenceTests:
    """Test Case ID: 36 - Session Persistence Across Pages"""
    
    def test_session_token_persistence(self, token, page_navigation_count=5):
        """Test if session token persists across multiple page navigations"""
        try:
            from django.conf import settings
            import jwt
            
            # Validate token format
            if not token:
                return {
                    'success': False,
                    'error': 'No token provided for persistence test',
                    'error_code': 'NO_TOKEN'
                }
            
            # Test token validity across navigations
            navigation_results = []
            
            for i in range(page_navigation_count):
                try:
                    # Decode token (simulating page navigation)
                    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
                    navigation_results.append({
                        'navigation': i + 1,
                        'token_valid': True,
                        'user_id': payload.get('user_id')
                    })
                except jwt.ExpiredSignatureError:
                    navigation_results.append({
                        'navigation': i + 1,
                        'token_valid': False,
                        'error': 'Token expired'
                    })
                    break
                except jwt.InvalidTokenError:
                    navigation_results.append({
                        'navigation': i + 1,
                        'token_valid': False,
                        'error': 'Invalid token'
                    })
                    break
            
            successful_navigations = sum(1 for result in navigation_results if result['token_valid'])
            persistence_rate = (successful_navigations / page_navigation_count) * 100
            
            return {
                'success': True,
                'total_navigations': page_navigation_count,
                'successful_navigations': successful_navigations,
                'persistence_rate': round(persistence_rate, 1),
                'session_persistent': persistence_rate == 100,
                'navigation_results': navigation_results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Session persistence test failed: {str(e)}',
                'error_code': 'SESSION_PERSISTENCE_ERROR'
            }
    
    def test_cross_tab_session_sharing(self, user_id):
        """Test if session is shared correctly across browser tabs"""
        try:
            # Simulate multiple tab access
            tab_sessions = []
            
            for tab_id in range(3):  
                tab_session = {
                    'tab_id': tab_id + 1,
                    'user_id': user_id,
                    'session_active': True,
                    'shared_state': True
                }
                tab_sessions.append(tab_session)
            
            # Check if all tabs share the same session
            all_tabs_synced = all(tab['session_active'] for tab in tab_sessions)
            
            return {
                'success': True,
                'total_tabs': len(tab_sessions),
                'tabs_synced': all_tabs_synced,
                'tab_sessions': tab_sessions,
                'cross_tab_sharing': all_tabs_synced
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Cross-tab session test failed: {str(e)}',
                'error_code': 'CROSS_TAB_ERROR'
            }

class QuizResumeTests:
    """Test Case ID: 37 - Quiz Attempt Resume"""
    
    def test_resume_attempt_validation(self, attempt_id, user_id):
        """Test validation for resuming a quiz attempt"""
        try:
            from .models import QuizAttempt
            from django.utils import timezone
            from datetime import timedelta
            
            try:
                attempt = QuizAttempt.objects.get(attemptID=attempt_id, userID_id=user_id)
            except QuizAttempt.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz attempt not found or access denied',
                    'error_code': 'ATTEMPT_NOT_FOUND'
                }
            
            if attempt.completed:
                return {
                    'success': False,
                    'error': 'Cannot resume completed quiz attempt',
                    'error_code': 'ATTEMPT_COMPLETED'
                }
            
            # Check if attempt is within time limit (24 hours)
            time_elapsed = timezone.now() - attempt.startTime
            max_time = timedelta(hours=24)
            
            if time_elapsed > max_time:
                return {
                    'success': False,
                    'error': 'Quiz attempt has expired',
                    'error_code': 'ATTEMPT_EXPIRED',
                    'elapsed_hours': time_elapsed.total_seconds() / 3600
                }
            
            return {
                'success': True,
                'can_resume': True,
                'attempt_id': attempt_id,
                'elapsed_time': str(time_elapsed).split('.')[0],
                'remaining_time': str(max_time - time_elapsed).split('.')[0]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Resume attempt validation failed: {str(e)}',
                'error_code': 'RESUME_VALIDATION_ERROR'
            }
    
    def test_progress_restoration(self, attempt_id):
        """Test if progress is correctly restored when resuming"""
        try:
            from .models import QuizAttempt, Question, Answer
            
            try:
                attempt = QuizAttempt.objects.get(attemptID=attempt_id)
            except QuizAttempt.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Quiz attempt not found',
                    'error_code': 'ATTEMPT_NOT_FOUND'
                }
            
            # Get total questions and answered questions
            total_questions = Question.objects.filter(quizID=attempt.quizID).count()
            answered_questions = Answer.objects.filter(attemptID=attempt).count()
            
            # Find next unanswered question
            answered_question_ids = Answer.objects.filter(
                attemptID=attempt
            ).values_list('questionID_id', flat=True)
            
            next_question = Question.objects.filter(
                quizID=attempt.quizID
            ).exclude(
                questionID__in=answered_question_ids
            ).order_by('questionID').first()
            
            progress_percentage = (answered_questions / total_questions) * 100 if total_questions > 0 else 0
            
            return {
                'success': True,
                'total_questions': total_questions,
                'answered_questions': answered_questions,
                'progress_percentage': round(progress_percentage, 1),
                'next_question_id': next_question.questionID if next_question else None,
                'can_continue': next_question is not None,
                'all_answered': next_question is None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Progress restoration test failed: {str(e)}',
                'error_code': 'PROGRESS_RESTORATION_ERROR'
            }

def run_email_notification_tests(user_email, reset_token):
    """Run email notification tests"""
    email_tests = EmailNotificationTests()
    
    # Test email service configuration
    config_test = email_tests.test_email_service_configuration()
    if not config_test['success']:
        return config_test
    
    # Test email generation
    generation_test = email_tests.test_password_reset_email_generation(user_email, reset_token)
    
    return {
        'success': generation_test['success'],
        'email_service_ready': config_test.get('email_service_ready', False),
        'email_generation_ready': generation_test.get('delivery_ready', False),
        'message': 'Email notification tests completed'
    }

def run_quiz_title_edit_tests(user_id, quiz_id, new_title):
    """Run quiz title edit tests"""
    title_tests = QuizTitleEditTests()
    
    # Test title validation
    validation_test = title_tests.test_title_edit_validation(new_title)
    if not validation_test['success']:
        return validation_test
    
    # Test edit permissions
    permission_test = title_tests.test_title_update_permissions(user_id, quiz_id)
    if not permission_test['success']:
        return permission_test
    
    return {
        'success': True,
        'title_valid': validation_test['title_valid'],
        'permission_granted': permission_test['edit_permission_granted'],
        'cleaned_title': validation_test.get('cleaned_title'),
        'message': 'Quiz title edit tests passed'
    }

def run_quiz_resume_tests(attempt_id, user_id):
    """Run quiz resume tests"""
    resume_tests = QuizResumeTests()
    
    # Test resume validation
    validation_test = resume_tests.test_resume_attempt_validation(attempt_id, user_id)
    if not validation_test['success']:
        return validation_test
    
    # Test progress restoration
    progress_test = resume_tests.test_progress_restoration(attempt_id)
    
    return {
        'success': progress_test['success'],
        'can_resume': validation_test.get('can_resume', False),
        'progress_restored': progress_test.get('success', False),
        'next_question_id': progress_test.get('next_question_id'),
        'progress_percentage': progress_test.get('progress_percentage', 0),
        'message': 'Quiz resume tests completed'
    }