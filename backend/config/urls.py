from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    """Simple API root endpoint"""
    return JsonResponse({
        'message': 'QuizCanvas API is running',
        'version': '1.0',
        'status': 'healthy',
        'available_endpoints': [
            '/api/auth/register/',
            '/api/auth/login/',
            '/api/health/',
            '/admin/'
        ]
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('quizapp.urls')),
    path('api/', api_root),
]