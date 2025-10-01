import redis
import json
from typing import Optional, Any
from app.core.config import settings

# Redis connection
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

class RedisCache:
    """Redis caching utility class"""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    @staticmethod
    def set(key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in Redis cache with expiration"""
        try:
            redis_client.setex(key, expire, json.dumps(value))
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from Redis cache"""
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    @staticmethod
    def exists(key: str) -> bool:
        """Check if key exists in Redis cache"""
        try:
            return redis_client.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    @staticmethod
    def increment(key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in Redis"""
        try:
            return redis_client.incrby(key, amount)
        except Exception as e:
            print(f"Redis increment error: {e}")
            return None
    
    @staticmethod
    def set_expire(key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        try:
            return redis_client.expire(key, seconds)
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False

# Cache key generators
def get_ai_response_cache_key(user_id: int, messages_hash: str) -> str:
    """Generate cache key for AI responses"""
    return f"ai_response:{user_id}:{messages_hash}"

def get_user_cache_key(user_id: int) -> str:
    """Generate cache key for user data"""
    return f"user:{user_id}"

def get_rate_limit_key(user_id: int, endpoint: str) -> str:
    """Generate cache key for rate limiting"""
    return f"rate_limit:{user_id}:{endpoint}"

def get_daily_queries_key(user_id: int) -> str:
    """Generate cache key for daily queries"""
    return f"daily_queries:{user_id}"
