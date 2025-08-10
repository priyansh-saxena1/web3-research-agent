import time
from typing import Any, Optional, Dict
from src.config import config

class CacheManager:
    def __init__(self, default_ttl: Optional[int] = None):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl or config.CACHE_TTL
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry["expires_at"]:
            del self.cache[key]
            return None
        
        return entry["data"]
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        expires_at = time.time() + (ttl or self.default_ttl)
        self.cache[key] = {
            "data": data,
            "expires_at": expires_at
        }
    
    def delete(self, key: str) -> bool:
        return self.cache.pop(key, None) is not None
    
    def clear(self) -> None:
        self.cache.clear()
    
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

cache_manager = CacheManager()
