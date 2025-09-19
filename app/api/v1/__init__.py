from fastapi import APIRouter
from app.api.v1 import auth, users, stripe, webhooks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stripe.router, prefix="/stripe", tags=["stripe"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])