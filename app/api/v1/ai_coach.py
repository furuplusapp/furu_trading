from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict
from openai import OpenAI
import hashlib
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.config import settings
from app.core.redis import RedisCache, get_ai_response_cache_key
from app.core.rate_limiter import RateLimiter
from app.tasks.ai_processing import process_ai_request_async
from app.services.chart_analysis import chart_analysis_service
from typing import Optional

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
    from_cache: bool = False
    task_id: str = None
    chart_update: Optional[Dict] = None

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
    Chat with AI Trading Assistant with Redis caching and rate limiting
    """
    try:
        # Check rate limiting (10 requests per minute)
        is_allowed, rate_info = RateLimiter.check_rate_limit(
            user_id=current_user.id,
            endpoint="ai_chat",
            limit=10,
            window_seconds=60
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {rate_info['reset_time']}"
            )
        
        # Check daily query limit using Redis (without incrementing yet)
        query_info = RateLimiter.get_daily_queries_info(
            user_id=current_user.id,
            plan=current_user.plan
        )
        
        if query_info['used'] >= query_info['daily_limit']:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily query limit reached ({query_info['daily_limit']} queries per day). Upgrade to Pro for unlimited access."
            )
        
        # Analyze the latest message for chart updates (using rule-based analysis to avoid extra API calls)
        latest_message = request.messages[-1].content if request.messages else ""
        chart_analysis = chart_analysis_service.analyze_query(latest_message)
        
        # Create messages hash for caching
        messages_str = str([{"role": msg.role, "content": msg.content} for msg in request.messages])
        messages_hash = hashlib.md5(messages_str.encode()).hexdigest()
        
        # Check cache first
        cache_key = get_ai_response_cache_key(current_user.id, messages_hash)
        cached_response = RedisCache.get(cache_key)
        
        if cached_response:
            # For cached responses, we don't increment the daily query count
            return ChatResponse(
                reply=cached_response['reply'],
                daily_queries_used=query_info['used'],
                daily_queries_limit=query_info['daily_limit'],
                from_cache=True,
                chart_update=chart_analysis if chart_analysis['needs_chart_update'] else None
            )
        
        # Process AI request asynchronously
        task = process_ai_request_async.delay(
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            user_id=current_user.id,
            plan=current_user.plan
        )
        
        # Wait for task completion (with timeout)
        try:
            result = task.get(timeout=30)  # 30 second timeout
            
            # Only increment daily query count if this is not a cached response
            if not result.get('from_cache', False):
                # Increment daily query count after successful AI processing
                is_allowed, updated_query_info = RateLimiter.check_daily_queries(
                    user_id=current_user.id,
                    plan=current_user.plan
                )
                query_info = updated_query_info
            
            return ChatResponse(
                reply=result['reply'],
                daily_queries_used=query_info['used'],
                daily_queries_limit=query_info['daily_limit'],
                from_cache=result.get('from_cache', False),
                task_id=result.get('task_id'),
                chart_update=chart_analysis if chart_analysis['needs_chart_update'] else None
            )
        except Exception as task_error:
            # Fallback to synchronous processing if Celery fails
            print(f"Celery task failed, falling back to sync: {task_error}")
            
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
                model="gpt-5-nano",
                messages=messages,
            )
            
            ai_reply = response.choices[0].message.content
            
            # Cache the response
            RedisCache.set(cache_key, {'reply': ai_reply}, expire=3600)
            
            # Increment daily query count after successful AI processing
            is_allowed, updated_query_info = RateLimiter.check_daily_queries(
                user_id=current_user.id,
                plan=current_user.plan
            )
            
            return ChatResponse(
                reply=ai_reply,
                daily_queries_used=updated_query_info['used'],
                daily_queries_limit=updated_query_info['daily_limit'],
                from_cache=False,
                chart_update=chart_analysis if chart_analysis['needs_chart_update'] else None
            )
        
    except HTTPException:
        raise
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
    Get current daily query count for the user using Redis (without incrementing)
    """
    try:
        # Get daily query count from Redis without incrementing
        query_info = RateLimiter.get_daily_queries_info(
            user_id=current_user.id,
            plan=current_user.plan
        )
        
        return QueryCountResponse(
            daily_queries_used=query_info['used'],
            daily_queries_limit=query_info['daily_limit']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
