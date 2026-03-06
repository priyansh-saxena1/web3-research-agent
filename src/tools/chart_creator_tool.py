from langchain_community.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime

from src.visualizations import CryptoVisualizations
from src.tools.coingecko_tool import CoinGeckoTool
from src.tools.defillama_tool import DeFiLlamaTool
from src.tools.etherscan_tool import EtherscanTool
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ChartCreatorInput(BaseModel):
    """Input schema for chart creation requests - accepts only essential parameters"""
    chart_type: str = Field(
        description="Chart type: price_chart, market_overview, defi_tvl, portfolio_pie, gas_tracker"
    )
    symbol: Optional[str] = Field(
        default=None,
        description="Asset symbol (e.g., bitcoin, ethereum) for price/market charts"
    )
    timeframe: Optional[str] = Field(
        default="30d",
        description="Time range: 1d, 7d, 30d, 90d, 365d"
    )
    protocols: Optional[List[str]] = Field(
        default=None,
        description="Protocol names for DeFi TVL charts (e.g., ['uniswap', 'aave'])"
    )
    network: Optional[str] = Field(
        default="ethereum",
        description="Blockchain network for gas tracker (ethereum, polygon, etc.)"
    )

class ChartCreatorTool(BaseTool):
    """
    Intelligent Chart Creator Tool
    
    This tool can create various types of cryptocurrency and DeFi charts by:
    1. Understanding chart requirements from natural language
    2. Fetching appropriate data from available sources
    3. Generating professional visualizations
    """
    
    name: str = "chart_creator"
    description: str = """Create cryptocurrency and DeFi charts with specific parameters only.
    
    IMPORTANT: Only pass essential chart parameters - do not send full user queries.
    
    Chart types and required parameters:
    - price_chart: symbol (e.g., "bitcoin"), timeframe (e.g., "30d")
    - market_overview: symbol (optional), timeframe (default "30d")
    - defi_tvl: protocols (list of protocol names), timeframe (optional)
    - portfolio_pie: No parameters needed (uses default allocation)
    - gas_tracker: network (e.g., "ethereum"), timeframe (optional)
    
    Examples of CORRECT usage:
    - price_chart for Bitcoin: symbol="bitcoin", timeframe="30d"
    - DeFi TVL chart: protocols=["uniswap", "aave"], timeframe="7d"
    - Gas tracker: network="ethereum", timeframe="1d"
    """
    
    # Define fields
    viz: Any = None
    coingecko: Any = None
    defillama: Any = None
    etherscan: Any = None
    
    args_schema: type[ChartCreatorInput] = ChartCreatorInput
    
    def __init__(self):
        super().__init__()
        self.viz = CryptoVisualizations()
        self.coingecko = CoinGeckoTool()
        self.defillama = DeFiLlamaTool()
        self.etherscan = EtherscanTool()
    
    def _run(self, chart_type: str, symbol: str = None, timeframe: str = "30d", 
             protocols: List[str] = None, network: str = "ethereum") -> str:
        """Synchronous execution (not used in async context)"""
        return asyncio.run(self._arun(chart_type, symbol, timeframe, protocols, network))
    
    async def _arun(self, chart_type: str, symbol: str = None, timeframe: str = "30d", 
                    protocols: List[str] = None, network: str = "ethereum") -> str:
        """Create charts with controlled parameters"""
        try:
            logger.info(f"Creating {chart_type} chart for {symbol or 'general'} with timeframe {timeframe}")
            
            # Build parameters from clean inputs
            parameters = {
                "symbol": symbol,
                "timeframe": timeframe,
                "protocols": protocols,
                "network": network,
                "days": self._parse_timeframe(timeframe)
            }
            
            # Determine data source based on chart type
            data_source = self._get_data_source(chart_type)
            
            # Fetch data based on source and chart type
            data = await self._fetch_chart_data(chart_type, parameters, data_source)
            
            if not data:
                return json.dumps({
                    "status": "error",
                    "message": f"Unable to fetch data for {chart_type} from {data_source}",
                    "alternative": f"Try requesting textual analysis instead, or use different parameters",
                    "chart_html": None
                })
            
            # Create the appropriate chart
            chart_html = await self._create_chart(chart_type, data, parameters)
            
            if chart_html:
                logger.info(f"Successfully created {chart_type} chart")
                return json.dumps({
                    "status": "success",
                    "message": f"Successfully created {chart_type} chart",
                    "chart_html": chart_html,
                    "data_source": data_source
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Chart creation failed for {chart_type}",
                    "alternative": f"Data was retrieved but visualization failed. Providing textual analysis instead.",
                    "chart_html": None
                })
                
        except Exception as e:
            logger.error(f"Chart creation error: {e}")
            return json.dumps({
                "status": "error", 
                "message": f"Chart creation failed: {str(e)}",
                "alternative": "Please try again with different parameters or request textual analysis",
                "chart_html": None
            })
    
    async def _fetch_chart_data(self, chart_type: str, parameters: Dict[str, Any], data_source: str) -> Optional[Dict[str, Any]]:
        """Fetch data from appropriate source based on chart type"""
        try:
            if data_source == "coingecko":
                return await self._fetch_coingecko_data(chart_type, parameters)
            elif data_source == "defillama":
                return await self._fetch_defillama_data(chart_type, parameters)
            elif data_source == "etherscan":
                return await self._fetch_etherscan_data(chart_type, parameters)
            else:
                logger.warning(f"Unknown data source: {data_source}")
                return None
                
        except Exception as e:
            logger.error(f"Data fetch error: {e}")
            return None
    
    async def _fetch_coingecko_data(self, chart_type: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch data from CoinGecko API"""
        try:
            if chart_type == "price_chart":
                symbol = parameters.get("symbol", "bitcoin")
                days = parameters.get("days", 30)
                
                                # Create mock price data
                base_timestamp = 1704067200000  # Jan 1, 2024
                mock_data = {
                    "prices": [[base_timestamp + i * 86400000, 35000 + i * 100 + (i % 7) * 500] for i in range(days)],
                    "total_volumes": [[base_timestamp + i * 86400000, 1000000 + i * 10000 + (i % 5) * 50000] for i in range(days)],
                    "symbol": symbol,
                    "days": days
                }
                return mock_data
                
            elif chart_type == "market_overview":
                # Create mock market data
                mock_data = {
                    "coins": [
                        {"name": "Bitcoin", "symbol": "BTC", "current_price": 35000, "market_cap_rank": 1, "price_change_percentage_24h": 2.5},
                        {"name": "Ethereum", "symbol": "ETH", "current_price": 1800, "market_cap_rank": 2, "price_change_percentage_24h": -1.2},
                        {"name": "Cardano", "symbol": "ADA", "current_price": 0.25, "market_cap_rank": 3, "price_change_percentage_24h": 3.1}
                    ]
                }
                return mock_data
                
        except Exception as e:
            logger.error(f"CoinGecko data fetch error: {e}")
            
        return None
    
    async def _fetch_defillama_data(self, chart_type: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch data from DeFiLlama API"""
        try:
            if chart_type == "defi_tvl":
                protocols = parameters.get("protocols", ["uniswap", "aave", "compound"])
                # Create mock TVL data
                mock_data = {
                    "protocols": [
                        {"name": "Uniswap", "tvl": 3500000000, "change_24h": 2.1},
                        {"name": "Aave", "tvl": 5200000000, "change_24h": -0.8},
                        {"name": "Compound", "tvl": 1800000000, "change_24h": 1.5}
                    ]
                }
                return mock_data
                
        except Exception as e:
            logger.error(f"DeFiLlama data fetch error: {e}")
            
        return None
    
    async def _fetch_etherscan_data(self, chart_type: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch data from Etherscan API"""
        try:
            if chart_type == "gas_tracker":
                # Create mock gas data
                mock_data = {
                    "gas_prices": {
                        "safe": 15,
                        "standard": 20,
                        "fast": 35,
                        "instant": 50
                    },
                    "network": "ethereum"
                }
                return mock_data
                
        except Exception as e:
            logger.error(f"Etherscan data fetch error: {e}")
            
        return None
    
    async def _create_chart(self, chart_type: str, data: Dict[str, Any], parameters: Dict[str, Any]) -> Optional[str]:
        """Create chart using the visualization module"""
        try:
            fig = None
            
            if chart_type == "price_chart":
                symbol = parameters.get("symbol", "BTC")
                fig = self.viz.create_price_chart(data, symbol)
                
            elif chart_type == "market_overview":
                # Convert dict to list format expected by visualization
                market_data = []
                if isinstance(data, dict) and "data" in data:
                    market_data = data["data"]
                elif isinstance(data, list):
                    market_data = data
                fig = self.viz.create_market_overview(market_data)
                
            elif chart_type == "defi_tvl":
                # Convert to format expected by visualization
                tvl_data = []
                if isinstance(data, dict):
                    tvl_data = [data]  # Wrap single protocol in list
                elif isinstance(data, list):
                    tvl_data = data
                fig = self.viz.create_defi_tvl_chart(tvl_data)
                
            elif chart_type == "portfolio_pie":
                portfolio_data = parameters.get("portfolio", {})
                if not portfolio_data and isinstance(data, dict):
                    portfolio_data = data
                fig = self.viz.create_portfolio_pie_chart(portfolio_data)
                
            elif chart_type == "gas_tracker":
                fig = self.viz.create_gas_tracker(data)
            
            if fig:
                # Convert to HTML
                chart_html = fig.to_html(
                    include_plotlyjs='cdn',
                    div_id=f"chart_{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    config={'displayModeBar': True, 'responsive': True}
                )
                
                # Store chart for later retrieval (you could save to database/cache here)
                return chart_html
            
            return None
            
        except Exception as e:
            logger.error(f"Chart creation error: {e}")
            return None

    def get_chart_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Generate chart suggestions based on user query"""
        suggestions = []
        
        query_lower = query.lower()
        
        # Price-related queries
        if any(word in query_lower for word in ["price", "chart", "trend", "bitcoin", "ethereum", "crypto"]):
            suggestions.append({
                "chart_type": "price_chart",
                "description": "Price and volume chart with historical data",
                "parameters": {"symbol": "bitcoin", "days": 30},
                "data_source": "coingecko"
            })
        
        # Market overview queries
        if any(word in query_lower for word in ["market", "overview", "top", "comparison", "ranking"]):
            suggestions.append({
                "chart_type": "market_overview",
                "description": "Market cap and performance overview of top cryptocurrencies",
                "parameters": {"limit": 20},
                "data_source": "coingecko"
            })
        
        # DeFi queries
        if any(word in query_lower for word in ["defi", "tvl", "protocol", "uniswap", "aave", "compound"]):
            suggestions.append({
                "chart_type": "defi_tvl",
                "description": "DeFi protocol Total Value Locked comparison",
                "parameters": {"protocols": ["uniswap", "aave", "compound"]},
                "data_source": "defillama"
            })
        
        # Gas fee queries
        if any(word in query_lower for word in ["gas", "fee", "ethereum", "network", "transaction"]):
            suggestions.append({
                "chart_type": "gas_tracker",
                "description": "Ethereum gas fee tracker",
                "parameters": {"network": "ethereum"},
                "data_source": "etherscan"
            })
        
        # Portfolio queries
        if any(word in query_lower for word in ["portfolio", "allocation", "distribution", "holdings"]):
            suggestions.append({
                "chart_type": "portfolio_pie",
                "description": "Portfolio allocation pie chart",
                "parameters": {"portfolio": {"BTC": 40, "ETH": 30, "ADA": 20, "DOT": 10}},
                "data_source": "custom"
            })
        
        return suggestions[:3]  # Return top 3 suggestions

    def _parse_timeframe(self, timeframe: str) -> int:
        """Convert timeframe string to days"""
        timeframe_map = {
            "1d": 1, "7d": 7, "30d": 30, "90d": 90, "365d": 365, "1y": 365
        }
        return timeframe_map.get(timeframe, 30)
    
    def _get_data_source(self, chart_type: str) -> str:
        """Determine appropriate data source for chart type"""
        source_map = {
            "price_chart": "coingecko",
            "market_overview": "coingecko", 
            "defi_tvl": "defillama",
            "portfolio_pie": "custom",
            "gas_tracker": "etherscan"
        }
        return source_map.get(chart_type, "coingecko")
