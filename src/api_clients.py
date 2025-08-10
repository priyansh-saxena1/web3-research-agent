import aiohttp
import asyncio
import time
from typing import Dict, Any, Optional, List
from src.config import config
import json

class RateLimiter:
    def __init__(self, delay: float):
        self.delay = delay
        self.last_call = 0
    
    async def acquire(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        self.last_call = time.time()

class CoinGeckoClient:
    def __init__(self):
        self.rate_limiter = RateLimiter(config.RATE_LIMIT_DELAY)
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self.rate_limiter.acquire()
        
        url = f"{config.COINGECKO_BASE_URL}/{endpoint}"
        if params is None:
            params = {}
        
        if config.COINGECKO_API_KEY:
            params["x_cg_demo_api_key"] = config.COINGECKO_API_KEY
        
        session = await self.get_session()
        
        for attempt in range(config.MAX_RETRIES):
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise Exception(f"API error: {response.status}")
            except asyncio.TimeoutError:
                if attempt == config.MAX_RETRIES - 1:
                    raise Exception("Request timeout")
                await asyncio.sleep(1)
        
        raise Exception("Max retries exceeded")
    
    async def get_price(self, coin_ids: str, vs_currencies: str = "usd") -> Dict[str, Any]:
        params = {
            "ids": coin_ids,
            "vs_currencies": vs_currencies,
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
        return await self._make_request("simple/price", params)
    
    async def get_trending(self) -> Dict[str, Any]:
        return await self._make_request("search/trending")
    
    async def get_global_data(self) -> Dict[str, Any]:
        return await self._make_request("global")
    
    async def get_coin_data(self, coin_id: str) -> Dict[str, Any]:
        params = {"localization": "false", "tickers": "false", "community_data": "false"}
        return await self._make_request(f"coins/{coin_id}", params)
    
    async def get_market_data(self, vs_currency: str = "usd", per_page: int = 10) -> Dict[str, Any]:
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "false"
        }
        return await self._make_request("coins/markets", params)
    
    async def get_price_history(self, coin_id: str, days: int = 7) -> Dict[str, Any]:
        params = {"vs_currency": "usd", "days": days}
        return await self._make_request(f"coins/{coin_id}/market_chart", params)
    
    async def close(self):
        if self.session:
            await self.session.close()

class CryptoCompareClient:
    def __init__(self):
        self.rate_limiter = RateLimiter(config.RATE_LIMIT_DELAY)
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self.rate_limiter.acquire()
        
        url = f"{config.CRYPTOCOMPARE_BASE_URL}/{endpoint}"
        if params is None:
            params = {}
        
        if config.CRYPTOCOMPARE_API_KEY:
            params["api_key"] = config.CRYPTOCOMPARE_API_KEY
        
        session = await self.get_session()
        
        for attempt in range(config.MAX_RETRIES):
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("Response") == "Error":
                            raise Exception(data.get("Message", "API error"))
                        return data
                    elif response.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise Exception(f"API error: {response.status}")
            except asyncio.TimeoutError:
                if attempt == config.MAX_RETRIES - 1:
                    raise Exception("Request timeout")
                await asyncio.sleep(1)
        
        raise Exception("Max retries exceeded")
    
    async def get_price_multi(self, fsyms: str, tsyms: str = "USD") -> Dict[str, Any]:
        params = {"fsyms": fsyms, "tsyms": tsyms}
        return await self._make_request("pricemulti", params)
    
    async def get_social_data(self, coin_symbol: str) -> Dict[str, Any]:
        params = {"coinSymbol": coin_symbol}
        return await self._make_request("social/coin/latest", params)
    
    async def get_news(self, categories: str = "blockchain") -> Dict[str, Any]:
        params = {"categories": categories}
        return await self._make_request("news/", params)
    
    async def close(self):
        if self.session:
            await self.session.close()

coingecko_client = CoinGeckoClient()
cryptocompare_client = CryptoCompareClient()
