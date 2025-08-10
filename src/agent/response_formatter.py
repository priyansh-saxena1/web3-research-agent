from typing import Dict, Any, Optional
import json
import re

class ResponseFormatter:
    """Formats AI agent responses for optimal user experience"""
    
    @staticmethod  
    def format_research_response(response: str, data: Optional[Dict[str, Any]] = None) -> str:
        """Format research response with structured data presentation"""
        if not response:
            return "No information available."
        
        formatted = response.strip()
        
        if data:
            if "prices" in data:
                formatted = ResponseFormatter._add_price_formatting(formatted, data["prices"])
            if "metrics" in data:
                formatted = ResponseFormatter._add_metrics_formatting(formatted, data["metrics"])
        
        formatted = ResponseFormatter._enhance_markdown(formatted)
        return formatted
    
    @staticmethod
    def _add_price_formatting(text: str, prices: Dict[str, float]) -> str:
        """Add price data with formatting"""
        price_section = "\n\n📈 **Current Prices:**\n"
        for symbol, price in prices.items():
            price_section += f"• **{symbol.upper()}**: ${price:,.2f}\n"
        return text + price_section
    
    @staticmethod  
    def _add_metrics_formatting(text: str, metrics: Dict[str, Any]) -> str:
        """Add metrics with formatting"""
        metrics_section = "\n\n📊 **Key Metrics:**\n"
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                metrics_section += f"• **{key.title()}**: {value:,.2f}\n"
            else:
                metrics_section += f"• **{key.title()}**: {value}\n"
        return text + metrics_section
    
    @staticmethod
    def _enhance_markdown(text: str) -> str:
        """Enhance markdown formatting for better readability"""
        text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        return text.strip()
