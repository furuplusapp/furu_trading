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
    chart_state: Optional[Dict] = None  # Current chart configuration for state preservation

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
        
        # Get current chart state from request for state preservation and context
        current_chart_state = request.chart_state
        
        # Debug logging - show current state
        if current_chart_state:
            print(f"[Chart State] User {current_user.id} current state: {current_chart_state}")
        
        # Analyze the latest message for chart updates (using AI for intelligent extraction)
        latest_message = request.messages[-1].content if request.messages else ""
        chart_analysis = chart_analysis_service.analyze_query_with_ai(latest_message, current_chart_state)
        
        # Add current chart context to the AI messages for context-aware responses
        chart_context = ""
        if current_chart_state:
            symbol = current_chart_state.get('symbol', 'Unknown')
            interval = current_chart_state.get('interval', 'D')
            studies = current_chart_state.get('studies', [])
            
            # Convert interval code to readable format
            interval_map = {'1': '1m', '5': '5m', '15': '15m', '30': '30m', '60': '1h', '240': '4h', 'D': 'daily', 'W': 'weekly', 'M': 'monthly', '3M': '3-month', '6M': '6-month', '12M': 'yearly'}
            interval_readable = interval_map.get(interval, interval)
            
            # Convert studies to readable format
            studies_readable = []
            if studies:
                study_map = {'STD;RSI': 'RSI', 'STD;MACD': 'MACD', 'STD;BB': 'Bollinger Bands', 'STD;SMA': 'SMA', 'STD;EMA': 'EMA', 'STD;ADX': 'ADX', 'STD;MFI': 'MFI', 'STD;MOM': 'MOM', 'STD;PPO': 'PPO', 'STD;PVO': 'PVO', 'STD;ROC': 'ROC', 'STD;RVI': 'RVI', 'STD;SAR': 'SAR', 'STD;TRIX': 'TRIX', 'STD;VWAP': 'VWAP', 'STD;WMA': 'WMA', 'STD;BB': 'Bollinger Bands', 'STD;DEMA': 'DEMA', 'STD;TEMA': 'TEMA', 'STD;VIDYA': 'VIDYA', 'STD;VWMA': 'VWMA'}
                studies_readable = [study_map.get(s, s) for s in studies]
            
            chart_context = f"\n\nCURRENT CHART CONTEXT (User is viewing):\n- Symbol: {symbol}\n- Timeframe: {interval_readable}\n- Indicators: {', '.join(studies_readable) if studies_readable else 'None'}\n\nIMPORTANT: When user asks about 'current chart', 'this chart', or 'what I'm seeing', refer to the above chart context."
        
        # Normalize and validate chart config intervals
        if chart_analysis.get('needs_chart_update'):
            chart_config = chart_analysis.get('chart_config', {})
            
            # Fix interval format if AI returned wrong format
            interval = chart_config.get('interval', 'D')
            interval_fix_map = {
                '1Y': '12M',  # Fix yearly
                'Y': '12M',   # Fix yearly
                '1M': 'M',    # Fix monthly
            }
            if interval in interval_fix_map:
                chart_config['interval'] = interval_fix_map[interval]
                chart_analysis['chart_config']['interval'] = interval_fix_map[interval]
                print(f"[Chart Update] Fixed interval: {interval} → {interval_fix_map[interval]}")
            
            print(f"[Chart Update] User {current_user.id} new config: {chart_analysis.get('chart_config')}")
        
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
        
        # Prepare messages with chart context
        messages_for_ai = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Add chart context to the system message or last user message
        if chart_context and messages_for_ai:
            # Append chart context to the last user message
            messages_for_ai[-1]["content"] += chart_context
            print(f"[Chart Context] Added context to AI: {chart_context[:100]}...")
        
        # Process AI request asynchronously
        task = process_ai_request_async.delay(
            messages=messages_for_ai,
            user_id=current_user.id,
            plan=current_user.plan
        )
        
        # Wait for task completion (with timeout)
        try:
            result = task.get(timeout=30)  # 30 second timeout
            
            # Validate result structure
            if not isinstance(result, dict) or 'reply' not in result:
                raise ValueError(f"Invalid Celery task result structure: {result}")
            
            # Only increment daily query count if this is not a cached response
            if not result.get('from_cache', False):
                # Increment daily query count after successful AI processing
                is_allowed, updated_query_info = RateLimiter.check_daily_queries(
                    user_id=current_user.id,
                    plan=current_user.plan
                )
                # Update query_info with new counts
                query_info.update(updated_query_info)
            
            print(f"[AI Coach] User {current_user.id}: Celery task completed successfully. From cache: {result.get('from_cache', False)}. Daily queries: {query_info['used']}/{query_info['daily_limit']}")
            
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
            
            # Add conversation history with chart context
            for i, msg in enumerate(request.messages):
                content = msg.content
                # Add chart context to the last user message
                if i == len(request.messages) - 1 and msg.role == "user" and chart_context:
                    content += chart_context
                messages.append({
                    "role": msg.role,
                    "content": content
                })
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini-search-preview",
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
            
            print(f"[AI Coach] User {current_user.id}: Sync fallback completed. Daily queries: {updated_query_info['used']}/{updated_query_info['daily_limit']}")
            
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
