from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.user import update_user_plan
from app.core.config import settings
import stripe
import json

router = APIRouter()

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    try:
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                body, signature, settings.stripe_webhook_secret
            )
        except ValueError as e:
            print(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            print(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle the event
        if event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"], db)
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event["data"]["object"], db)
        elif event["type"] == "invoice.payment_succeeded":
            await handle_payment_succeeded(event["data"]["object"], db)
        elif event["type"] == "invoice.payment_failed":
            await handle_payment_failed(event["data"]["object"], db)
        elif event["type"] == "invoice.payment.paid":
            await handle_payment_paid(event["data"]["object"], db)
        else:
            print(f"Unhandled event type: {event['type']}")

        return {"received": True}

    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook handler failed")


async def handle_checkout_completed(session, db: Session):
    """Handle successful checkout"""
    print(f"Checkout completed for session: {session.get('id')}")
    print(f"Session metadata: {session.get('metadata')}")
    
    user_id = session.get("metadata", {}).get("userId")
    plan_name = session.get("metadata", {}).get("planName")

    print(f"Extracted user_id: {user_id}, plan_name: {plan_name}")

    if not user_id or not plan_name:
        print("Missing user ID or plan name in session metadata")
        raise ValueError("Missing user ID or plan name in session metadata")

    try:
        # Update user's plan in database
        user = update_user_plan(
            db=db,
            user_id=int(user_id),
            plan=plan_name.lower(),
            stripe_customer_id=session.get("customer"),
            stripe_subscription_id=session.get("subscription")
        )

        if user:
            print(f"User {user_id} successfully upgraded to {plan_name} plan")
            print(f"Updated user plan: {user.plan}")
        else:
            print(f"Failed to update user {user_id} plan - user not found")
            raise ValueError(f"User {user_id} not found")

    except Exception as e:
        print(f"Error updating user {user_id} plan: {e}")
        import traceback
        traceback.print_exc()
        raise e


async def handle_subscription_updated(subscription, db: Session):
    """Handle subscription updates"""
    user_id = subscription.get("metadata", {}).get("userId")

    if not user_id:
        print("Missing user ID in subscription metadata")
        return

    print(f"Subscription updated for user {user_id}: {subscription.get('status')}")


async def handle_subscription_deleted(subscription, db: Session):
    """Handle subscription cancellation"""
    user_id = subscription.get("metadata", {}).get("userId")

    if not user_id:
        print("Missing user ID in subscription metadata")
        raise ValueError("Missing user ID in subscription metadata")

    try:
        # Downgrade user to free plan
        user = update_user_plan(
            db=db,
            user_id=int(user_id),
            plan="free",
            stripe_subscription_id=None
        )

        if user:
            print(f"User {user_id} successfully downgraded to free plan")
        else:
            print(f"Failed to downgrade user {user_id} - user not found")
            raise ValueError(f"User {user_id} not found")

    except Exception as e:
        print(f"Error downgrading user {user_id}: {e}")
        raise e


async def handle_payment_succeeded(invoice, db: Session):
    """Handle successful payment"""
    subscription_id = invoice.get("subscription")

    if subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            user_id = subscription.get("metadata", {}).get("userId")

            if user_id:
                print(f"Payment succeeded for user {user_id}")
        except Exception as e:
            print(f"Error retrieving subscription {subscription_id}: {e}")


async def handle_payment_failed(invoice, db: Session):
    """Handle failed payment"""
    subscription_id = invoice.get("subscription")

    if subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            user_id = subscription.get("metadata", {}).get("userId")

            if user_id:
                print(f"Payment failed for user {user_id}")
        except Exception as e:
            print(f"Error retrieving subscription {subscription_id}: {e}")


async def handle_payment_paid(invoice, db: Session):
    """Handle successful payment (invoice.payment.paid)"""
    subscription_id = invoice.get("subscription")

    if subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            user_id = subscription.get("metadata", {}).get("userId")

            if user_id:
                print(f"Payment paid for user {user_id}")
        except Exception as e:
            print(f"Error retrieving subscription {subscription_id}: {e}")