import logging
import smtplib
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class EmailService:
    """Improved Gmail email service with proper error handling"""
    
    def __init__(self):
        """Initialize and validate Gmail configuration"""
        self._validate_gmail_configuration()
    
    def _validate_gmail_configuration(self):
        """Validate Gmail-specific configuration"""
        required_settings = [
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD',
            'EMAIL_HOST',
            'EMAIL_PORT'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ImproperlyConfigured(
                f"Missing Gmail configuration settings: {', '.join(missing_settings)}"
            )
        
        # Verify Gmail-specific settings
        if getattr(settings, 'EMAIL_HOST') != 'smtp.gmail.com':
            logger.warning(f"EMAIL_HOST is {getattr(settings, 'EMAIL_HOST')}, expected smtp.gmail.com for Gmail")
        
        if getattr(settings, 'EMAIL_PORT') != 587:
            logger.warning(f"EMAIL_PORT is {getattr(settings, 'EMAIL_PORT')}, expected 587 for Gmail")
        
        email_user = getattr(settings, 'EMAIL_HOST_USER', '')
        if not email_user.endswith('@gmail.com'):
            logger.warning(f"EMAIL_HOST_USER {email_user} doesn't appear to be a Gmail address")
        
        logger.info("Gmail email configuration validated")
    
    def test_email_connection(self):
        """Test Gmail SMTP connection"""
        try:
            logger.info("Testing Gmail SMTP connection...")
            connection = get_connection()
            connection.open()
            connection.close()
            logger.info("Gmail connection test successful")
            return True
        except Exception as e:
            logger.error(f"Gmail connection test failed: {e}")
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> None:
        """Send password reset email with comprehensive error handling"""
        try:
            # Validate inputs
            if not to_email or '@' not in to_email:
                raise ValueError("Invalid email address provided")
            
            if not reset_token:
                raise ValueError("Reset token is required")
            
            logger.info(f"Attempting to send password reset email to {to_email}")
            
            # Test connection first
            if not self.test_email_connection():
                raise ConnectionError("Unable to connect to Gmail SMTP server")
            
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
                    <h2 style="color: #3498db; text-align: center;">QuizCanvas Password Reset</h2>
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
                            Reset Your Password
                        </a>
                    </div>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request this reset, please ignore this email.</p>
                    <hr style="border: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #7f8c8d; font-size: 14px;">
                        Best regards,<br>QuizCanvas Team
                    </p>
                </div>
            </body>
            </html>
            """
            
            logger.info(f"Creating email message for {to_email}")
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email]
            )
            msg.attach_alternative(html_body, "text/html")
            
            # Send with specific Gmail error handling
            try:
                logger.info(f"Sending email to {to_email} via Gmail...")
                msg.send(fail_silently=False)
                logger.info(f"Password reset email sent successfully to {to_email}")
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Gmail SMTP Authentication failed: {e}")
                raise ConnectionError(f"Gmail authentication failed. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD (app password). Error: {e}")
                
            except smtplib.SMTPRecipientsRefused as e:
                logger.error(f"Gmail recipients refused: {e}")
                raise ValueError(f"Email address {to_email} was refused by Gmail: {e}")
                
            except smtplib.SMTPServerDisconnected as e:
                logger.error(f"Gmail SMTP server disconnected: {e}")
                raise ConnectionError(f"Gmail server disconnected unexpectedly: {e}")
                
            except smtplib.SMTPException as e:
                logger.error(f"Gmail SMTP error occurred: {e}")
                raise ConnectionError(f"Gmail email sending failed: {e}")
                
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            raise  # Re-raise the exception so calling code can handle it


# Debug function
def debug_gmail_configuration():
    """Debug function to check Gmail configuration"""
    config_info = {
        'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'NOT SET'),
        'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'NOT SET'),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'NOT SET'),
        'EMAIL_HOST_PASSWORD': '***SET***' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'NOT SET',
        'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'NOT SET'),
        'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET'),
        'FRONTEND_BASE_URL': getattr(settings, 'FRONTEND_BASE_URL', 'NOT SET'),
    }
    
    logger.info("Gmail Configuration Debug:")
    for key, value in config_info.items():
        logger.info(f"  {key}: {value}")
    
    # Check Gmail optimization
    gmail_optimized = (
        getattr(settings, 'EMAIL_HOST', '') == 'smtp.gmail.com' and
        getattr(settings, 'EMAIL_PORT', 0) == 587 and
        getattr(settings, 'EMAIL_USE_TLS', False) is True
    )
    
    config_info['gmail_optimized'] = gmail_optimized
    logger.info(f"  Gmail optimized: {gmail_optimized}")
    
    return config_info