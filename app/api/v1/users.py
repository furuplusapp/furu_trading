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
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information - always fresh from database"""
    try:
        # Always fetch fresh data from database to ensure accuracy
        # This is important for plan updates, profile changes, etc.
        fresh_user = get_user_by_id(db, current_user.id)
        
        if not fresh_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update cache with fresh data for other endpoints that might use it
        cache_key = get_user_cache_key(current_user.id)
        user_data = {
            "id": fresh_user.id,
            "email": fresh_user.email,
            "full_name": fresh_user.full_name,
            "is_active": fresh_user.is_active,
            "is_verified": fresh_user.is_verified,
            "plan": fresh_user.plan,
            "created_at": fresh_user.created_at.isoformat() if fresh_user.created_at else None,
            "last_login": fresh_user.last_login.isoformat() if fresh_user.last_login else None
        }
        RedisCache.set(cache_key, user_data, expire=300)  # Cache for 5 minutes
        
        return fresh_user
        
    except HTTPException:
        raise
    except Exception as e:
        # Fallback to token user data if database query fails
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
    
    # Invalidate user cache after plan update
    cache_key = get_user_cache_key(user_id)
    RedisCache.delete(cache_key)
    print(f"Cache invalidated for user {user_id} after plan update to {plan_data.plan}")
    
    return {"message": "Plan updated successfully", "user_id": user_id, "plan": plan_data.plan}