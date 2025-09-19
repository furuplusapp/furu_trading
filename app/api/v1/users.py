from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.user import get_user_by_id, update_user_plan, get_user_by_stripe_customer_id, update_user
from app.schemas.auth import UserResponse, UserUpdate
from app.api.dependencies import get_current_user
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
    """Get current user information"""
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