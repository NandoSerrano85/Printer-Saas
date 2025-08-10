# services/common/cache.py
import redis
import json
import hashlib
from functools import wraps
from typing import Any, Optional, Callable
import pickle

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=False)

class TenantCache:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.key_prefix = f"tenant:{tenant_id}"
    
    def cache_key(self, key: str) -> str:
        """Generate tenant-scoped cache key"""
        return f"{self.key_prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        cache_key = self.cache_key(key)
        data = redis_client.get(cache_key)
        if data:
            return pickle.loads(data)
        return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> None:
        """Set cached value with expiration"""
        cache_key = self.cache_key(key)
        redis_client.setex(cache_key, expire, pickle.dumps(value))
    
    def delete(self, key: str) -> None:
        """Delete cached value"""
        cache_key = self.cache_key(key)
        redis_client.delete(cache_key)
    
    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern"""
        pattern_key = self.cache_key(pattern)
        keys = redis_client.keys(pattern_key)
        if keys:
            redis_client.delete(*keys)

def cache_tenant_data(expire: int = 3600, key_suffix: str = None):
    """Decorator for caching tenant-specific data"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(tenant_id: str, *args, **kwargs):
            cache = TenantCache(tenant_id)
            
            # Generate cache key from function name and parameters
            if key_suffix:
                cache_key = f"{func.__name__}:{key_suffix}"
            else:
                # Create hash of parameters for unique key
                params_hash = hashlib.md5(
                    json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True).encode()
                ).hexdigest()[:8]
                cache_key = f"{func.__name__}:{params_hash}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(tenant_id, *args, **kwargs)
            cache.set(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator

# Usage examples
@cache_tenant_data(expire=1800, key_suffix="analytics")
async def get_tenant_analytics(tenant_id: str, date_range: str) -> Dict[str, Any]:
    """Cached analytics data"""
    # Expensive analytics computation here
    pass

@cache_tenant_data(expire=300)  # 5 minutes for frequently changing data
async def get_etsy_listings(tenant_id: str, page: int = 1) -> Dict[str, Any]:
    """Cached Etsy listings with pagination"""
    # API call to Etsy
    pass