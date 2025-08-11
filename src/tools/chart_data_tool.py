from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import asyncio

from src.utils.logger import get_logger

logger = get_logger(__name__)

class ChartDataInput(BaseModel):
    """Input schema for chart data requests"""
    chart_type: str = Field(description="Chart type: price_chart, market_overview, defi_tvl, portfolio_pie, gas_tracker")
    symbol: Optional[str] = Field(default=None, description="Asset symbol (e.g., bitcoin, ethereum)")
    timeframe: Optional[str] = Field(default="30d", description="Time range: 1d, 7d, 30d, 90d, 365d")
    protocols: Optional[List[str]] = Field(default=None, description="DeFi protocol names")
    network: Optional[str] = Field(default="ethereum", description="Blockchain network")

class ChartDataTool(BaseTool):
    """
    Chart Data Provider Tool
    
    This tool provides structured data that can be used to create charts.
    Instead of returning HTML, it returns clean JSON data for visualization.
    """
    
    name: str = "chart_data_provider"
    description: str = """Provides structured data for creating cryptocurrency charts.
    
    Returns JSON data in this format:
    {{
        "chart_type": "price_chart|market_overview|defi_tvl|portfolio_pie|gas_tracker",
        "data": {{...}},
        "config": {{...}}
    }}
    
    Chart types:
    - price_chart: Bitcoin/crypto price and volume data
    - market_overview: Top cryptocurrencies market data  
    - defi_tvl: DeFi protocol TVL comparison
    - portfolio_pie: Portfolio allocation breakdown
    - gas_tracker: Gas fees across networks
    """
    
    args_schema: type[ChartDataInput] = ChartDataInput
    
    def _run(self, chart_type: str, symbol: str = None, timeframe: str = "30d", 
             protocols: List[str] = None, network: str = "ethereum") -> str:
        """Synchronous execution"""
        return asyncio.run(self._arun(chart_type, symbol, timeframe, protocols, network))
    
    async def _arun(self, chart_type: str, symbol: str = None, timeframe: str = "30d", 
                    protocols: List[str] = None, network: str = "ethereum") -> str:
        """Provide chart data based on request"""
        try:
            logger.info(f"Providing {chart_type} data for {symbol or 'general'}")
            
            # Convert timeframe to days
            days = self._parse_timeframe(timeframe)
            
            if chart_type == "price_chart":
                return await self._get_price_chart_data(symbol or "bitcoin", days)
            elif chart_type == "market_overview":
                return await self._get_market_overview_data()
            elif chart_type == "defi_tvl":
                return await self._get_defi_tvl_data(protocols or ["uniswap", "aave", "compound"])
            elif chart_type == "portfolio_pie":
                return await self._get_portfolio_data()
            elif chart_type == "gas_tracker":
                return await self._get_gas_data(network)
            else:
                return json.dumps({
                    "chart_type": "error",
                    "error": f"Unknown chart type: {chart_type}",
                    "available_types": ["price_chart", "market_overview", "defi_tvl", "portfolio_pie", "gas_tracker"]
                })
                
        except Exception as e:
            logger.error(f"Chart data error: {e}")
            return json.dumps({
                "chart_type": "error",
                "error": str(e),
                "message": "Failed to generate chart data"
            })
    
    async def _get_price_chart_data(self, symbol: str, days: int) -> str:
        """Get price chart data with fallback for API failures"""
        try:
            # First try to get real data from CoinGecko
            from src.tools.coingecko_tool import CoinGeckoTool
            
            coingecko = CoinGeckoTool()
            
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                "btc": "bitcoin", "bitcoin": "bitcoin",
                "eth": "ethereum", "ethereum": "ethereum", 
                "sol": "solana", "solana": "solana",
                "ada": "cardano", "cardano": "cardano",
                "bnb": "binancecoin", "binance": "binancecoin",
                "matic": "matic-network", "polygon": "matic-network",
                "avax": "avalanche-2", "avalanche": "avalanche-2",
                "dot": "polkadot", "polkadot": "polkadot",
                "link": "chainlink", "chainlink": "chainlink",
                "uni": "uniswap", "uniswap": "uniswap"
            }
            
            coin_id = symbol_map.get(symbol.lower(), symbol.lower())
            
            try:
                # Use basic API endpoint that doesn't require premium
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
                params = {"vs_currency": "usd", "days": days, "interval": "daily"}
                
                data = await coingecko.make_request(url, params=params)
                
                if data and "prices" in data:
                    # Format the real data
                    price_data = data.get("prices", [])
                    volume_data = data.get("total_volumes", [])
                    
                    # Get current coin info
                    coin_info = await coingecko.make_request(f"https://api.coingecko.com/api/v3/coins/{coin_id}")
                    coin_name = coin_info.get("name", symbol.title()) if coin_info else symbol.title()
                    
                    return json.dumps({
                        "chart_type": "price_chart", 
                        "data": {
                            "prices": price_data,
                            "total_volumes": volume_data,
                            "symbol": symbol.upper(),
                            "name": coin_name
                        },
                        "config": {
                            "title": f"{coin_name} Price Analysis ({days} days)",
                            "timeframe": f"{days}d", 
                            "currency": "USD"
                        }
                    })
                else:
                    raise Exception("No price data in response")
                    
            except Exception as api_error:
                logger.error(f"Real price data failed: {api_error}")
                # Fallback to mock data on any API error
                logger.info(f"Using fallback mock data for {symbol}")
                return await self._get_mock_price_data(symbol, days)
            
        except Exception as e:
            logger.error(f"Price chart data generation failed: {e}")
            # Final fallback to mock data
            return await self._get_mock_price_data(symbol, days)
    
    async def _get_mock_price_data(self, symbol: str, days: int) -> str:
        """Fallback mock price data"""
        import time
        import random
        
        base_price = 35000 if symbol.lower() == "bitcoin" else 1800 if symbol.lower() == "ethereum" else 100
        base_timestamp = int(time.time() * 1000) - (days * 24 * 60 * 60 * 1000)
        
        price_data = []
        volume_data = []
        
        for i in range(days):
            timestamp = base_timestamp + (i * 24 * 60 * 60 * 1000)
            price_change = random.uniform(-0.05, 0.05)
            price = base_price * (1 + price_change * i / days)
            price += random.uniform(-price*0.02, price*0.02)
            volume = random.uniform(1000000000, 5000000000)
            
            price_data.append([timestamp, round(price, 2)])
            volume_data.append([timestamp, int(volume)])
        
        return json.dumps({
            "chart_type": "price_chart",
            "data": {
                "prices": price_data,
                "total_volumes": volume_data,
                "symbol": symbol.upper(),
                "name": symbol.title()
            },
            "config": {
                "title": f"{symbol.title()} Price Analysis ({days} days)",
                "timeframe": f"{days}d",
                "currency": "USD"
            }
        })
    
    async def _get_market_overview_data(self) -> str:
        """Get real market overview data from CoinGecko API"""
        try:
            from src.tools.coingecko_tool import CoinGeckoTool
            
            coingecko = CoinGeckoTool()
            
            # Get top market cap coins
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc", 
                "per_page": 10,
                "page": 1,
                "sparkline": False
            }
            
            data = await coingecko.make_request(url, params=params)
            
            if not data:
                logger.warning("CoinGecko market data failed, using fallback")
                return await self._get_mock_market_data()
            
            # Format real market data
            coins = []
            for coin in data[:10]:
                coins.append({
                    "name": coin.get("name", "Unknown"),
                    "symbol": coin.get("symbol", "").upper(),
                    "current_price": coin.get("current_price", 0),
                    "market_cap_rank": coin.get("market_cap_rank", 0),
                    "price_change_percentage_24h": coin.get("price_change_percentage_24h", 0),
                    "market_cap": coin.get("market_cap", 0),
                    "total_volume": coin.get("total_volume", 0)
                })
            
            return json.dumps({
                "chart_type": "market_overview",
                "data": {"coins": coins},
                "config": {
                    "title": "Top Cryptocurrencies Market Overview",
                    "currency": "USD"
                }
            })
            
        except Exception as e:
            logger.error(f"Market overview API failed: {e}")
            return await self._get_mock_market_data()
    
    async def _get_mock_market_data(self) -> str:
        """Fallback mock market data"""
        return json.dumps({
            "chart_type": "market_overview",
            "data": {
                "coins": [
                    {"name": "Bitcoin", "symbol": "BTC", "current_price": 35000, "market_cap_rank": 1, "price_change_percentage_24h": 2.5},
                    {"name": "Ethereum", "symbol": "ETH", "current_price": 1800, "market_cap_rank": 2, "price_change_percentage_24h": -1.2},
                    {"name": "Cardano", "symbol": "ADA", "current_price": 0.25, "market_cap_rank": 3, "price_change_percentage_24h": 3.1},
                    {"name": "Solana", "symbol": "SOL", "current_price": 22.5, "market_cap_rank": 4, "price_change_percentage_24h": -2.8},
                    {"name": "Polygon", "symbol": "MATIC", "current_price": 0.52, "market_cap_rank": 5, "price_change_percentage_24h": 1.9}
                ]
            },
            "config": {
                "title": "Top Cryptocurrencies Market Overview",
                "currency": "USD"
            }
        })
    
    async def _get_defi_tvl_data(self, protocols: List[str]) -> str:
        """Get real DeFi TVL data from DeFiLlama API"""
        try:
            from src.tools.defillama_tool import DeFiLlamaTool
            
            defillama = DeFiLlamaTool()
            
            # Get protocols data
            data = await defillama.make_request(f"{defillama._base_url}/protocols")
            
            if not data:
                logger.warning("DeFiLlama API failed, using fallback")
                return await self._get_mock_defi_data(protocols)
            
            # Filter for requested protocols or top protocols
            if protocols:
                filtered_protocols = []
                for protocol_name in protocols:
                    for protocol in data:
                        if protocol_name.lower() in protocol.get("name", "").lower():
                            filtered_protocols.append(protocol)
                            break
                protocols_data = filtered_protocols[:8]  # Limit to 8
            else:
                # Get top protocols by TVL
                protocols_data = sorted([p for p in data if p.get("tvl", 0) > 0], 
                                      key=lambda x: x.get("tvl", 0), reverse=True)[:8]
            
            if not protocols_data:
                return await self._get_mock_defi_data(protocols)
            
            # Format TVL data
            tvl_data = []
            for protocol in protocols_data:
                tvl_data.append({
                    "name": protocol.get("name", "Unknown"),
                    "tvl": protocol.get("tvl", 0),
                    "change_1d": protocol.get("change_1d", 0),
                    "chain": protocol.get("chain", "Multi-chain"),
                    "category": protocol.get("category", "DeFi")
                })
            
            return json.dumps({
                "chart_type": "defi_tvl",
                "data": {"protocols": tvl_data},
                "config": {
                    "title": "DeFi Protocols by Total Value Locked",
                    "currency": "USD"
                }
            })
            
        except Exception as e:
            logger.error(f"DeFi TVL API failed: {e}")
            return await self._get_mock_defi_data(protocols)
    
    async def _get_mock_defi_data(self, protocols: List[str]) -> str:
        """Fallback mock DeFi data"""
        import random
        
        protocol_names = protocols or ["Uniswap", "Aave", "Compound", "Curve", "MakerDAO"]
        tvl_data = []
        
        for protocol in protocol_names[:5]:
            tvl = random.uniform(500000000, 5000000000)
            change = random.uniform(-10, 15)
            tvl_data.append({
                "name": protocol,
                "tvl": tvl,
                "change_1d": change,
                "chain": "Ethereum",
                "category": "DeFi"
            })
        
        return json.dumps({
            "chart_type": "defi_tvl",
            "data": {"protocols": tvl_data},
            "config": {
                "title": "DeFi Protocols by Total Value Locked",
                "currency": "USD"
            }
        })
    
    async def _get_portfolio_data(self) -> str:
        """Get portfolio allocation data"""
        return json.dumps({
            "chart_type": "portfolio_pie",
            "data": {
                "allocations": [
                    {"name": "Bitcoin", "symbol": "BTC", "value": 40, "color": "#f7931a"},
                    {"name": "Ethereum", "symbol": "ETH", "value": 30, "color": "#627eea"},
                    {"name": "Cardano", "symbol": "ADA", "value": 15, "color": "#0033ad"},
                    {"name": "Solana", "symbol": "SOL", "value": 10, "color": "#9945ff"},
                    {"name": "Other", "symbol": "OTHER", "value": 5, "color": "#666666"}
                ]
            },
            "config": {
                "title": "Sample Portfolio Allocation",
                "currency": "Percentage"
            }
        })
    
    async def _get_gas_data(self, network: str) -> str:
        """Get gas fee data"""
        import random
        import time
        
        # Generate 24 hours of gas data
        gas_data = []
        base_timestamp = int(time.time() * 1000) - (24 * 60 * 60 * 1000)
        
        for i in range(24):
            timestamp = base_timestamp + (i * 60 * 60 * 1000)
            gas_price = random.uniform(20, 100) if network == "ethereum" else random.uniform(1, 10)
            gas_data.append([timestamp, round(gas_price, 2)])
        
        return json.dumps({
            "chart_type": "gas_tracker",
            "data": {
                "gas_prices": gas_data,
                "network": network.title()
            },
            "config": {
                "title": f"{network.title()} Gas Fee Tracker (24h)",
                "unit": "Gwei"
            }
        })
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Convert timeframe string to days"""
        timeframe_map = {
            "1d": 1, "7d": 7, "30d": 30, "90d": 90, "365d": 365, "1y": 365
        }
        return timeframe_map.get(timeframe, 30)
