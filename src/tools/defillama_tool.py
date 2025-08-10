from typing import Dict, Any, Optional
from pydantic import BaseModel, PrivateAttr
from src.tools.base_tool import BaseWeb3Tool, Web3ToolInput

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
            return f"DeFiLlama error: {str(e)}"
    
    async def _get_top_protocols(self) -> str:
        data = await self.make_request(f"{self.base_url}/protocols")
        
        if not data:
            return "No DeFi protocol data available"
        
        top_protocols = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)[:10]
        
        result = "🏦 **Top DeFi Protocols by TVL:**\n\n"
        
        for i, protocol in enumerate(top_protocols, 1):
            name = protocol.get("name", "Unknown")
            tvl = protocol.get("tvl", 0)
            change = protocol.get("change_1d", 0)
            chain = protocol.get("chain", "Multi-chain")
            
            emoji = "📈" if change >= 0 else "📉"
            result += f"{i}. **{name}** ({chain}): ${tvl/1e9:.2f}B TVL {emoji} ({change:+.2f}%)\n"
        
        return result
    
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
