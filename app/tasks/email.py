import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.tasks.celery_app import celery_app
from app.core.config import settings


@celery_app.task
def send_verification_email(email: str, token: str):
    """Send email verification email"""
    subject = "Verify your Furu AI account"
    
    # Create verification link
    verification_link = f"http://localhost:3000/verify-email?token={token}"
    
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
    
    _send_email(email, subject, html_body, text_body)


@celery_app.task
def send_password_reset_email(email: str, token: str):
    """Send password reset email"""
    subject = "Reset your Furu AI password"
    
    # Create reset link
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    
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
    
    _send_email(email, subject, html_body, text_body)


def _send_email(to_email: str, subject: str, html_body: str, text_body: str):
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.from_email
        msg["To"] = to_email
        
        # Add both plain text and HTML versions
        text_part = MIMEText(text_body, "plain")
        html_part = MIMEText(html_body, "html")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
            
        print(f"Email sent successfully to {to_email}")
        
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        raise e