import stripe
from app.core.config import settings
from app.models.user import User

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


async def create_customer(user: User) -> str:
    """Create a Stripe customer for a user"""
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={
            "userId": str(user.id),
        }
        )
        return customer.id
    except stripe.error.StripeError as e:
        print(f"Error creating Stripe customer: {e}")
        raise e


async def get_customer(customer_id: str):
    """Get a Stripe customer by ID"""
    try:
        return stripe.Customer.retrieve(customer_id)
    except stripe.error.StripeError as e:
        print(f"Error retrieving Stripe customer: {e}")
        raise e


async def create_subscription(customer_id: str, price_id: str, user_id: int):
    """Create a Stripe subscription"""
    try:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata={
                "userId": str(user_id),
            }
        )
        return subscription
    except stripe.error.StripeError as e:
        print(f"Error creating subscription: {e}")
        raise e


async def cancel_subscription(subscription_id: str):
    """Cancel a Stripe subscription"""
    try:
        return stripe.Subscription.delete(subscription_id)
    except stripe.error.StripeError as e:
        print(f"Error canceling subscription: {e}")
        raise e


async def get_subscription(subscription_id: str):
    """Get a Stripe subscription by ID"""
    try:
        return stripe.Subscription.retrieve(subscription_id)
    except stripe.error.StripeError as e:
        print(f"Error retrieving subscription: {e}")
        raise e


async def create_checkout_session(customer_id: str, price_id: str, user_id: int, plan_name: str):
    
    """Create a Stripe checkout session"""
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.cors_origins[0]}/dashboard?session_id={{CHECKOUT_SESSION_ID}}&upgrade=success",
            cancel_url=f"{settings.cors_origins[0]}/pricing?canceled=true",
            metadata={
                "userId": str(user_id),
                "planName": plan_name,
            }
        )
        return session
    except stripe.error.StripeError as e:
        print(f"Error creating checkout session: {e}")
        raise e


async def create_portal_session(customer_id: str):
    """Create a Stripe customer portal session"""
    try:
        session = stripe.billingPortal.Session.create(
            customer=customer_id,
            return_url=f"{settings.cors_origins[0]}/dashboard",
        )
        return session
    except stripe.error.StripeError as e:
        print(f"Error creating portal session: {e}")
        raise e