import hashlib
from typing import List, Dict, Any
from openai import OpenAI
from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.redis import RedisCache, get_ai_response_cache_key

# OpenAI config
client = OpenAI(api_key=settings.openai_api_key)

@celery_app.task(bind=True)
def process_ai_request_async(self, messages: List[Dict[str, str]], user_id: int, plan: str):
    """
    Process AI request asynchronously
    """
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'status': 'Processing AI request...'})
        
        # Create messages hash for caching
        messages_str = str(messages)
        messages_hash = hashlib.md5(messages_str.encode()).hexdigest()
        
        # Check cache first
        cache_key = get_ai_response_cache_key(user_id, messages_hash)
        cached_response = RedisCache.get(cache_key)
        
        if cached_response:
            self.update_state(state='SUCCESS', meta={'status': 'Retrieved from cache'})
            return {
                'reply': cached_response['reply'],
                'from_cache': True,
                'task_id': self.request.id
            }
        
        # Prepare messages for OpenAI
        openai_messages = []
        
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
        openai_messages.append(system_message)
        
        # Add conversation history
        for msg in messages:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini-search-preview",
            messages=openai_messages,
        )
        
        ai_reply = response.choices[0].message.content
        
        # Cache the response for 1 hour
        RedisCache.set(cache_key, {'reply': ai_reply}, expire=3600)
        
        self.update_state(state='SUCCESS', meta={'status': 'AI processing completed'})
        
        return {
            'reply': ai_reply,
            'from_cache': False,
            'task_id': self.request.id
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'status': f'Error: {str(e)}'})
        raise e

@celery_app.task
def cleanup_expired_cache():
    """
    Clean up expired cache entries (run daily)
    """
    try:
        # This would typically be handled by Redis TTL, but we can add custom cleanup logic here
        print("Cache cleanup task completed")
        return {"status": "success", "message": "Cache cleanup completed"}
    except Exception as e:
        print(f"Cache cleanup error: {e}")
        raise e

@celery_app.task
def update_user_analytics(user_id: int, action: str, metadata: Dict[str, Any] = None):
    """
    Update user analytics in background
    """
    try:
        # Store analytics data
        analytics_key = f"analytics:{user_id}:{action}"
        RedisCache.set(analytics_key, {
            'user_id': user_id,
            'action': action,
            'metadata': metadata or {},
            'timestamp': RedisCache.get('current_timestamp') or 'unknown'
        }, expire=86400)  # 24 hours
        
        return {"status": "success", "message": "Analytics updated"}
    except Exception as e:
        print(f"Analytics update error: {e}")
        raise e
