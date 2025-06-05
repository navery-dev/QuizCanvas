from django.urls import path
from . import views

app_name = 'quizapp'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # User authentication
    path('api/register/', views.register_user, name='register_user'),
    path('api/login/', views.login_user, name='login_user'),
    
    # File upload and quiz management
    path('api/upload/', views.upload_quiz_file, name='upload_quiz_file'),
    path('api/quizzes/', views.get_user_quizzes, name='get_user_quizzes'),

    # Quiz taking apis
    path('api/quiz/<int:quiz_id>/start/', views.start_quiz_attempt, name='start_quiz_attempt'),
    path('api/attempt/<int:attempt_id>/question/<int:question_number>/', views.get_quiz_question, name='get_quiz_question'),
    path('api/attempt/<int:attempt_id>/answer/<int:question_id>/', views.submit_quiz_answer, name='submit_quiz_answer'),
    path('api/attempt/<int:attempt_id>/complete/', views.complete_quiz_attempt, name='complete_quiz_attempt'),
    
    # Quiz Management APIs 
    path('api/quiz/<int:quiz_id>/details/', views.get_quiz_details, name='get_quiz_details'),
    path('api/quiz/<int:quiz_id>/sections/', views.get_quiz_sections, name='get_quiz_sections'),
    path('api/quiz/<int:quiz_id>/section/<int:section_id>/questions/', views.get_section_questions, name='get_section_questions'),
    path('api/quiz/<int:quiz_id>/attempts/', views.get_user_quiz_attempts, name='get_user_quiz_attempts'),
]