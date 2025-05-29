from django.urls import path
from . import views

app_name = 'quizapp'

urlpatterns = [
    # API root endpoint
    path('', views.api_root, name='api_root'),
    
    
]