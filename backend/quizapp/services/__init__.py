# Services package for QuizCanvas
# Provides helper functions to access service instances

from .email_service import EmailService

_email_service = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
