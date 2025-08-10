from typing import Dict, Any, List
import asyncio

class QueryPlanner:
    def __init__(self, llm):
        self.llm = llm
    
    async def plan_research(self, query: str) -> Dict[str, Any]:
        try:
            planning_prompt = f"""
            Analyze this research query and create a structured plan:
            Query: {query}
            
            Determine:
            1. What type of analysis is needed (price, market, defi, comparison, etc.)
            2. Which data sources would be most relevant
            3. What specific steps should be taken
            4. Priority focus area
            
            Respond in JSON format with keys: type, steps, priority, data_sources
            """
            
            response = await asyncio.to_thread(
                self.llm.invoke,
                planning_prompt
            )
            
            # Simple categorization based on keywords
            query_lower = query.lower()
            plan = {
                "type": self._categorize_query(query_lower),
                "steps": self._generate_steps(query_lower),
                "priority": self._determine_priority(query_lower),
                "data_sources": self._identify_sources(query_lower)
            }
            
            return plan
            
        except Exception:
            return {
                "type": "general",
                "steps": ["Analyze query", "Gather data", "Provide insights"],
                "priority": "general analysis",
                "data_sources": ["coingecko", "defillama"]
            }
    
    def _categorize_query(self, query: str) -> str:
        if any(word in query for word in ["price", "chart", "value"]):
            return "price_analysis"
        elif any(word in query for word in ["defi", "tvl", "protocol", "yield"]):
            return "defi_analysis"
        elif any(word in query for word in ["compare", "vs", "versus"]):
            return "comparison"
        elif any(word in query for word in ["market", "overview", "trending"]):
            return "market_overview"
        else:
            return "general"
    
    def _generate_steps(self, query: str) -> List[str]:
        steps = ["Gather relevant data"]
        
        if "price" in query:
            steps.extend(["Get current price data", "Analyze price trends"])
        if "defi" in query:
            steps.extend(["Fetch DeFi protocol data", "Analyze TVL trends"])
        if any(word in query for word in ["compare", "vs"]):
            steps.append("Perform comparative analysis")
        
        steps.append("Synthesize insights and recommendations")
        return steps
    
    def _determine_priority(self, query: str) -> str:
        if "urgent" in query or "now" in query:
            return "high"
        elif "overview" in query:
            return "comprehensive"
        else:
            return "standard"
    
    def _identify_sources(self, query: str) -> List[str]:
        sources = []
        if any(word in query for word in ["price", "market", "coin", "token"]):
            sources.append("coingecko")
        if any(word in query for word in ["defi", "tvl", "protocol"]):
            sources.append("defillama")
        if any(word in query for word in ["transaction", "address", "gas"]):
            sources.append("etherscan")
        
        return sources if sources else ["coingecko", "defillama"]
