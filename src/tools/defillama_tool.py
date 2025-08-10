from typing import Dict, Any, Optional
from pydantic import BaseModel, PrivateAttr
from src.tools.base_tool import BaseWeb3Tool, Web3ToolInput
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DeFiLlamaTool(BaseWeb3Tool):
    name: str = "defillama_data"
    description: str = """Get DeFi protocol data, TVL, and yields from DeFiLlama.
    Useful for: DeFi analysis, protocol rankings, TVL trends, yield farming data.
    Input: protocol name or general DeFi query."""
    args_schema: type[BaseModel] = Web3ToolInput
    
    _base_url: str = PrivateAttr(default="https://api.llama.fi")
    
    def __init__(self):
        super().__init__()
    
    async def _arun(self, query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        try:
            filters = filters or {}
            
            if filters.get("type") == "tvl_overview":
                return await self._get_tvl_overview()
            elif filters.get("type") == "protocol_data":
                return await self._get_protocol_data(query)
            elif query:
                return await self._search_protocols(query)
            else:
                return await self._get_top_protocols()
                
        except Exception as e:
            logger.error(f"DeFiLlama error: {e}")
            return f"⚠️ DeFiLlama service temporarily unavailable: {str(e)}"
    
    async def _get_top_protocols(self) -> str:
        try:
            data = await self.make_request(f"{self._base_url}/protocols")
            
            if not data or not isinstance(data, list):
                return "⚠️ DeFi protocol data temporarily unavailable"
            
            if len(data) == 0:
                return "❌ No DeFi protocols found"
            
            # Filter and validate protocols
            valid_protocols = []
            for protocol in data:
                try:
                    tvl = protocol.get("tvl", 0)
                    if tvl is not None and tvl > 0:
                        valid_protocols.append(protocol)
                except (TypeError, ValueError):
                    continue
            
            if not valid_protocols:
                return "⚠️ No valid protocol data available"
            
            # Sort by TVL and take top 10
            top_protocols = sorted(valid_protocols, key=lambda x: x.get("tvl", 0), reverse=True)[:10]
            
            result = "🏦 **Top DeFi Protocols by TVL:**\n\n"
            
            for i, protocol in enumerate(top_protocols, 1):
                try:
                    name = protocol.get("name", "Unknown")
                    tvl = protocol.get("tvl", 0)
                    change = protocol.get("change_1d", 0)
                    chain = protocol.get("chain", "Multi-chain")
                    
                    # Handle edge cases
                    if tvl <= 0:
                        continue
                    
                    emoji = "📈" if change >= 0 else "📉"
                    tvl_formatted = f"${tvl/1e9:.2f}B" if tvl >= 1e9 else f"${tvl/1e6:.1f}M"
                    change_formatted = f"({change:+.2f}%)" if change is not None else "(N/A)"
                    
                    result += f"{i}. **{name}** ({chain}): {tvl_formatted} TVL {emoji} {change_formatted}\n"
                    
                except (TypeError, KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid protocol data: {e}")
                    continue
            
            return result if len(result.split('\n')) > 3 else "⚠️ Unable to format protocol data properly"
            
        except Exception as e:
            logger.error(f"Top protocols error: {e}")
            return "⚠️ DeFi protocol data temporarily unavailable"
    
    async def _get_tvl_overview(self) -> str:
        try:
            protocols_data = await self.make_request(f"{self.base_url}/protocols")
            chains_data = await self.make_request(f"{self.base_url}/chains")
            
            if not protocols_data or not chains_data:
                return "TVL overview data unavailable"
            
            total_tvl = sum(p.get("tvl", 0) for p in protocols_data)
            top_chains = sorted(chains_data, key=lambda x: x.get("tvl", 0), reverse=True)[:5]
            
            result = "🌐 **DeFi TVL Overview:**\n\n"
            result += f"💰 **Total TVL**: ${total_tvl/1e9:.2f}B\n\n"
            result += "**Top Chains by TVL:**\n"
            
            for i, chain in enumerate(top_chains, 1):
                name = chain.get("name", "Unknown")
                tvl = chain.get("tvl", 0)
                result += f"{i}. **{name}**: ${tvl/1e9:.2f}B\n"
            
            return result
            
        except Exception:
            return await self._get_top_protocols()
    
    async def _get_protocol_data(self, protocol: str) -> str:
        protocols = await self.make_request(f"{self.base_url}/protocols")
        
        if not protocols:
            return f"No data available for {protocol}"
        
        matching_protocol = None
        for p in protocols:
            if protocol.lower() in p.get("name", "").lower():
                matching_protocol = p
                break
        
        if not matching_protocol:
            return f"Protocol '{protocol}' not found"
        
        name = matching_protocol.get("name", "Unknown")
        tvl = matching_protocol.get("tvl", 0)
        change_1d = matching_protocol.get("change_1d", 0)
        change_7d = matching_protocol.get("change_7d", 0)
        chain = matching_protocol.get("chain", "Multi-chain")
        category = matching_protocol.get("category", "Unknown")
        
        result = f"🏛️ **{name} Protocol Analysis:**\n\n"
        result += f"💰 **TVL**: ${tvl/1e9:.2f}B\n"
        result += f"📊 **24h Change**: {change_1d:+.2f}%\n"
        result += f"📈 **7d Change**: {change_7d:+.2f}%\n"
        result += f"⛓️ **Chain**: {chain}\n"
        result += f"🏷️ **Category**: {category}\n"
        
        return result
    
    async def _search_protocols(self, query: str) -> str:
        protocols = await self.make_request(f"{self.base_url}/protocols")
        
        if not protocols:
            return "No protocol data available"
        
        matching = [p for p in protocols if query.lower() in p.get("name", "").lower()][:5]
        
        if not matching:
            return f"No protocols found matching '{query}'"
        
        result = f"🔍 **Protocols matching '{query}':**\n\n"
        
        for protocol in matching:
            name = protocol.get("name", "Unknown")
            tvl = protocol.get("tvl", 0)
            chain = protocol.get("chain", "Multi-chain")
            result += f"• **{name}** ({chain}): ${tvl/1e9:.2f}B TVL\n"
        
        return result
