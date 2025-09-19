from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.crud.user import get_user_by_id, update_user_plan
from app.services.stripe_service import create_customer, create_checkout_session, create_portal_session
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


@router.get("/config")
async def get_stripe_config():
    """Get Stripe configuration for frontend"""
    return {
        "publishable_key": settings.stripe_publishable_key,
        "api_version": "2025-08-27.basil"
    }


class CreateCheckoutRequest(BaseModel):
    priceId: str
    userId: int
    planName: str


class CreatePortalRequest(BaseModel):
    customerId: str


@router.post("/create-checkout-session")
async def create_checkout_session_endpoint(
    request: CreateCheckoutRequest,
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session"""
    try:
        # Get user
        user = get_user_by_id(db, request.userId)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Create or get Stripe customer
        if not user.stripe_customer_id:
            customer_id = await create_customer(user)
            # Update user with customer ID
            update_user_plan(
                db=db,
                user_id=user.id,
                plan=user.plan,
                stripe_customer_id=customer_id
            )
        else:
            customer_id = user.stripe_customer_id

        # Create checkout session
        session = await create_checkout_session(
            customer_id=customer_id,
            price_id=request.priceId,
            user_id=request.userId,
            plan_name=request.planName
        )

        return {
            "sessionId": session.id,
            "url": session.url
        }

    except Exception as e:
        print(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/create-portal-session")
async def create_portal_session_endpoint(
    request: CreatePortalRequest,
    db: Session = Depends(get_db)
):
    """Create a Stripe customer portal session"""
    try:
        session = await create_portal_session(request.customerId)
        return {"url": session.url}

    except Exception as e:
        print(f"Error creating portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )