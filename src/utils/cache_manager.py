import time
from typing import Any, Optional, Dict
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class CacheManager:
    def __init__(self, default_ttl: Optional[int] = None):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl or config.CACHE_TTL
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        if time.time() > entry["expires_at"]:
            del self.cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return entry["data"]
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        try:
            expires_at = time.time() + (ttl or self.default_ttl)
            self.cache[key] = {
                "data": data,
                "expires_at": expires_at,
                "created_at": time.time()
            }
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")
    
    def delete(self, key: str) -> bool:
        return self.cache.pop(key, None) is not None
    
    def clear(self) -> None:
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def cleanup_expired(self) -> int:
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def size(self) -> int:
        return len(self.cache)
    
    def stats(self) -> Dict[str, Any]:
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": self.size(),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "expired_cleaned": self.cleanup_expired()
        }

cache_manager = CacheManager()
