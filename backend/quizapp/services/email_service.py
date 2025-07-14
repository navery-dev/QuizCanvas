import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    def send_password_reset_email(self, to_email: str, reset_token: str) -> None:
        reset_url = f"{settings.FRONTEND_BASE_URL}/reset-password?token={reset_token}"
        subject = "QuizCanvas Password Reset"
        text_body = f"""Hello,

You requested a password reset for your QuizCanvas account.

Click the following link to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this reset, please ignore this email.

Best regards,
QuizCanvas Team"""
        html_body = (
            f"<html><body><h2>Password Reset Request</h2>"
            f"<p>Hello,</p>"
            f"<p>You requested a password reset for your QuizCanvas account.</p>"
            f"<p><a href=\"{reset_url}\" style=\"background-color: #4CAF50; color: white;"
            f" padding: 10px 20px; text-decoration: none; border-radius: 5px;\">Reset Password</a></p>"
            f"<p>This link will expire in 1 hour.</p>"
            f"<p>If you didn't request this reset, please ignore this email.</p>"
            f"<p>Best regards,<br>QuizCanvas Team</p></body></html>"
        )
        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [to_email])
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info("Password reset email sent to %s", to_email)

