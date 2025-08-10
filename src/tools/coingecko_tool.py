from typing import Dict, Any, Optional
from pydantic import BaseModel, PrivateAttr
from src.tools.base_tool import BaseWeb3Tool, Web3ToolInput
from src.utils.config import config

class CoinGeckoTool(BaseWeb3Tool):
    name: str = "coingecko_data"
    description: str = """Get cryptocurrency price, volume, market cap and trend data from CoinGecko.
    Useful for: price analysis, market rankings, volume trends, price changes.
    Input: cryptocurrency name/symbol (bitcoin, ethereum, BTC, ETH) or market query."""
    args_schema: type[BaseModel] = Web3ToolInput
    
    _base_url: str = PrivateAttr(default="https://api.coingecko.com/api/v3")
    _symbol_map: Dict[str, str] = PrivateAttr(default_factory=lambda: {
        "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "ada": "cardano",
        "dot": "polkadot", "bnb": "binancecoin", "usdc": "usd-coin", 
        "usdt": "tether", "xrp": "ripple", "avax": "avalanche-2",
        "link": "chainlink", "matic": "matic-network", "uni": "uniswap"
    })
    
    def __init__(self):
        super().__init__()
    
    async def _arun(self, query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        try:
            filters = filters or {}
            
            if filters.get("type") == "trending":
                return await self._get_trending()
            elif filters.get("type") == "market_overview":
                return await self._get_market_overview()
            elif filters.get("type") == "price_history":
                return await self._get_price_history(query, filters.get("days", 30))
            else:
                return await self._get_coin_data(query)
                
        except Exception as e:
            return f"CoinGecko error: {str(e)}"
    async def _get_trending(self) -> str:
        data = await self.make_request(f"{self._base_url}/search/trending")
        data = await self.make_request(f"{self.base_url}/search/trending")
        
        trending = data.get("coins", [])[:5]
        result = "🔥 **Trending Cryptocurrencies:**\n\n"
        
        for i, coin in enumerate(trending, 1):
            item = coin.get("item", {})
            name = item.get("name", "Unknown")
            symbol = item.get("symbol", "").upper()
            rank = item.get("market_cap_rank", "N/A")
            result += f"{i}. **{name} ({symbol})** - Rank #{rank}\n"
        
        return result
    
    async def _get_market_overview(self) -> str:
        data = await self.make_request(f"{self._base_url}/coins/markets", params)10, "page": 1}
        data = await self.make_request(f"{self.base_url}/coins/markets", params)
        
        result = "📊 **Top Cryptocurrencies by Market Cap:**\n\n"
        
        for coin in data[:10]:
            name = coin.get("name", "Unknown")
            symbol = coin.get("symbol", "").upper()
            price = coin.get("current_price", 0)
            change = coin.get("price_change_percentage_24h", 0)
            mcap = coin.get("market_cap", 0)
            
            emoji = "📈" if change >= 0 else "📉"
            result += f"{emoji} **{name} ({symbol})**: ${price:,.4f} ({change:+.2f}%) | MCap: ${mcap/1e9:.2f}B\n"
        
        return result
    
        coin_id = self._symbol_map.get(query.lower(), query.lower())
        coin_id = self.symbol_map.get(query.lower(), query.lower())
        
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
        data = await self.make_request(f"{self._base_url}/simple/price", params)
        data = await self.make_request(f"{self.base_url}/simple/price", params)
        
        if coin_id not in data:
            return f"No data found for {query}"
        
        coin_data = data[coin_id]
        price = coin_data.get("usd", 0)
        change = coin_data.get("usd_24h_change", 0)
        volume = coin_data.get("usd_24h_vol", 0)
        mcap = coin_data.get("usd_market_cap", 0)
        
        emoji = "📈" if change >= 0 else "📉"
        
        result = f"💰 **{query.upper()} Market Data:**\n\n"
        result += f"{emoji} **Price**: ${price:,.4f}\n"
        result += f"📊 **24h Change**: {change:+.2f}%\n"
        result += f"📈 **24h Volume**: ${volume:,.0f}\n"
        result += f"🏦 **Market Cap**: ${mcap:,.0f}\n"
        
        return result
    
        coin_id = self._symbol_map.get(symbol.lower(), symbol.lower())
        
        params = {"vs_currency": "usd", "days": days}
        data = await self.make_request(f"{self._base_url}/coins/{coin_id}/market_chart", params)
        data = await self.make_request(f"{self.base_url}/coins/{coin_id}/market_chart", params)
        
        return {
            "symbol": symbol.upper(),
            "prices": data.get("prices", []),
            "volumes": data.get("total_volumes", []),
            "market_caps": data.get("market_caps", [])
        }
