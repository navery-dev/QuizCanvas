import logging
import smtplib
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails with improved error handling"""
    
    def __init__(self):
        """Initialize email service and validate configuration"""
        self._validate_email_configuration()
    
    def _validate_email_configuration(self):
        """Validate that all required email settings are configured"""
        required_settings = [
            'EMAIL_HOST',
            'EMAIL_PORT', 
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD',
            'DEFAULT_FROM_EMAIL'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ImproperlyConfigured(
                f"Missing email configuration settings: {', '.join(missing_settings)}"
            )
        
        logger.info("Email configuration validated successfully")
    
    def test_email_connection(self):
        """Test email server connection"""
        try:
            connection = get_connection()
            connection.open()
            connection.close()
            logger.info("Email connection test successful")
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> None:
        """Send password reset email with comprehensive error handling"""
        try:
            # Validate inputs
            if not to_email or '@' not in to_email:
                raise ValueError("Invalid email address provided")
            
            if not reset_token:
                raise ValueError("Reset token is required")
            
            # Test connection first
            if not self.test_email_connection():
                raise ConnectionError("Unable to connect to email server")
            
            # Generate email content
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

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #3498db; text-align: center;">Password Reset Request</h2>
                    <p>Hello,</p>
                    <p>You requested a password reset for your QuizCanvas account.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #4CAF50; 
                                  color: white; 
                                  padding: 12px 24px; 
                                  text-decoration: none; 
                                  border-radius: 5px; 
                                  display: inline-block;
                                  font-weight: bold;">
                            Reset Password
                        </a>
                    </div>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request this reset, please ignore this email.</p>
                    <hr style="border: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #7f8c8d; font-size: 14px;">
                        Best regards,<br>
                        QuizCanvas Team
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Create and send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email]
            )
            msg.attach_alternative(html_body, "text/html")
            
            # Send with explicit error handling
            try:
                msg.send(fail_silently=False)
                logger.info(f"Password reset email sent successfully to {to_email}")
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP Authentication failed: {e}")
                raise ConnectionError("Email authentication failed. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD.")
                
            except smtplib.SMTPRecipientsRefused as e:
                logger.error(f"Recipients refused: {e}")
                raise ValueError(f"Email address {to_email} was refused by the server")
                
            except smtplib.SMTPServerDisconnected as e:
                logger.error(f"SMTP server disconnected: {e}")
                raise ConnectionError("Email server disconnected unexpectedly")
                
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error occurred: {e}")
                raise ConnectionError(f"Email sending failed: {e}")
                
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {e}")
            raise  # Re-raise the exception so calling code can handle it


# Utility function for debugging email configuration
def debug_email_configuration():
    """Debug function to check email configuration"""
    config_info = {
        'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'NOT SET'),
        'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'NOT SET'),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'NOT SET'),
        'EMAIL_HOST_PASSWORD': '***SET***' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'NOT SET',
        'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'NOT SET'),
        'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET'),
    }
    
    logger.info("Email Configuration:")
    for key, value in config_info.items():
        logger.info(f"  {key}: {value}")
    
    return config_info