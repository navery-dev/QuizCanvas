from django.urls import path
from . import views

app_name = 'quizapp'

urlpatterns = [
    # User Management
    path('api/auth/register/', views.register_user, name='register_user'),  
    path('api/auth/login/', views.login_user, name='login_user'),  
    path('api/auth/logout/', views.logout_user, name='logout_user'),  
    path('api/auth/profile/', views.update_user_profile, name='update_user_profile'), 
    path('api/auth/password-reset/', views.reset_password_request, name='reset_password_request'),  
    path('api/auth/password-reset/confirm/', views.reset_password_confirm, name='reset_password_confirm'),  
    path('api/auth/save-options/', views.get_user_account_save_options, name='user_save_options'),  
    
    # File Management
    path('api/files/upload/', views.upload_quiz_file, name='upload_quiz_file'),  
    
    # Quiz Management
    path('api/quizzes/', views.get_user_quizzes, name='get_user_quizzes'),
    path('api/quizzes/<int:quiz_id>/', views.get_quiz_details, name='get_quiz_details'),
    path('api/quizzes/<int:quiz_id>/sections/', views.get_quiz_sections, name='get_quiz_sections'),  
    path('api/quizzes/<int:quiz_id>/sections/<int:section_id>/questions/', views.get_section_questions, name='get_section_questions'),
    path('api/quizzes/<int:quiz_id>/update-title/', views.update_quiz_title, name='update_quiz_title'), 
    path('api/quizzes/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),  
    path('api/quizzes/<int:quiz_id>/randomized/', views.get_randomized_quiz_questions, name='randomized_questions'),  
    
    # Quiz Taking
    path('api/quizzes/<int:quiz_id>/start/', views.start_quiz_attempt, name='start_quiz_attempt'),  
    path('api/attempts/<int:attempt_id>/question/<int:question_number>/', views.get_quiz_question, name='get_quiz_question'),  
    path('api/attempts/<int:attempt_id>/answer/<int:question_id>/', views.submit_quiz_answer, name='submit_quiz_answer'), 
    path('api/attempts/<int:attempt_id>/complete/', views.complete_quiz_attempt, name='complete_quiz_attempt'),  
    path('api/attempts/<int:attempt_id>/resume/', views.resume_quiz_attempt, name='resume_quiz_attempt'),  
    path('api/attempts/<int:attempt_id>/timer/', views.get_timed_quiz_status, name='timed_quiz_status'),  
    path('api/attempts/<int:attempt_id>/progress/', views.get_quiz_progress_bar, name='quiz_progress_bar'),  
    
    # Quiz History & Results
    path('api/quizzes/<int:quiz_id>/attempts/', views.get_user_quiz_attempts, name='get_user_quiz_attempts'),
    path('api/attempts/<int:attempt_id>/details/', views.get_attempt_details, name='get_attempt_details'),
    
    # Progress & Analytics
    path('api/progress/', views.get_user_progress, name='get_user_progress_all'),  
    path('api/progress/<int:quiz_id>/', views.get_user_progress, name='get_user_progress_quiz'),  
    path('api/quizzes/<int:quiz_id>/statistics/', views.get_quiz_statistics, name='get_quiz_statistics'),
    path('api/dashboard/', views.get_user_dashboard, name='get_user_dashboard'),
    
    # System Health & Status
    path('api/health/', views.health_check, name='health_check'), 
    path('api/system/connections/', views.check_system_connections, name='system_connections'),  
    path('api/faq/', views.get_faq, name='get_faq'),  
]