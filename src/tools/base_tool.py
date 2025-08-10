from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import get_logger

logger = get_logger(__name__)

class Web3ToolInput(BaseModel):
    query: str = Field(description="Search query or parameter")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")

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
        session = await self.get_session()
        try:
            async with session.get(url, params=params or {}) as response:
                if response.status == 200:
                    return await response.json()
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
    
    def _run(self, query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        return asyncio.run(self._arun(query, filters))
    
    @abstractmethod
    async def _arun(self, query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        pass

    async def cleanup(self):
        if self._session:
            await self._session.close()
        if self.session:
            await self.session.close()
