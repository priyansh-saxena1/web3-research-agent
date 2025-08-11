from typing import Dict, Any, Optional
from pydantic import BaseModel, PrivateAttr
from src.tools.base_tool import BaseWeb3Tool, Web3ToolInput
from src.utils.logger import get_logger
import aiohttp
import json

logger = get_logger(__name__)

class DeFiLlamaTool(BaseWeb3Tool):
    name: str = "defillama_data"
    description: str = """Get real DeFi protocol data, TVL, and yields from DeFiLlama API.
    Useful for: DeFi analysis, protocol rankings, TVL trends, chain analysis.
    Input: protocol name, chain name, or general DeFi query."""
    args_schema: type[BaseModel] = Web3ToolInput
    
    _base_url: str = PrivateAttr(default="https://api.llama.fi")
    
    def __init__(self):
        super().__init__()
    
    async def make_request(self, url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Make HTTP request to DeFiLlama API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ DeFiLlama API call successful: {url}")
                        return data
                    else:
                        logger.error(f"❌ DeFiLlama API error: {response.status} for {url}")
                        return None
        except Exception as e:
            logger.error(f"❌ DeFiLlama API request failed: {e}")
            return None
    
    async def _arun(self, query: str, filters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        try:
            filters = filters or {}
            query_lower = query.lower()
            
            # Route based on query type
            if "protocol" in query_lower and any(name in query_lower for name in ["uniswap", "aave", "compound", "curve"]):
                return await self._get_protocol_data(query)
            elif any(word in query_lower for word in ["chain", "ethereum", "polygon", "avalanche", "bsc"]):
                return await self._get_chain_tvl(query)
            elif "tvl" in query_lower or "total value locked" in query_lower:
                return await self._get_tvl_overview()
            elif "top" in query_lower or "ranking" in query_lower:
                return await self._get_top_protocols()
            else:
                return await self._search_protocols(query)
                
        except Exception as e:
            logger.error(f"DeFiLlama error: {e}")
            return f"⚠️ DeFiLlama service temporarily unavailable: {str(e)}"
    
    async def _get_top_protocols(self) -> str:
        """Get top protocols using /protocols endpoint"""
        try:
            data = await self.make_request(f"{self._base_url}/protocols")
            
            if not data or not isinstance(data, list):
                return "⚠️ DeFi protocol data temporarily unavailable"
            
            # Sort by TVL and take top 10
            top_protocols = sorted([p for p in data if p.get("tvl") is not None and p.get("tvl", 0) > 0], 
                                 key=lambda x: x.get("tvl", 0), reverse=True)[:10]
            
            if not top_protocols:
                return "⚠️ No valid protocol data available"
            
            result = "🏦 **Top DeFi Protocols by TVL:**\n\n"
            
            for i, protocol in enumerate(top_protocols, 1):
                name = protocol.get("name", "Unknown")
                tvl = protocol.get("tvl", 0)
                change_1d = protocol.get("change_1d", 0)
                chain = protocol.get("chain", "Multi-chain")
                
                emoji = "📈" if change_1d >= 0 else "📉"
                tvl_formatted = f"${tvl/1e9:.2f}B" if tvl >= 1e9 else f"${tvl/1e6:.1f}M"
                change_formatted = f"({change_1d:+.2f}%)" if change_1d is not None else "(N/A)"
                
                result += f"{i}. **{name}** ({chain}): {tvl_formatted} TVL {emoji} {change_formatted}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Top protocols error: {e}")
            return "⚠️ DeFi protocol data temporarily unavailable"

    async def _get_protocol_data(self, protocol_name: str) -> str:
        """Get specific protocol data using /protocol/{protocol} endpoint"""
        try:
            # First get all protocols to find the slug
            protocols = await self.make_request(f"{self._base_url}/protocols")
            if not protocols:
                return f"❌ Cannot fetch protocols list"
            
            # Find matching protocol
            matching_protocol = None
            for p in protocols:
                if protocol_name.lower() in p.get("name", "").lower():
                    matching_protocol = p
                    break
            
            if not matching_protocol:
                return f"❌ Protocol '{protocol_name}' not found"
            
            # Get detailed protocol data
            protocol_slug = matching_protocol.get("slug", protocol_name.lower())
            detailed_data = await self.make_request(f"{self._base_url}/protocol/{protocol_slug}")
            
            if detailed_data:
                # Use detailed data if available
                name = detailed_data.get("name", matching_protocol.get("name"))
                tvl = detailed_data.get("tvl", matching_protocol.get("tvl", 0))
                change_1d = detailed_data.get("change_1d", matching_protocol.get("change_1d", 0))
                change_7d = detailed_data.get("change_7d", matching_protocol.get("change_7d", 0))
                chains = detailed_data.get("chains", [matching_protocol.get("chain", "Unknown")])
                category = detailed_data.get("category", matching_protocol.get("category", "Unknown"))
                description = detailed_data.get("description", "No description available")
            else:
                # Fallback to basic protocol data
                name = matching_protocol.get("name", "Unknown")
                tvl = matching_protocol.get("tvl", 0)
                change_1d = matching_protocol.get("change_1d", 0)
                change_7d = matching_protocol.get("change_7d", 0)
                chains = [matching_protocol.get("chain", "Unknown")]
                category = matching_protocol.get("category", "Unknown")
                description = "No description available"
            
            result = f"🏛️ **{name} Protocol Analysis:**\n\n"
            result += f"📝 **Description**: {description[:200]}{'...' if len(description) > 200 else ''}\n\n"
            result += f"💰 **Current TVL**: ${tvl/1e9:.2f}B\n"
            result += f"📊 **24h Change**: {change_1d:+.2f}%\n"
            result += f"📈 **7d Change**: {change_7d:+.2f}%\n"
            result += f"⛓️ **Chains**: {', '.join(chains) if isinstance(chains, list) else str(chains)}\n"
            result += f"🏷️ **Category**: {category}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Protocol data error: {e}")
            return f"⚠️ Error fetching data for {protocol_name}: {str(e)}"
    
    async def _get_tvl_overview(self) -> str:
        """Get TVL overview using /protocols and /v2/chains endpoints"""
        try:
            # Get protocols and chains data
            protocols_data = await self.make_request(f"{self._base_url}/protocols")
            chains_data = await self.make_request(f"{self._base_url}/v2/chains")
            
            if not protocols_data:
                return "⚠️ TVL overview data unavailable"
            
            # Calculate total TVL
            total_tvl = sum(p.get("tvl", 0) for p in protocols_data if p.get("tvl") is not None and p.get("tvl", 0) > 0)
            
            result = "🌐 **DeFi TVL Overview:**\n\n"
            result += f"💰 **Total DeFi TVL**: ${total_tvl/1e9:.2f}B\n\n"
            
            # Add chain data if available
            if chains_data and isinstance(chains_data, list):
                top_chains = sorted([c for c in chains_data if c.get("tvl") is not None and c.get("tvl", 0) > 0], 
                                  key=lambda x: x.get("tvl", 0), reverse=True)[:5]
                
                result += "**Top Chains by TVL:**\n"
                for i, chain in enumerate(top_chains, 1):
                    name = chain.get("name", "Unknown")
                    tvl = chain.get("tvl", 0)
                    result += f"{i}. **{name}**: ${tvl/1e9:.2f}B\n"
            
            # Add top protocol categories
            categories = {}
            for protocol in protocols_data:
                if protocol.get("tvl") is not None and protocol.get("tvl", 0) > 0:
                    category = protocol.get("category", "Other")
                    categories[category] = categories.get(category, 0) + protocol.get("tvl", 0)
            
            if categories:
                result += "\n**Top Categories by TVL:**\n"
                sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
                for i, (category, tvl) in enumerate(sorted_categories, 1):
                    result += f"{i}. **{category}**: ${tvl/1e9:.2f}B\n"
            
            return result
            
        except Exception as e:
            logger.error(f"TVL overview error: {e}")
            return await self._get_top_protocols()

    async def _get_chain_tvl(self, chain_query: str) -> str:
        """Get chain TVL data using /v2/historicalChainTvl/{chain} endpoint"""
        try:
            # Map common chain names
            chain_mapping = {
                "ethereum": "Ethereum",
                "eth": "Ethereum", 
                "polygon": "Polygon",
                "matic": "Polygon",
                "bsc": "BSC",
                "binance": "BSC",
                "avalanche": "Avalanche",
                "avax": "Avalanche",
                "arbitrum": "Arbitrum",
                "optimism": "Optimism",
                "fantom": "Fantom",
                "solana": "Solana",
                "sol": "Solana"
            }
            
            # Extract chain name from query
            chain_name = None
            for key, value in chain_mapping.items():
                if key in chain_query.lower():
                    chain_name = value
                    break
            
            if not chain_name:
                # Try to get all chains first
                chains_data = await self.make_request(f"{self._base_url}/v2/chains")
                if chains_data:
                    result = "⛓️ **Available Chains:**\n\n"
                    sorted_chains = sorted([c for c in chains_data if c.get("tvl", 0) > 0], 
                                         key=lambda x: x.get("tvl", 0), reverse=True)[:10]
                    for i, chain in enumerate(sorted_chains, 1):
                        name = chain.get("name", "Unknown")
                        tvl = chain.get("tvl", 0)
                        result += f"{i}. **{name}**: ${tvl/1e9:.2f}B TVL\n"
                    return result
                else:
                    return f"❌ Chain '{chain_query}' not recognized. Try: ethereum, polygon, bsc, avalanche, etc."
            
            # Get historical TVL for the chain
            historical_data = await self.make_request(f"{self._base_url}/v2/historicalChainTvl/{chain_name}")
            
            if not historical_data:
                return f"❌ No data available for {chain_name}"
            
            # Get current TVL (last entry)
            current_tvl = historical_data[-1]["tvl"] if historical_data else 0
            
            result = f"⛓️ **{chain_name} Chain Analysis:**\n\n"
            result += f"💰 **Current TVL**: ${current_tvl/1e9:.2f}B\n"
            
            # Calculate changes if we have enough data
            if len(historical_data) >= 2:
                prev_tvl = historical_data[-2]["tvl"]
                daily_change = ((current_tvl - prev_tvl) / prev_tvl) * 100 if prev_tvl > 0 else 0
                emoji = "📈" if daily_change >= 0 else "📉"
                result += f"� **24h Change**: {daily_change:+.2f}% {emoji}\n"
            
            if len(historical_data) >= 7:
                week_ago_tvl = historical_data[-7]["tvl"]
                weekly_change = ((current_tvl - week_ago_tvl) / week_ago_tvl) * 100 if week_ago_tvl > 0 else 0
                emoji = "📈" if weekly_change >= 0 else "📉"
                result += f"📈 **7d Change**: {weekly_change:+.2f}% {emoji}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Chain TVL error: {e}")
            return f"⚠️ Error fetching chain data: {str(e)}"
    
    async def _search_protocols(self, query: str) -> str:
        """Search protocols by name"""
        try:
            protocols = await self.make_request(f"{self._base_url}/protocols")
            
            if not protocols:
                return "⚠️ No protocol data available"
            
            # Search for matching protocols
            query_lower = query.lower()
            matching = []
            
            for p in protocols:
                name = p.get("name", "").lower()
                category = p.get("category", "").lower() 
                
                if (query_lower in name or 
                    query_lower in category or
                    any(word in name for word in query_lower.split())):
                    matching.append(p)
            
            # Sort by TVL and limit results 
            matching = sorted([p for p in matching if p.get("tvl") is not None and p.get("tvl", 0) > 0], 
                            key=lambda x: x.get("tvl", 0), reverse=True)[:8]
            
            if not matching:
                return f"❌ No protocols found matching '{query}'"
            
            result = f"🔍 **Protocols matching '{query}':**\n\n"
            
            for i, protocol in enumerate(matching, 1):
                name = protocol.get("name", "Unknown")
                tvl = protocol.get("tvl", 0)
                chain = protocol.get("chain", "Multi-chain")
                category = protocol.get("category", "Unknown")
                change_1d = protocol.get("change_1d", 0)
                
                emoji = "📈" if change_1d >= 0 else "📉"
                tvl_formatted = f"${tvl/1e9:.2f}B" if tvl >= 1e9 else f"${tvl/1e6:.1f}M"
                
                result += f"{i}. **{name}** ({category})\n"
                result += f"   💰 {tvl_formatted} TVL on {chain} {emoji} {change_1d:+.1f}%\n\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Search protocols error: {e}")
            return f"⚠️ Search temporarily unavailable: {str(e)}"
