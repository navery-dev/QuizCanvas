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
from django.db import transaction, IntegrityError
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Max

import jwt

from .models import File, Quiz, Section, Question, Users, Progress, QuizAttempt, Answer
from .utils.file_processors import process_quiz_file
from .services.s3_service import get_s3_service

# Configure logging
logger = logging.getLogger(__name__)

def generate_jwt_token(user: Users) -> str:
    payload = {
        'user_id': user.userID,
        'username': user.userName,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValidationError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValidationError("Invalid token")

def jwt_required(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'error': 'Authorization token required'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = verify_jwt_token(token)
            user = Users.objects.get(userID=payload['user_id'])
            request.user = user
            return view_func(request, *args, **kwargs)
        except (ValidationError, Users.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired token'
            }, status=401)
    return wrapper

@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    try:
        data = json.loads(request.body)
        
        # Validate input
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not all([username, email, password]):
            return JsonResponse({
                'success': False,
                'error': 'Username, email, and password are required'
            }, status=400)
        
        # Validate field lengths
        if len(username) > 10:
            return JsonResponse({
                'success': False,
                'error': 'Username must be 10 characters or less'
            }, status=400)
        
        if len(email) > 50:
            return JsonResponse({
                'success': False,
                'error': 'Email must be 50 characters or less'
            }, status=400)
        
        if len(password) > 20:
            return JsonResponse({
                'success': False,
                'error': 'Password must be 20 characters or less'
            }, status=400)
        
        # Check if user already exists
        if Users.objects.filter(userName=username).exists():
            return JsonResponse({
                'success': False,
                'error': 'Username already exists'
            }, status=409)
        
        if Users.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'Email already exists'
            }, status=409)
        
        # Create user with hashed password
        hashed_password = make_password(password)
        
        with transaction.atomic():
            user = Users.objects.create(
                userName=username,
                email=email,
                password=hashed_password
            )
        
        logger.info(f"New user registered: {username}")
        token = generate_jwt_token(user)
        
        return JsonResponse({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user_id': user.userID,
                'username': user.userName,
                'email': user.email,
                'token': token
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    try:
        data = json.loads(request.body)
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'error': 'Username and password are required'
            }, status=400)
        
        try:
            user = Users.objects.get(userName=username)
            
            if check_password(password, user.password):
                token = generate_jwt_token(user)
                logger.info(f"User logged in: {username}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'data': {
                        'user_id': user.userID,
                        'username': user.userName,
                        'email': user.email,
                        'token': token
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid username or password'
                }, status=401)
                
        except Users.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid username or password'
            }, status=401)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_quiz_file(request):
    try:
        # Check if file was uploaded
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        user = request.user
        
        # Validate file
        if not uploaded_file.name:
            return JsonResponse({
                'success': False,
                'error': 'Invalid file name'
            }, status=400)
        
        # File size validation
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': f'File size exceeds 10MB limit'
            }, status=400)
        
        # Process the file
        try:
            logger.info(f"Processing file upload: {uploaded_file.name} by user {user.userName}")
            questions_data, metadata = process_quiz_file(uploaded_file)
        except ValidationError as e:
            error_message = str(e.message) if hasattr(e, 'message') else str(e)
            logger.warning(f"File processing error: {error_message}")
            return JsonResponse({
                'success': False,
                'error': error_message
            }, status=400)
        
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
                
                # Upload to S3
                s3_service = get_s3_service()
                s3_result = s3_service.upload_quiz_file(
                    uploaded_file, 
                    user.userID, 
                    uploaded_file.name
                )
                
                # Update file record with S3 path
                file_record.filePath = s3_result['s3_key'][:100]
                file_record.save()
                
                logger.info(f"File uploaded to S3: {s3_result['s3_key']}")
                
                # Create Quiz record
                quiz_title = request.POST.get('quiz_title', uploaded_file.name.split('.')[0])[:50]
                quiz_description = request.POST.get('quiz_description', 
                                                 f"Quiz imported from {uploaded_file.name}")[:200]
                
                quiz = Quiz.objects.create(
                    fileID=file_record,
                    title=quiz_title,
                    description=quiz_description
                )
                
                # Create sections and questions
                sections_created = {}
                questions_created = []
                
                for question_data in questions_data:
                    # Get or create section
                    section_name = question_data['section'][:50]
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
                
                logger.info(f"Successfully processed upload: {len(questions_created)} questions created")
        
        except Exception as e:
            logger.error(f"Error during file upload processing: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Upload processing failed: {str(e)}'
            }, status=500)
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'data': {
                'file_id': file_record.fileID,
                'quiz_id': quiz.quizID,
                'quiz_title': quiz.title,
                'total_questions': len(questions_created),
                'sections': list(sections_created.keys()),
                'metadata': metadata,
                's3_info': {
                    'key': s3_result['s3_key'],
                    'size': s3_result['file_size']
                }
            }
        }, status=201)
        
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_user_quizzes(request):
    try:
        user = request.user
        
        # Get user's files and quizzes
        files = File.objects.filter(userID=user)
        
        quizzes_data = []
        for file in files:
            quizzes = Quiz.objects.filter(fileID=file)
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
        
        return JsonResponse({
            'success': True,
            'data': {
                'quizzes': quizzes_data,
                'total_count': len(quizzes_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user quizzes: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        's3_configured': bool(settings.AWS_ACCESS_KEY_ID)
    })

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_quiz_details(request, quiz_id):
    try:
        user = request.user
        
        # Get quiz and verify access
        try:
            quiz = Quiz.objects.get(quizID=quiz_id)
            # Verify user owns this quiz
            if quiz.fileID.userID != user:
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied to this quiz'
                }, status=403)
        except Quiz.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Quiz not found'
            }, status=404)
        
        # Get sections with questions
        sections_data = []
        sections = Section.objects.filter(quizID=quiz).order_by('sectionName')
        
        for section in sections:
            questions = Question.objects.filter(sectionID=section).order_by('questionID')
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
        
        return JsonResponse({
            'success': True,
            'data': {
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
        })
        
    except Exception as e:
        logger.error(f"Error getting quiz details: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_quiz_sections(request, quiz_id):

    try:
        user = request.user
        
        # Verify quiz exists and user has access
        try:
            quiz = Quiz.objects.get(quizID=quiz_id)
            if quiz.fileID.userID != user:
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied to this quiz'
                }, status=403)
        except Quiz.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Quiz not found'
            }, status=404)
        
        # Get sections with question counts
        sections = Section.objects.filter(quizID=quiz).order_by('sectionName')
        sections_data = []
        
        for section in sections:
            question_count = Question.objects.filter(sectionID=section).count()
            sections_data.append({
                'section_id': section.sectionID,
                'name': section.sectionName,
                'description': section.sectionDesc or '',
                'question_count': question_count
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'quiz_title': quiz.title,
                'sections': sections_data,
                'total_sections': len(sections_data),
                'total_questions': sum(s['question_count'] for s in sections_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting quiz sections: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_section_questions(request, quiz_id, section_id):
    try:
        user = request.user
        
        # Verify quiz and section exist and user has access
        try:
            quiz = Quiz.objects.get(quizID=quiz_id)
            if quiz.fileID.userID != user:
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied to this quiz'
                }, status=403)
                
            section = Section.objects.get(sectionID=section_id, quizID=quiz)
        except Quiz.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Quiz not found'
            }, status=404)
        except Section.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Section not found'
            }, status=404)
        
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
        
        return JsonResponse({
            'success': True,
            'data': {
                'section': {
                    'section_id': section.sectionID,
                    'name': section.sectionName,
                    'description': section.sectionDesc or ''
                },
                'quiz_title': quiz.title,
                'questions': questions_data,
                'question_count': len(questions_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting section questions: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_user_quiz_attempts(request, quiz_id):
    try:
        user = request.user
        
        # Verify quiz exists and user has access
        try:
            quiz = Quiz.objects.get(quizID=quiz_id)
            if quiz.fileID.userID != user:
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied to this quiz'
                }, status=403)
        except Quiz.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Quiz not found'
            }, status=404)
        
        # Get user's attempts for this quiz
        attempts = QuizAttempt.objects.filter(
            userID=user, 
            quizID=quiz
        ).order_by('-startTime')
        
        attempts_data = []
        for attempt in attempts:
            # Get answer statistics for this attempt
            total_answers = Answer.objects.filter(attemptID=attempt).count()
            correct_answers = Answer.objects.filter(attemptID=attempt, isCorrect=True).count()
            
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
        
        return JsonResponse({
            'success': True,
            'data': {
                'quiz_title': quiz.title,
                'attempts': attempts_data,
                'total_attempts': len(attempts_data),
                'completed_attempts': len([a for a in attempts_data if a['completed']]),
                'best_score': max([a['score'] for a in attempts_data if a['score'] is not None], default=0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user quiz attempts: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def start_quiz_attempt(request, quiz_id):
    try:
        user = request.user
        
        # Verify quiz exists and user has access
        try:
            quiz = Quiz.objects.get(quizID=quiz_id)
            # Verify user owns this quiz (uploaded it)
            if quiz.fileID.userID != user:
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied to this quiz'
                }, status=403)
        except Quiz.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Quiz not found'
            }, status=404)
        
        # Check if user has an incomplete attempt for this quiz
        incomplete_attempt = QuizAttempt.objects.filter(
            userID=user,
            quizID=quiz,
            completed=False
        ).first()
        
        if incomplete_attempt:
            return JsonResponse({
                'success': False,
                'error': 'You have an incomplete attempt for this quiz',
                'data': {
                    'attempt_id': incomplete_attempt.attemptID,
                    'started_at': incomplete_attempt.startTime.isoformat()
                }
            }, status=409)
        
        # Create new quiz attempt
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
                return JsonResponse({
                    'success': False,
                    'error': 'No questions found in this quiz'
                }, status=400)
            
            logger.info(f"User {user.userName} started quiz {quiz.title}")
            
            return JsonResponse({
                'success': True,
                'message': 'Quiz attempt started successfully',
                'data': {
                    'attempt_id': quiz_attempt.attemptID,
                    'quiz_title': quiz.title,
                    'total_questions': Question.objects.filter(quizID=quiz).count(),
                    'first_question': {
                        'question_id': first_question.questionID,
                        'text': first_question.questionText,
                        'options': first_question.answerOptions,
                        'section': first_question.sectionID.sectionName if first_question.sectionID else 'General'
                    }
                }
            }, status=201)
            
    except Exception as e:
        logger.error(f"Error starting quiz attempt: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_quiz_question(request, attempt_id, question_number):
    try:
        user = request.user
        
        # Verify quiz attempt belongs to user
        try:
            quiz_attempt = QuizAttempt.objects.get(attemptID=attempt_id, userID=user)
        except QuizAttempt.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Quiz attempt not found'
            }, status=404)
        
        if quiz_attempt.completed:
            return JsonResponse({
                'success': False,
                'error': 'Quiz attempt already completed'
            }, status=400)
        
        # Get all questions for this quiz in order
        questions = Question.objects.filter(quizID=quiz_attempt.quizID).order_by('questionID')
        total_questions = questions.count()
        
        # Validate question number
        if question_number < 1 or question_number > total_questions:
            return JsonResponse({
                'success': False,
                'error': f'Question number must be between 1 and {total_questions}'
            }, status=400)
        
        # Get the specific question (question_number is 1-based)
        question = questions[question_number - 1]
        
        # Check if user already answered this question
        existing_answer = Answer.objects.filter(
            attemptID=quiz_attempt,
            questionID=question
        ).first()
        
        return JsonResponse({
            'success': True,
            'data': {
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
                'previous_answer': existing_answer.selectedOption if existing_answer else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting quiz question: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def submit_quiz_answer(request, attempt_id, question_id):
   try:
       user = request.user
       data = json.loads(request.body)
       
       # Validate input
       selected_option = data.get('selected_option')
       if selected_option is None or not isinstance(selected_option, int):
           return JsonResponse({
               'success': False,
               'error': 'selected_option must be an integer'
           }, status=400)
       
       # Get response time from frontend (in milliseconds)
       response_time = data.get('response_time', 0)
       if not isinstance(response_time, (int, float)) or response_time < 0:
           response_time = 0  # Default to 0 if invalid
       
       # Verify quiz attempt belongs to user
       try:
           quiz_attempt = QuizAttempt.objects.get(attemptID=attempt_id, userID=user)
       except QuizAttempt.DoesNotExist:
           return JsonResponse({
               'success': False,
               'error': 'Quiz attempt not found'
           }, status=404)
       
       if quiz_attempt.completed:
           return JsonResponse({
               'success': False,
               'error': 'Quiz attempt already completed'
           }, status=400)
       
       # Verify question belongs to this quiz
       try:
           question = Question.objects.get(questionID=question_id, quizID=quiz_attempt.quizID)
       except Question.DoesNotExist:
           return JsonResponse({
               'success': False,
               'error': 'Question not found in this quiz'
           }, status=404)
       
       # Validate selected option is within range
       if selected_option < 0 or selected_option >= len(question.answerOptions):
           return JsonResponse({
               'success': False,
               'error': f'selected_option must be between 0 and {len(question.answerOptions) - 1}'
           }, status=400)
       
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
           
           logger.info(f"User {user.userName} answered question {question_id}: {'correct' if is_correct else 'incorrect'} (response time: {response_time}ms)")
       
       return JsonResponse({
           'success': True,
           'message': 'Answer submitted successfully',
           'data': {
               'is_correct': is_correct,
               'correct_answer': question.answerOptions[question.answerIndex],
               'selected_answer': question.answerOptions[selected_option],
               'response_time': response_time
           }
       })
       
   except json.JSONDecodeError:
       return JsonResponse({
           'success': False,
           'error': 'Invalid JSON data'
       }, status=400)
   except Exception as e:
       logger.error(f"Error submitting quiz answer: {e}")
       return JsonResponse({
           'success': False,
           'error': 'Internal server error'
       }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def complete_quiz_attempt(request, attempt_id):
    try:
        user = request.user
        
        # Verify quiz attempt belongs to user
        try:
            quiz_attempt = QuizAttempt.objects.get(attemptID=attempt_id, userID=user)
        except QuizAttempt.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Quiz attempt not found'
            }, status=404)
        
        if quiz_attempt.completed:
            return JsonResponse({
                'success': False,
                'error': 'Quiz attempt already completed'
            }, status=400)
        
        # Calculate score
        with transaction.atomic():
            # Get all answers for this attempt
            answers = Answer.objects.filter(attemptID=quiz_attempt)
            total_questions = Question.objects.filter(quizID=quiz_attempt.quizID).count()
            correct_answers = answers.filter(isCorrect=True).count()
            
            # Calculate score percentage
            score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            # Update quiz attempt
            quiz_attempt.endTime = timezone.now()
            quiz_attempt.score = score
            quiz_attempt.completed = True
            quiz_attempt.save()
            
            # Update user progress
            progress, created = Progress.objects.update_or_create(
                userID=user,
                quizID=quiz_attempt.quizID,
                defaults={
                    'attemptsCount': Progress.objects.filter(
                        userID=user, 
                        quizID=quiz_attempt.quizID
                    ).count() + 1,
                    'bestScore': max(
                        score,
                        Progress.objects.filter(
                            userID=user, 
                            quizID=quiz_attempt.quizID
                        ).aggregate(Max('bestScore'))['bestScore__max'] or 0
                    ),
                    'lastAttemptDate': timezone.now(),
                    'masteryLevel': calculate_mastery_level(score)
                }
            )
            
            logger.info(f"User {user.userName} completed quiz {quiz_attempt.quizID.title} with score {score}%")
        
        return JsonResponse({
            'success': True,
            'message': 'Quiz completed successfully',
            'data': {
                'score': round(score, 1),
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'time_taken': str(quiz_attempt.endTime - quiz_attempt.startTime),
                'mastery_level': calculate_mastery_level(score),
                'quiz_title': quiz_attempt.quizID.title
            }
        })
        
    except Exception as e:
        logger.error(f"Error completing quiz attempt: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

def calculate_mastery_level(score):
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