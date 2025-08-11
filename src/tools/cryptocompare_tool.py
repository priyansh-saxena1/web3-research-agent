from typing import Dict, Any, Optional
from pydantic import BaseModel, PrivateAttr
from src.tools.base_tool import BaseWeb3Tool, Web3ToolInput
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class CryptoCompareTool(BaseWeb3Tool):
    name: str = "cryptocompare_data"
    description: str = """Get cryptocurrency price, volume, and market data from CryptoCompare API.
    Useful for: real-time prices, historical data, market analysis, volume tracking.
    Input: cryptocurrency symbol or query (e.g., BTC, ETH, price analysis)."""
    args_schema: type[BaseModel] = Web3ToolInput
    
    _base_url: str = PrivateAttr(default="https://min-api.cryptocompare.com/data")
    
    def __init__(self):
        super().__init__()
        # Store API key as instance variable instead of using Pydantic field
        self._api_key = config.CRYPTOCOMPARE_API_KEY
    
    async def _arun(self, query: str, filters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """Get crypto data from CryptoCompare API"""
        try:
            filters = filters or {}
            query_lower = query.lower()
            
            # Extract cryptocurrency symbols
            common_symbols = {
                "bitcoin": "BTC", "btc": "BTC",
                "ethereum": "ETH", "eth": "ETH", 
                "solana": "SOL", "sol": "SOL",
                "cardano": "ADA", "ada": "ADA",
                "polygon": "MATIC", "matic": "MATIC",
                "avalanche": "AVAX", "avax": "AVAX",
                "chainlink": "LINK", "link": "LINK",
                "uniswap": "UNI", "uni": "UNI",
                "polkadot": "DOT", "dot": "DOT",
                "binance": "BNB", "bnb": "BNB"
            }
            
            # Find symbol in query
            symbol = None
            for key, value in common_symbols.items():
                if key in query_lower:
                    symbol = value
                    break
            
            if not symbol:
                # Try to extract uppercase words as potential symbols
                words = query.upper().split()
                potential_symbols = [w for w in words if w.isalpha() and len(w) <= 5]
                symbol = potential_symbols[0] if potential_symbols else "BTC"
            
            # Determine data type needed
            if any(word in query_lower for word in ["price", "cost", "value", "current"]):
                return await self._get_current_price(symbol)
            elif any(word in query_lower for word in ["history", "historical", "trend", "chart"]):
                return await self._get_historical_data(symbol)
            elif any(word in query_lower for word in ["volume", "trading"]):
                return await self._get_volume_data(symbol)
            else:
                # Default to current price + basic stats
                return await self._get_current_price(symbol)
                
        except Exception as e:
            logger.error(f"CryptoCompare error: {e}")
            return f"⚠️ CryptoCompare data temporarily unavailable: {str(e)}"
    
    async def _get_current_price(self, symbol: str) -> str:
        """Get current price and basic stats"""
        try:
            # Current price endpoint
            params = {
                "fsym": symbol,
                "tsyms": "USD,EUR,BTC",
                "extraParams": "Web3ResearchAgent"
            }
            
            if self._api_key:
                params["api_key"] = self._api_key
            
            price_data = await self.make_request(f"{self._base_url}/price", params=params)
            
            if not price_data:
                return f"❌ No price data available for {symbol}"
            
            # Get additional stats
            stats_params = {
                "fsym": symbol,
                "tsym": "USD",
                "extraParams": "Web3ResearchAgent"
            }
            
            if self._api_key:
                stats_params["api_key"] = self._api_key
            
            stats_data = await self.make_request(f"{self._base_url}/pricemultifull", params=stats_params)
            
            # Format response
            usd_price = price_data.get("USD", 0)
            eur_price = price_data.get("EUR", 0)
            btc_price = price_data.get("BTC", 0)
            
            result = f"💰 **{symbol} Current Price** (CryptoCompare):\n\n"
            result += f"🇺🇸 **USD**: ${usd_price:,.2f}\n"
            
            if eur_price > 0:
                result += f"🇪🇺 **EUR**: €{eur_price:,.2f}\n"
            if btc_price > 0:
                result += f"₿ **BTC**: {btc_price:.8f}\n"
            
            # Add stats if available
            if stats_data and "RAW" in stats_data:
                raw_data = stats_data["RAW"].get(symbol, {}).get("USD", {})
                
                if raw_data:
                    change_24h = raw_data.get("CHANGEPCT24HOUR", 0)
                    volume_24h = raw_data.get("VOLUME24HOUR", 0)
                    market_cap = raw_data.get("MKTCAP", 0)
                    
                    emoji = "📈" if change_24h >= 0 else "📉"
                    result += f"\n📊 **24h Change**: {change_24h:+.2f}% {emoji}\n"
                    
                    if volume_24h > 0:
                        result += f"📈 **24h Volume**: ${volume_24h:,.0f}\n"
                    
                    if market_cap > 0:
                        result += f"🏦 **Market Cap**: ${market_cap:,.0f}\n"
            
            result += f"\n🕒 *Real-time data from CryptoCompare*"
            return result
            
        except Exception as e:
            logger.error(f"Price data error: {e}")
            return f"⚠️ Unable to fetch {symbol} price data"
    
    async def _get_historical_data(self, symbol: str, days: int = 30) -> str:
        """Get historical price data"""
        try:
            params = {
                "fsym": symbol,
                "tsym": "USD", 
                "limit": min(days, 365),
                "extraParams": "Web3ResearchAgent"
            }
            
            if self._api_key:
                params["api_key"] = self._api_key
            
            hist_data = await self.make_request(f"{self._base_url}/histoday", params=params)
            
            if not hist_data or "Data" not in hist_data:
                return f"❌ No historical data available for {symbol}"
            
            data_points = hist_data["Data"]
            if not data_points:
                return f"❌ No historical data points for {symbol}"
            
            # Get first and last prices
            first_price = data_points[0].get("close", 0)
            last_price = data_points[-1].get("close", 0)
            
            # Calculate performance
            if first_price > 0:
                performance = ((last_price - first_price) / first_price) * 100
                performance_emoji = "📈" if performance >= 0 else "📉"
            else:
                performance = 0
                performance_emoji = "➡️"
            
            # Find highest and lowest
            high_price = max([p.get("high", 0) for p in data_points])
            low_price = min([p.get("low", 0) for p in data_points if p.get("low", 0) > 0])
            
            result = f"📊 **{symbol} Historical Analysis** ({days} days):\n\n"
            result += f"💲 **Starting Price**: ${first_price:,.2f}\n"
            result += f"💲 **Current Price**: ${last_price:,.2f}\n"
            result += f"📊 **Performance**: {performance:+.2f}% {performance_emoji}\n\n"
            
            result += f"🔝 **Period High**: ${high_price:,.2f}\n"
            result += f"🔻 **Period Low**: ${low_price:,.2f}\n"
            
            # Calculate volatility (simplified)
            price_changes = []
            for i in range(1, len(data_points)):
                prev_close = data_points[i-1].get("close", 0)
                curr_close = data_points[i].get("close", 0)
                if prev_close > 0:
                    change = abs((curr_close - prev_close) / prev_close) * 100
                    price_changes.append(change)
            
            if price_changes:
                avg_volatility = sum(price_changes) / len(price_changes)
                result += f"📈 **Avg Daily Volatility**: {avg_volatility:.2f}%\n"
            
            result += f"\n🕒 *Data from CryptoCompare*"
            return result
            
        except Exception as e:
            logger.error(f"Historical data error: {e}")
            return f"⚠️ Unable to fetch historical data for {symbol}"
    
    async def _get_volume_data(self, symbol: str) -> str:
        """Get volume and trading data"""
        try:
            params = {
                "fsym": symbol,
                "tsym": "USD",
                "extraParams": "Web3ResearchAgent"
            }
            
            if self._api_key:
                params["api_key"] = self._api_key
            
            volume_data = await self.make_request(f"{self._base_url}/pricemultifull", params=params)
            
            if not volume_data or "RAW" not in volume_data:
                return f"❌ No volume data available for {symbol}"
            
            raw_data = volume_data["RAW"].get(symbol, {}).get("USD", {})
            
            if not raw_data:
                return f"❌ No trading data found for {symbol}"
            
            volume_24h = raw_data.get("VOLUME24HOUR", 0)
            volume_24h_to = raw_data.get("VOLUME24HOURTO", 0)
            total_volume = raw_data.get("TOTALVOLUME24H", 0)
            
            result = f"📈 **{symbol} Trading Volume**:\n\n"
            result += f"📊 **24h Volume**: {volume_24h:,.0f} {symbol}\n"
            result += f"💰 **24h Volume (USD)**: ${volume_24h_to:,.0f}\n"
            
            if total_volume > 0:
                result += f"🌐 **Total 24h Volume**: ${total_volume:,.0f}\n"
            
            # Additional trading info
            open_price = raw_data.get("OPEN24HOUR", 0)
            high_price = raw_data.get("HIGH24HOUR", 0)
            low_price = raw_data.get("LOW24HOUR", 0)
            
            if open_price > 0:
                result += f"\n📊 **24h Open**: ${open_price:,.2f}\n"
                result += f"🔝 **24h High**: ${high_price:,.2f}\n"
                result += f"🔻 **24h Low**: ${low_price:,.2f}\n"
            
            result += f"\n🕒 *Trading data from CryptoCompare*"
            return result
            
        except Exception as e:
            logger.error(f"Volume data error: {e}")
            return f"⚠️ Unable to fetch volume data for {symbol}"
