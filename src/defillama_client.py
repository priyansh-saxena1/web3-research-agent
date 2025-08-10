import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from src.config import config

class DeFiLlamaClient:
    def __init__(self):
        self.base_url = "https://api.llama.fi"
        self.session = None
        self.rate_limiter = None
    
    async def get_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        session = await self.get_session()
        
        for attempt in range(3):
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise Exception(f"API error: {response.status}")
            except Exception as e:
                if attempt == 2:
                    raise e
                await asyncio.sleep(1)
    
    async def get_protocols(self) -> List[Dict[str, Any]]:
        return await self._make_request("protocols")
    
    async def get_protocol_data(self, protocol: str) -> Dict[str, Any]:
        return await self._make_request(f"protocol/{protocol}")
    
    async def get_tvl_data(self) -> Dict[str, Any]:
        return await self._make_request("v2/historicalChainTvl")
    
    async def get_chain_tvl(self, chain: str) -> Dict[str, Any]:
        return await self._make_request(f"v2/historicalChainTvl/{chain}")
    
    async def get_yields(self) -> List[Dict[str, Any]]:
        return await self._make_request("pools")
    
    async def get_bridges(self) -> List[Dict[str, Any]]:
        return await self._make_request("bridges")
    
    async def get_dex_volume(self) -> Dict[str, Any]:
        return await self._make_request("overview/dexs")
    
    async def close(self):
        if self.session:
            await self.session.close()

defillama_client = DeFiLlamaClient()