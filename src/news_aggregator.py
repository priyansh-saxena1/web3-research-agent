import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class CryptoNewsAggregator:
    def __init__(self):
        self.sources = {
            "cryptonews": "https://cryptonews-api.com/api/v1/category?section=general&items=10",
            "newsapi": "https://newsapi.org/v2/everything?q=cryptocurrency&sortBy=publishedAt&pageSize=10",
            "coindesk": "https://api.coindesk.com/v1/news/articles"
        }
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {"User-Agent": "Web3-Research-CoBot/1.0"}
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session
    
    async def get_crypto_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        news_items = []
        tasks = []
        
        for source, url in self.sources.items():
            tasks.append(self._fetch_news_from_source(source, url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if not isinstance(result, Exception) and result:
                news_items.extend(result[:5])
        
        news_items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return news_items[:limit]
    
    async def _fetch_news_from_source(self, source: str, url: str) -> List[Dict[str, Any]]:
        try:
            session = await self.get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_news_data(source, data)
                return []
        except Exception:
            return []
    
    def _parse_news_data(self, source: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        news_items = []
        current_time = datetime.now().timestamp()
        
        try:
            if source == "cryptonews" and "data" in data:
                for item in data["data"][:5]:
                    news_items.append({
                        "title": item.get("news_title", ""),
                        "summary": item.get("text", "")[:200] + "...",
                        "url": item.get("news_url", ""),
                        "source": "CryptoNews",
                        "timestamp": current_time
                    })
            
            elif source == "newsapi" and "articles" in data:
                for item in data["articles"][:5]:
                    news_items.append({
                        "title": item.get("title", ""),
                        "summary": item.get("description", "")[:200] + "...",
                        "url": item.get("url", ""),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        "timestamp": current_time
                    })
        except Exception:
            pass
        
        return news_items
    
    async def close(self):
        if self.session:
            await self.session.close()

news_aggregator = CryptoNewsAggregator()