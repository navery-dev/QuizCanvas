from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unauthenticated access to API root
def api_root(request):
    return Response({
        'message': 'QuizCanvas API is running!',
        'version': '1.0.0',
        'environment': 'development' if settings.DEBUG else 'production',
        'authentication': 'JWT',
        'endpoints': {
            'auth': {
                'token': '/api/auth/token/',
                'refresh': '/api/auth/token/refresh/',
            },
            'api_root': '/api/',
        }
    })