from typing import Optional
from datetime import datetime, timedelta
from app.core.redis import RedisCache, get_rate_limit_key, get_daily_queries_key

class RateLimiter:
    """Rate limiting utility using Redis"""
    
    @staticmethod
    def check_rate_limit(user_id: int, endpoint: str, limit: int, window_seconds: int) -> tuple[bool, dict]:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User ID
            endpoint: API endpoint name
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            tuple: (is_allowed, rate_info)
        """
        try:
            key = get_rate_limit_key(user_id, endpoint)
            current_time = datetime.now()
            window_start = current_time - timedelta(seconds=window_seconds)
            
            # Get current count
            current_count = RedisCache.get(key) or 0
            
            if current_count >= limit:
                return False, {
                    'allowed': False,
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': window_start + timedelta(seconds=window_seconds),
                    'current_count': current_count
                }
            
            # Increment counter
            new_count = RedisCache.increment(key)
            if new_count == 1:
                # Set expiration for first request
                RedisCache.set_expire(key, window_seconds)
            
            return True, {
                'allowed': True,
                'limit': limit,
                'remaining': limit - new_count,
                'reset_time': current_time + timedelta(seconds=window_seconds),
                'current_count': new_count
            }
            
        except Exception as e:
            print(f"Rate limit check error: {e}")
            # Allow request if Redis is down
            return True, {
                'allowed': True,
                'limit': limit,
                'remaining': limit - 1,
                'reset_time': datetime.now() + timedelta(seconds=window_seconds),
                'current_count': 1,
                'error': 'Rate limit check failed, allowing request'
            }
    
    @staticmethod
    def check_daily_queries(user_id: int, plan: str) -> tuple[bool, dict]:
        """
        Check daily query limit for AI chat
        
        Args:
            user_id: User ID
            plan: User's plan (free, pro, elite)
            
        Returns:
            tuple: (is_allowed, query_info)
        """
        try:
            # Set daily limits based on plan
            if plan == "free":
                daily_limit = 5
            elif plan == "pro":
                daily_limit = 100
            elif plan == "elite":
                daily_limit = 1000
            else:
                daily_limit = 5  # Default to free plan
            
            key = get_daily_queries_key(user_id)
            current_count = RedisCache.get(key) or 0
            
            if current_count >= daily_limit:
                return False, {
                    'allowed': False,
                    'daily_limit': daily_limit,
                    'used': current_count,
                    'remaining': 0,
                    'reset_time': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                }
            
            # Increment counter
            new_count = RedisCache.increment(key)
            if new_count == 1:
                # Set expiration to end of day
                now = datetime.now()
                end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                seconds_until_midnight = int((end_of_day - now).total_seconds())
                RedisCache.set_expire(key, seconds_until_midnight)
            
            return True, {
                'allowed': True,
                'daily_limit': daily_limit,
                'used': new_count,
                'remaining': daily_limit - new_count,
                'reset_time': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            }
            
        except Exception as e:
            print(f"Daily queries check error: {e}")
            # Allow request if Redis is down
            return True, {
                'allowed': True,
                'daily_limit': daily_limit,
                'used': 1,
                'remaining': daily_limit - 1,
                'reset_time': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
                'error': 'Daily queries check failed, allowing request'
            }
    
    @staticmethod
    def reset_daily_queries(user_id: int) -> bool:
        """Reset daily queries counter (for testing or admin use)"""
        try:
            key = get_daily_queries_key(user_id)
            return RedisCache.delete(key)
        except Exception as e:
            print(f"Reset daily queries error: {e}")
            return False
