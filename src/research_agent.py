from google import genai
from google.genai import types
import json
from typing import Dict, Any, List
from src.api_clients import coingecko_client, cryptocompare_client
from src.cache_manager import cache_manager
from src.config import config
import asyncio

class ResearchAgent:
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.symbol_map = {
            "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
            "ada": "cardano", "dot": "polkadot", "bnb": "binancecoin",
            "usdc": "usd-coin", "usdt": "tether", "xrp": "ripple",
            "avax": "avalanche-2", "link": "chainlink", "matic": "matic-network"
        }
    
    def _format_coin_id(self, symbol: str) -> str:
        return self.symbol_map.get(symbol.lower(), symbol.lower())
    
    async def get_market_overview(self) -> Dict[str, Any]:
        cache_key = "market_overview"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            market_data = await coingecko_client.get_market_data(per_page=20)
            global_data = await coingecko_client.get_global_data()
            trending = await coingecko_client.get_trending()
            
            result = {
                "market_data": market_data,
                "global_data": global_data,
                "trending": trending
            }
            
            cache_manager.set(cache_key, result)
            return result
            
        except Exception as e:
            raise Exception(f"Failed to fetch market overview: {str(e)}")
    
    async def get_price_history(self, symbol: str) -> Dict[str, Any]:
        cache_key = f"price_history_{symbol.lower()}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            coin_id = self._format_coin_id(symbol)
            data = await coingecko_client.get_price_history(coin_id, days=30)
            
            cache_manager.set(cache_key, data)
            return data
            
        except Exception as e:
            raise Exception(f"Failed to fetch price history for {symbol}: {str(e)}")
    
    async def get_coin_analysis(self, symbol: str) -> Dict[str, Any]:
        cache_key = f"coin_analysis_{symbol.lower()}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            coin_id = self._format_coin_id(symbol)
            
            tasks = [
                coingecko_client.get_coin_data(coin_id),
                coingecko_client.get_price_history(coin_id, days=7),
                cryptocompare_client.get_social_data(symbol.upper())
            ]
            
            coin_data, price_history, social_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            result = {}
            if not isinstance(coin_data, Exception):
                result["coin_data"] = coin_data
            if not isinstance(price_history, Exception):
                result["price_history"] = price_history
            if not isinstance(social_data, Exception):
                result["social_data"] = social_data
            
            cache_manager.set(cache_key, result)
            return result
            
        except Exception as e:
            raise Exception(f"Failed to analyze {symbol}: {str(e)}")
    
    def _format_market_data(self, data: Dict[str, Any]) -> str:
        if not data:
            return "No market data available"
        
        formatted = "📊 MARKET OVERVIEW\n\n"
        
        if "global_data" in data and "data" in data["global_data"]:
            global_info = data["global_data"]["data"]
            total_mcap = global_info.get("total_market_cap", {}).get("usd", 0)
            total_volume = global_info.get("total_volume", {}).get("usd", 0)
            btc_dominance = global_info.get("market_cap_percentage", {}).get("btc", 0)
            
            formatted += f"Total Market Cap: ${total_mcap:,.0f}\n"
            formatted += f"24h Volume: ${total_volume:,.0f}\n"
            formatted += f"Bitcoin Dominance: {btc_dominance:.1f}%\n\n"
        
        if "trending" in data and "coins" in data["trending"]:
            formatted += "🔥 TRENDING COINS\n"
            for i, coin in enumerate(data["trending"]["coins"][:5], 1):
                name = coin.get("item", {}).get("name", "Unknown")
                symbol = coin.get("item", {}).get("symbol", "")
                formatted += f"{i}. {name} ({symbol.upper()})\n"
            formatted += "\n"
        
        if "market_data" in data:
            formatted += "💰 TOP CRYPTOCURRENCIES\n"
            for i, coin in enumerate(data["market_data"][:10], 1):
                name = coin.get("name", "Unknown")
                symbol = coin.get("symbol", "").upper()
                price = coin.get("current_price", 0)
                change = coin.get("price_change_percentage_24h", 0)
                change_symbol = "📈" if change >= 0 else "📉"
                
                formatted += f"{i:2d}. {name} ({symbol}): ${price:,.4f} {change_symbol} {change:+.2f}%\n"
        
        return formatted
    
    async def research(self, query: str) -> str:
        try:
            if not config.GEMINI_API_KEY:
                return "❌ Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
            
            system_prompt = """You are an expert Web3 and cryptocurrency research analyst. 
            Provide comprehensive, accurate, and actionable insights based on real market data.
            
            Guidelines:
            - Give specific, data-driven analysis
            - Include price targets and risk assessments when relevant
            - Explain technical concepts clearly
            - Provide actionable recommendations
            - Use emojis for better readability
            - Be concise but thorough
            """
            
            market_context = ""
            try:
                if any(keyword in query.lower() for keyword in ["market", "overview", "trending", "top"]):
                    market_data = await self.get_market_overview()
                    market_context = f"\n\nCURRENT MARKET DATA:\n{self._format_market_data(market_data)}"
                
                for symbol in ["btc", "eth", "sol", "ada", "dot", "bnb", "avax", "link"]:
                    if symbol in query.lower() or symbol.upper() in query:
                        analysis_data = await self.get_coin_analysis(symbol)
                        if "coin_data" in analysis_data:
                            coin_info = analysis_data["coin_data"]
                            market_data = coin_info.get("market_data", {})
                            current_price = market_data.get("current_price", {}).get("usd", 0)
                            price_change = market_data.get("price_change_percentage_24h", 0)
                            market_cap = market_data.get("market_cap", {}).get("usd", 0)
                            volume = market_data.get("total_volume", {}).get("usd", 0)
                            
                            market_context += f"\n\n{symbol.upper()} DATA:\n"
                            market_context += f"Price: ${current_price:,.4f}\n"
                            market_context += f"24h Change: {price_change:+.2f}%\n"
                            market_context += f"Market Cap: ${market_cap:,.0f}\n"
                            market_context += f"Volume: ${volume:,.0f}\n"
                        break
                
            except Exception as e:
                market_context = f"\n\nNote: Some market data unavailable ({str(e)})"
            
            full_prompt = f"{query}{market_context}"
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        role="user", 
                        parts=[types.Part(text=full_prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            if response.text:
                return response.text
            else:
                return "❌ No response generated. Please try rephrasing your query."
                
        except Exception as e:
            return f"❌ Research failed: {str(e)}"
    
    async def close(self):
        await coingecko_client.close()
        await cryptocompare_client.close()
