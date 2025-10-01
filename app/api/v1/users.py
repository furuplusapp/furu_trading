from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.user import get_user_by_id, update_user_plan, get_user_by_stripe_customer_id, update_user
from app.schemas.auth import UserResponse, UserUpdate
from app.api.dependencies import get_current_user
from app.core.redis import RedisCache, get_user_cache_key
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class UpdatePlanRequest(BaseModel):
    plan: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(
    current_user = Depends(get_current_user)
):
    """Get current user information with Redis caching"""
    try:
        # Check cache first
        cache_key = get_user_cache_key(current_user.id)
        cached_user = RedisCache.get(cache_key)
        
        if cached_user:
            return UserResponse(**cached_user)
        
        # Cache user data for 15 minutes
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "plan": current_user.plan,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }
        
        RedisCache.set(cache_key, user_data, expire=900)  # 15 minutes
        
        return current_user
        
    except Exception as e:
        # Fallback to direct user data if caching fails
        return current_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    user_data: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user information"""
    print(f"Update user endpoint called for user_id: {user_id}")
    print(f"Current user ID: {current_user.id}")
    print(f"User data: {user_data}")
    
    # Only allow users to update their own profile
    if current_user.id != user_id:
        print(f"Authorization failed: current_user.id ({current_user.id}) != user_id ({user_id})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    try:
        # Update user data
        updated_user = update_user(
            db=db,
            user_id=user_id,
            user_update=user_data
        )
        
        if not updated_user:
            print(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        print(f"User updated successfully: {updated_user.id}")
        
        # Invalidate user cache
        cache_key = get_user_cache_key(user_id)
        RedisCache.delete(cache_key)
        
        return updated_user
        
    except Exception as e:
        print(f"Error updating user: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{user_id}/update-plan")
async def update_user_plan_endpoint(
    user_id: int,
    plan_data: UpdatePlanRequest,
    db: Session = Depends(get_db)
):
    """Update user's plan (used by webhooks)"""
    user = update_user_plan(
        db=db,
        user_id=user_id,
        plan=plan_data.plan,
        stripe_customer_id=plan_data.stripe_customer_id,
        stripe_subscription_id=plan_data.stripe_subscription_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Plan updated successfully", "user_id": user_id, "plan": plan_data.plan}