from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from openai import OpenAI
from datetime import date
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter()

# OpenAI config
client = OpenAI(api_key=settings.openai_api_key)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    plan: str

class ChatResponse(BaseModel):
    reply: str
    daily_queries_used: int
    daily_queries_limit: int

class QueryCountResponse(BaseModel):
    daily_queries_used: int
    daily_queries_limit: int

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai_coach(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with AI Trading Assistant
    """
    try:
        today = date.today()
        
        # Reset daily queries if it's a new day
        if current_user.last_query_date != today:
            current_user.daily_queries_used = 0
            current_user.last_query_date = today
        
        # Check if user has reached query limit for free plan
        if current_user.plan == "free":
            daily_limit = 5
            if current_user.daily_queries_used >= daily_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily query limit reached ({daily_limit} queries per day). Upgrade to Pro for unlimited access."
                )
        else:
            daily_limit = 999999  # Unlimited for paid plans
        
        # Prepare messages for OpenAI
        messages = []
        
        # Add system message for trading context
        system_message = {
            "role": "system",
            "content": """You are an expert AI Trading Assistant specializing in financial markets, trading strategies, risk management, and portfolio optimization. 

RESPONSE STYLE:
- Keep responses SHORT and CONCISE (2-4 sentences maximum)
- Provide direct, actionable answers
- Only give detailed explanations when user specifically asks for "detailed analysis", "explain more", or "tell me more"
- Focus on key points and actionable insights

Your expertise includes:
- Technical analysis (charts, indicators, patterns)
- Fundamental analysis (earnings, economic data, market sentiment)
- Risk management and position sizing
- Portfolio diversification strategies
- Options trading strategies
- Forex, stocks, crypto, and commodities analysis
- Backtesting and strategy development

IMPORTANT: 
- Respond in plain text only. No markdown formatting, headers (##), bullet points (-), or special formatting
- Write in a conversational, professional tone
- Be brief unless user requests detailed information

Remember: This is for educational purposes. Always advise users to do their own research and consider their risk tolerance."""
        }
        messages.append(system_message)
        
        # Add conversation history
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini-search-preview",  # or "gpt-3.5-turbo" for cost efficiency
            messages=messages,
        )
        
        ai_reply = response.choices[0].message.content
        
        # Increment daily query count
        current_user.daily_queries_used += 1
        db.commit()
        
        return ChatResponse(
            reply=ai_reply,
            daily_queries_used=current_user.daily_queries_used,
            daily_queries_limit=daily_limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/query-count", response_model=QueryCountResponse)
async def get_daily_query_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current daily query count for the user
    """
    try:
        today = date.today()
        
        # Reset daily queries if it's a new day
        if current_user.last_query_date != today:
            current_user.daily_queries_used = 0
            current_user.last_query_date = today
            db.commit()
        
        # Set daily limit based on plan
        if current_user.plan == "free":
            daily_limit = 5
        else:
            daily_limit = 999999  # Unlimited for paid plans
        
        return QueryCountResponse(
            daily_queries_used=current_user.daily_queries_used,
            daily_queries_limit=daily_limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
