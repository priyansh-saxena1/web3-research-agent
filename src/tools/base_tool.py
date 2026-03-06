from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from langchain_community.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr, field_validator
import asyncio
import aiohttp
import hashlib
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import get_logger
from src.utils.cache_manager import cache_manager

logger = get_logger(__name__)

class Web3ToolInput(BaseModel):
    query: str = Field(description="Search query or parameter")
    filters: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="Additional filters (dict) or filter type (string)")

    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # Convert string filter to dict format
            return {"type": v}
        if isinstance(v, dict):
            return v
        return None

class BaseWeb3Tool(BaseTool, ABC):
    name: str = "base_web3_tool"
    description: str = "Base Web3 tool"
    args_schema: type[BaseModel] = Web3ToolInput
    
    _session: Optional[aiohttp.ClientSession] = PrivateAttr(default=None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._session = None
    
    async def get_session(self):
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        # Create cache key
        cache_key = self._create_cache_key(url, params or {})
        
        # Check cache first
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for {url}")
            return cached_result
        
        logger.debug(f"Cache miss for {url}")
        session = await self.get_session()
        
        try:
            async with session.get(url, params=params or {}) as response:
                if response.status == 200:
                    result = await response.json()
                    # Cache successful responses for 5 minutes
                    cache_manager.set(cache_key, result, ttl=300)
                    return result
                elif response.status == 429:
                    await asyncio.sleep(2)
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
                else:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def _create_cache_key(self, url: str, params: Dict[str, Any]) -> str:
        """Create a unique cache key from URL and parameters"""
        key_data = f"{url}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _run(self, query: str, filters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        return asyncio.run(self._arun(query, filters))

    @abstractmethod
    async def _arun(self, query: str, filters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        pass

    async def cleanup(self):
        if self._session:
            await self._session.close()
            self._session = None
