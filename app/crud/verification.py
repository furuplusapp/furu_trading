from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.verification import EmailVerification, PasswordReset
from typing import Optional
import uuid
from datetime import datetime, timedelta


def create_email_verification(db: Session, user_id: int) -> EmailVerification:
    """Create email verification token"""
    # Delete any existing unused verification tokens for this user
    db.query(EmailVerification).filter(
        and_(
            EmailVerification.user_id == user_id,
            EmailVerification.is_used == False
        )
    ).delete()
    
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    verification = EmailVerification(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def get_email_verification(db: Session, token: str) -> Optional[EmailVerification]:
    """Get email verification by token"""
    return db.query(EmailVerification).filter(
        and_(
            EmailVerification.token == token,
            EmailVerification.is_used == False,
            EmailVerification.expires_at > datetime.utcnow()
        )
    ).first()


def mark_email_verification_used(db: Session, token: str) -> bool:
    """Mark email verification token as used"""
    verification = get_email_verification(db, token)
    if not verification:
        return False
    
    verification.is_used = True
    db.commit()
    return True


def create_password_reset(db: Session, user_id: int) -> PasswordReset:
    """Create password reset token"""
    # Delete any existing unused reset tokens for this user
    db.query(PasswordReset).filter(
        and_(
            PasswordReset.user_id == user_id,
            PasswordReset.is_used == False
        )
    ).delete()
    
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    reset = PasswordReset(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(reset)
    db.commit()
    db.refresh(reset)
    return reset


def get_password_reset(db: Session, token: str) -> Optional[PasswordReset]:
    """Get password reset by token"""
    return db.query(PasswordReset).filter(
        and_(
            PasswordReset.token == token,
            PasswordReset.is_used == False,
            PasswordReset.expires_at > datetime.utcnow()
        )
    ).first()


def mark_password_reset_used(db: Session, token: str) -> bool:
    """Mark password reset token as used"""
    reset = get_password_reset(db, token)
    if not reset:
        return False
    
    reset.is_used = True
    db.commit()
    return True