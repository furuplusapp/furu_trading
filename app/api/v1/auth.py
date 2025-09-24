from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.crud.user import create_user, authenticate_user, get_user_by_email, update_last_login, verify_user_email
from app.crud.verification import create_email_verification, get_email_verification, mark_email_verification_used
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse, EmailVerification, PasswordResetRequest, PasswordReset
from app.tasks.email import send_verification_email
from app.api.dependencies import get_current_user
from datetime import timedelta
from jose import jwt
import base64
import json

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    from app.core.security import validate_password_strength
    
    print("user in register", user)
    
    # Check if user already exists
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, message = validate_password_strength(user.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Create user
    db_user = create_user(db, user)
    
    # Create email verification token
    verification = create_email_verification(db, db_user.id)
    
    # Send verification email (async)
    send_verification_email.delay(db_user.email, verification.token)
    
    return db_user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return tokens"""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email before logging in. Check your inbox for a verification link."
        )
    
    # Update last login
    update_last_login(db, user)
    
    # Create tokens with different expiration based on remember me
    if user_credentials.remember_me:
        # Longer expiration for remember me: 30 days for access, 90 days for refresh
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=timedelta(days=30)
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(days=90)
        )
    else:
        # Default expiration: 30 minutes for access, 7 days for refresh
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    token_data = verify_token(refresh_token, "refresh")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user information
    from app.crud.user import get_user_by_id
    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/verify-email")
def verify_email(verification: EmailVerification, db: Session = Depends(get_db)):
    """Verify user email with token"""
    verification_record = get_email_verification(db, verification.token)
    if not verification_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Mark user as verified
    user = verify_user_email(db, verification_record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark verification token as used
    mark_email_verification_used(db, verification.token)
    
    return {
        "message": "Email verified successfully",
        "redirect_url": "/signin?verified=true"
    }


@router.post("/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    """Resend email verification"""
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Create new verification token
    verification = create_email_verification(db, user.id)
    
    # Send verification email
    send_verification_email.delay(user.email, verification.token)
    
    return {"message": "Verification email sent"}


@router.post("/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset"""
    user = get_user_by_email(db, request.email)
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Create password reset token
    from app.crud.verification import create_password_reset
    from app.tasks.email import send_password_reset_email
    
    reset = create_password_reset(db, user.id)
    send_password_reset_email.delay(user.email, reset.token)
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
def reset_password(reset: PasswordReset, db: Session = Depends(get_db)):
    """Reset password with token"""
    from app.crud.verification import get_password_reset, mark_password_reset_used
    from app.crud.user import update_user
    from app.schemas.auth import UserUpdate
    
    reset_record = get_password_reset(db, reset.token)
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user_update = UserUpdate(password=reset.new_password)
    updated_user = update_user(db, reset_record.user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark reset token as used
    mark_password_reset_used(db, reset.token)
    
    return {"message": "Password reset successfully"}


@router.post("/logout")
def logout(current_user = Depends(get_current_user)):
    """Logout user (client should clear tokens)"""
    # In a more advanced implementation, you could blacklist the token
    # For now, we rely on client-side token removal
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    from app.core.security import verify_password, get_password_hash, validate_password_strength
    from app.crud.user import update_user
    from app.schemas.auth import UserUpdate
    
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_valid, message = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Update password
    user_update = UserUpdate(password=new_password)
    updated_user = update_user(db, current_user.id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return {"message": "Password changed successfully"}


class GoogleAuthRequest(BaseModel):
    credential: str


@router.post("/google", response_model=Token)
def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate user with Google OAuth"""
    try:
        print(f"Received Google credential: {request.credential[:50]}...")
        
        # Decode the Google JWT token manually (without verification for now)
        try:
            # Split the JWT token into parts
            parts = request.credential.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")
            
            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded_payload = base64.urlsafe_b64decode(payload)
            decoded_token = json.loads(decoded_payload)
            
            print(f"Decoded token: {decoded_token}")
        except Exception as decode_error:
            print(f"JWT decode error: {decode_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token format"
            )
        
        # Extract user information from the token
        google_id = decoded_token.get("sub")
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        given_name = decoded_token.get("given_name", "")
        family_name = decoded_token.get("family_name", "")
        
        print(f"Extracted - google_id: {google_id}, email: {email}")
        
        if not google_id or not email:
            print(f"Missing required fields - google_id: {google_id}, email: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token - missing required fields"
            )
        
        # Check if user exists by email
        user = get_user_by_email(db, email)
        
        if user:
            # User exists, update their Google ID if not set
            if not user.google_id:
                user.google_id = google_id
                db.commit()
                db.refresh(user)
        else:
            # Create new user
            user_data = UserCreate(
                email=email,
                full_name=name or f"{given_name} {family_name}".strip(),
                password="",  # No password for Google OAuth users
                google_id=google_id
            )
            user = create_user(db, user_data)
            # Mark as verified since Google already verified the email
            user.is_verified = True
            db.commit()
            db.refresh(user)
        
        # Update last login
        update_last_login(db, user)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
        
    except jwt.JWTError:
        print("Invalid Google token", jwt.JWTError)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token"
        )
    except Exception as e:
        print(f"Google OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )

