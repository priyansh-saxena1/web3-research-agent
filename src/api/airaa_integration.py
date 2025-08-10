import aiohttp
import re
from typing import Dict, Any, List
from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AIRAAIntegration:
    def __init__(self):
        self.webhook_url = config.AIRAA_WEBHOOK_URL
        self.api_key = config.AIRAA_API_KEY
        self.enabled = bool(self.webhook_url)
    
    async def send_research_data(self, research_result: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        
        try:
            payload = self._format_for_airaa(research_result)
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.webhook_url, json=payload, headers=headers
                ) as response:
                    success = response.status == 200
                    if success:
                        logger.info("Data sent to AIRAA successfully")
                    else:
                        logger.warning(f"AIRAA webhook returned {response.status}")
                    return success
                    
        except Exception as e:
            logger.error(f"AIRAA integration failed: {e}")
            return False
    
    def _format_for_airaa(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "web3-research-copilot",
            "timestamp": result["metadata"]["timestamp"],
            "query": result["query"],
            "research_plan": result.get("research_plan", {}),
            "findings": result["result"],
            "data_sources": result["sources"],
            "confidence_score": self._calculate_confidence(result),
            "tags": self._extract_tags(result["query"]),
            "structured_data": self._extract_structured_data(result["result"])
        }
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        base_score = 0.7
        source_boost = min(len(result.get("sources", [])) * 0.1, 0.3)
        error_penalty = 0.3 if not result.get("success", True) else 0
        return max(0.0, min(1.0, base_score + source_boost - error_penalty))
    
    def _extract_tags(self, query: str) -> List[str]:
        tags = []
        query_lower = query.lower()
        
        token_patterns = {
            "bitcoin": ["bitcoin", "btc"],
            "ethereum": ["ethereum", "eth"],
            "defi": ["defi", "defillama", "protocol", "tvl"],
            "market-analysis": ["price", "market", "analysis"],
            "trading-volume": ["volume", "trading"]
        }
        
        for tag, patterns in token_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                tags.append(tag)
        
        return tags
    
    def _extract_structured_data(self, result_text: str) -> Dict[str, Any]:
        structured = {}
        
        price_pattern = r'\$([0-9,]+\.?[0-9]*)'
        percentage_pattern = r'([+-]?[0-9]+\.?[0-9]*)%'
        
        prices = re.findall(price_pattern, result_text)
        percentages = re.findall(percentage_pattern, result_text)
        
        if prices:
            structured["prices"] = [float(p.replace(',', '')) for p in prices[:5]]
        if percentages:
            structured["percentages"] = [float(p) for p in percentages[:5]]
        
        return structured
