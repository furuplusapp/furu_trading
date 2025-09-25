from fastapi import APIRouter
from app.api.v1 import auth, users, stripe, webhooks, ai_coach

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stripe.router, prefix="/stripe", tags=["stripe"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(ai_coach.router, prefix="/ai-coach", tags=["ai-coach"])