from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from typing import Optional
from datetime import datetime


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create new user"""
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_plan(db: Session, user_id: int, plan: str, stripe_customer_id: str = None, stripe_subscription_id: str = None) -> Optional[User]:
    """Update user's plan and Stripe information"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.plan = plan
    if stripe_customer_id:
        user.stripe_customer_id = stripe_customer_id
    if stripe_subscription_id:
        user.stripe_subscription_id = stripe_subscription_id
    
    db.commit()
    db.refresh(user)
    return user


def get_user_by_stripe_customer_id(db: Session, stripe_customer_id: str) -> Optional[User]:
    """Get user by Stripe customer ID"""
    return db.query(User).filter(User.stripe_customer_id == stripe_customer_id).first()


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_last_login(db: Session, user: User) -> User:
    """Update user's last login time"""
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def verify_user_email(db: Session, user_id: int) -> Optional[User]:
    """Mark user email as verified"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user