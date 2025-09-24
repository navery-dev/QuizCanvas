from django.urls import path
from . import views

app_name = 'quizapp'

urlpatterns = [
    # User Management
    path('auth/register/', views.register_user, name='register_user'),  
    path('auth/login/', views.login_user, name='login_user'),  
    path('auth/logout/', views.logout_user, name='logout_user'),  
    path('auth/profile/', views.update_user_profile, name='update_user_profile'), 
    path('auth/password-reset/', views.reset_password_request, name='reset_password_request'),  
    path('auth/password-reset/confirm/', views.reset_password_confirm, name='reset_password_confirm'),
    path('auth/change-password/', views.change_password, name='change_password'),
    path('auth/save-options/', views.get_user_account_save_options, name='user_save_options'),  
    
    # File Management
    path('files/upload/', views.upload_quiz_file, name='upload_quiz_file'),  
    
    # Quiz Management
    path('quizzes/', views.get_user_quizzes, name='get_user_quizzes'),
    path('quizzes/<int:quiz_id>/', views.get_quiz_details, name='get_quiz_details'),
    path('quizzes/<int:quiz_id>/sections/', views.get_quiz_sections, name='get_quiz_sections'),  
    path('quizzes/<int:quiz_id>/sections/<int:section_id>/questions/', views.get_section_questions, name='get_section_questions'),
    path('quizzes/<int:quiz_id>/update-title/', views.update_quiz_title, name='update_quiz_title'),
    path('quizzes/<int:quiz_id>/update-description/', views.update_quiz_description, name='update_quiz_description'),
    path('quizzes/<int:quiz_id>/sections/<int:section_id>/update/', views.update_section, name='update_section'),
    path('quizzes/<int:quiz_id>/questions/<int:question_id>/update/', views.update_question, name='update_question'),
    path('quizzes/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'), 
    path('quizzes/<int:quiz_id>/randomized/', views.get_randomized_quiz_questions, name='randomized_questions'),  
    
    # Quiz Taking
    path('quizzes/<int:quiz_id>/start/', views.start_quiz_attempt, name='start_quiz_attempt'),
    path('quizzes/<int:quiz_id>/sections/<int:section_id>/start/', views.start_quiz_attempt, name='start_section_quiz_attempt'),
    path('attempts/<int:attempt_id>/question/<int:question_number>/', views.get_quiz_question, name='get_quiz_question'),  
    path('attempts/<int:attempt_id>/answer/<int:question_id>/', views.submit_quiz_answer, name='submit_quiz_answer'), 
    path('attempts/<int:attempt_id>/complete/', views.complete_quiz_attempt, name='complete_quiz_attempt'),
    path('attempts/<int:attempt_id>/resume/', views.resume_quiz_attempt, name='resume_quiz_attempt'),
    path('attempts/<int:attempt_id>/end/', views.end_quiz_attempt, name='end_quiz_attempt'),
    path('attempts/<int:attempt_id>/timer/', views.get_timed_quiz_status, name='timed_quiz_status'),  
    path('attempts/<int:attempt_id>/progress/', views.get_quiz_progress_bar, name='quiz_progress_bar'),  
    
    # Quiz History & Results
    path('quizzes/<int:quiz_id>/attempts/', views.get_user_quiz_attempts, name='get_user_quiz_attempts'),
    path('attempts/<int:attempt_id>/details/', views.get_attempt_details, name='get_attempt_details'),
    
    # Progress & Analytics
    path('progress/', views.get_user_progress, name='get_user_progress_all'),  
    path('progress/<int:quiz_id>/', views.get_user_progress, name='get_user_progress_quiz'),  
    path('quizzes/<int:quiz_id>/statistics/', views.get_quiz_statistics, name='get_quiz_statistics'),
    path('dashboard/', views.get_user_dashboard, name='get_user_dashboard'),
    
    # System Health & Status
    path('health/', views.health_check, name='health_check'), 
    path('system/connections/', views.check_system_connections, name='system_connections'),  
    path('faq/', views.get_faq, name='get_faq'),  

    path('api/test-gmail/', views.test_gmail_connection, name='test_gmail'),
]