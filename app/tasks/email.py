import os
import resend
from app.tasks.celery_app import celery_app
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

# Set Resend API key
resend.api_key = settings.resend_api_key

@celery_app.task
def send_verification_email(email: str, token: str):
    """Send email verification email"""
    subject = "Verify your Furu AI account"
    
    # Create verification link
    verification_link = f"{os.getenv('FRONTEND_URL')}/verify-email?token={token}"
    
    # HTML email body
    html_body = f"""
    <html>
        <body>
            <h2>Welcome to Furu AI!</h2>
            <p>Thank you for registering. Please click the link below to verify your email address:</p>
            <p><a href="{verification_link}" style="background-color: #164e63; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <p>Best regards,<br>The Furu AI Team</p>
        </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    Welcome to Furu AI!
    
    Thank you for registering. Please click the link below to verify your email address:
    {verification_link}
    
    This link will expire in 24 hours.
    
    Best regards,
    The Furu AI Team
    """
    
    _send_email_resend(email, subject, html_body, text_body)


@celery_app.task
def send_password_reset_email(email: str, token: str):
    """Send password reset email"""
    subject = "Reset your Furu AI password"
    
    # Create reset link
    reset_link = f"{os.getenv('FRONTEND_URL')}/reset-password?token={token}"
    
    # HTML email body
    html_body = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Click the link below to reset it:</p>
            <p><a href="{reset_link}" style="background-color: #164e63; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{reset_link}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>Best regards,<br>The Furu AI Team</p>
        </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    Password Reset Request
    
    You requested to reset your password. Click the link below to reset it:
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    The Furu AI Team
    """
    
    _send_email_resend(email, subject, html_body, text_body)


def _send_email_resend(to_email: str, subject: str, html_body: str, text_body: str):
    """Send email using Resend API"""
    try:
        print(f"Sending email to {to_email} via Resend API")
        
        # Send email using Resend
        r = resend.Emails.send({
            "from": settings.from_email,
            "to": to_email,
            "subject": subject,
            "html": html_body,
            "text": text_body
        })
        
        print(f"Email sent successfully to {to_email} via Resend. ID: {r.get('id', 'unknown')}")
        return r
        
    except Exception as e:
        print(f"Failed to send email via Resend: {str(e)}")
        raise e