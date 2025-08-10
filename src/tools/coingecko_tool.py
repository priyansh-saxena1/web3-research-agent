from typing import Dict, Any, Optional
from pydantic import BaseModel, PrivateAttr
from src.tools.base_tool import BaseWeb3Tool, Web3ToolInput
from src.utils.config import config
from src.utils.logger import get_logger
from src.utils.cache_manager import cache_manager

logger = get_logger(__name__)

class CoinGeckoTool(BaseWeb3Tool):
    name: str = "coingecko_data"
    description: str = """Get cryptocurrency price, volume, market cap and trend data from CoinGecko."""
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
        filters = filters or {}
        try:
            # Check cache first
            cache_key = f"coingecko_{filters.get('type', 'coin')}_{query}_{str(filters)}"
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for {cache_key}")
                return cached_result
            
            result = None
            t = filters.get("type")
            
            if t == "trending":
                result = await self._get_trending()
            elif t == "market_overview":
                result = await self._get_market_overview()
            elif t == "price_history":
                days = int(filters.get("days", 30))
                result = await self._get_price_history(query, days)
            else:
                result = await self._get_coin_data(query)
            
            # Cache successful results
            if result and not result.startswith("⚠️"):
                cache_manager.set(cache_key, result, ttl=300)
            
            return result
            
        except Exception as e:
            logger.error(f"CoinGecko error: {e}")
            return f"⚠️ CoinGecko service temporarily unavailable: {str(e)}"

    async def _get_trending(self) -> str:
        data = await self.make_request(f"{self._base_url}/search/trending")
        coins = data.get("coins", [])[:5]
        out = "🔥 **Trending Cryptocurrencies:**\n\n"
        for i, c in enumerate(coins, 1):
            item = c.get("item", {})
            out += f"{i}. **{item.get('name','?')} ({item.get('symbol','?').upper()})** – Rank #{item.get('market_cap_rank','?')}\n"
        return out

    async def _get_market_overview(self) -> str:
        try:
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 10,
                "page": 1
            }
            data = await self.make_request(f"{self._base_url}/coins/markets", params=params)
            
            if not data or not isinstance(data, list):
                return "⚠️ Market overview data temporarily unavailable"
            
            if len(data) == 0:
                return "❌ No market data available"
            
            result = "📊 **Top Cryptocurrencies by Market Cap:**\n\n"
            
            for coin in data[:10]:  # Ensure max 10
                try:
                    name = coin.get("name", "Unknown")
                    symbol = coin.get("symbol", "?").upper()
                    price = coin.get("current_price", 0)
                    change_24h = coin.get("price_change_percentage_24h", 0)
                    market_cap = coin.get("market_cap", 0)
                    
                    # Handle missing or invalid data
                    if price is None or price <= 0:
                        continue
                    
                    emoji = "📈" if change_24h >= 0 else "📉"
                    mcap_formatted = f"${market_cap/1e9:.2f}B" if market_cap > 0 else "N/A"
                    
                    result += f"{emoji} **{name} ({symbol})**: ${price:,.4f} ({change_24h:+.2f}%) | MCap: {mcap_formatted}\n"
                    
                except (TypeError, KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid coin data: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Market overview error: {e}")
            return "⚠️ Market overview temporarily unavailable"

    async def _get_coin_data(self, query: str) -> str:
        if not query or not query.strip():
            return "❌ Please provide a cryptocurrency symbol or name"
        
        coin_id = self._symbol_map.get(query.lower(), query.lower())
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
        
        try:
            data = await self.make_request(f"{self._base_url}/simple/price", params=params)
            
            if not data or coin_id not in data:
                # Try alternative search if direct lookup fails
                search_data = await self._search_coin(query)
                if search_data:
                    return search_data
                return f"❌ No data found for '{query}'. Try using full name or common symbols like BTC, ETH, SOL"
            
            coin_data = data[coin_id]
            
            # Validate required fields
            if "usd" not in coin_data:
                return f"❌ Price data unavailable for {query.upper()}"
            
            price = coin_data.get("usd", 0)
            change_24h = coin_data.get("usd_24h_change", 0)
            volume_24h = coin_data.get("usd_24h_vol", 0)
            market_cap = coin_data.get("usd_market_cap", 0)
            
            # Handle edge cases
            if price <= 0:
                return f"⚠️ {query.upper()} price data appears invalid"
            
            emoji = "📈" if change_24h >= 0 else "📉"
            
            result = f"💰 **{query.upper()} Market Data:**\n\n"
            result += f"{emoji} **Price**: ${price:,.4f}\n"
            result += f"📊 **24h Change**: {change_24h:+.2f}%\n"
            
            if volume_24h > 0:
                result += f"📈 **24h Volume**: ${volume_24h:,.0f}\n"
            else:
                result += f"📈 **24h Volume**: Data unavailable\n"
            
            if market_cap > 0:
                result += f"🏦 **Market Cap**: ${market_cap:,.0f}\n"
            else:
                result += f"🏦 **Market Cap**: Data unavailable\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching coin data for {query}: {e}")
            return f"⚠️ Unable to fetch data for {query.upper()}. Please try again later."
    
    async def _search_coin(self, query: str) -> Optional[str]:
        """Fallback search when direct ID lookup fails"""
        try:
            search_params = {"query": query}
            search_data = await self.make_request(f"{self._base_url}/search", params=search_params)
            
            coins = search_data.get("coins", [])
            if coins:
                coin = coins[0]  # Take first match
                coin_id = coin.get("id")
                if coin_id:
                    return await self._get_coin_data(coin_id)
            
            return None
        except Exception:
            return None

    async def _get_price_history(self, symbol: str, days: int) -> str:
        coin_id = self._symbol_map.get(symbol.lower(), symbol.lower())
        params = {"vs_currency": "usd", "days": days}
        data = await self.make_request(f"{self._base_url}/coins/{coin_id}/market_chart", params=params)
        # you can format this as you like; here’s a simple JSON dump
        return {
            "symbol": symbol.upper(),
            "prices": data.get("prices", []),
            "volumes": data.get("total_volumes", []),
            "market_caps": data.get("market_caps", [])
        }
