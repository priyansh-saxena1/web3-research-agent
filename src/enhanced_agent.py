import google.generativeai as genai
import json
import asyncio
from typing import Dict, Any, List, Optional
from src.api_clients import coingecko_client, cryptocompare_client
from src.defillama_client import defillama_client
from src.news_aggregator import news_aggregator
from src.cache_manager import cache_manager
from src.config import config

class EnhancedResearchAgent:
    def __init__(self):
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            
        self.symbol_map = {
            "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "ada": "cardano",
            "dot": "polkadot", "bnb": "binancecoin", "usdc": "usd-coin", 
            "usdt": "tether", "xrp": "ripple", "avax": "avalanche-2",
            "link": "chainlink", "matic": "matic-network", "uni": "uniswap",
            "atom": "cosmos", "near": "near", "icp": "internet-computer",
            "ftm": "fantom", "algo": "algorand", "xlm": "stellar"
        }
    
    def _format_coin_id(self, symbol: str) -> str:
        return self.symbol_map.get(symbol.lower(), symbol.lower())
    
    async def get_comprehensive_market_data(self) -> Dict[str, Any]:
        cache_key = "comprehensive_market"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            tasks = [
                coingecko_client.get_market_data(per_page=50),
                coingecko_client.get_global_data(),
                coingecko_client.get_trending(),
                defillama_client.get_protocols(),
                defillama_client.get_tvl_data(),
                news_aggregator.get_crypto_news(5)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            data = {}
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    if i == 0: data["market_data"] = result
                    elif i == 1: data["global_data"] = result
                    elif i == 2: data["trending"] = result
                    elif i == 3: 
                        data["defi_protocols"] = result[:20] if isinstance(result, list) and result else []
                    elif i == 4: data["tvl_data"] = result
                    elif i == 5: data["news"] = result
            
            cache_manager.set(cache_key, data, 180)
            return data
            
        except Exception as e:
            raise Exception(f"Failed to fetch comprehensive market data: {str(e)}")
    
    async def get_defi_analysis(self, protocol: Optional[str] = None) -> Dict[str, Any]:
        cache_key = f"defi_analysis_{protocol or 'overview'}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            if protocol:
                data = await defillama_client.get_protocol_data(protocol)
            else:
                protocols = await defillama_client.get_protocols()
                tvl_data = await defillama_client.get_tvl_data()
                yields_data = await defillama_client.get_yields()
                
                data = {
                    "top_protocols": protocols[:20] if isinstance(protocols, list) and protocols else [],
                    "tvl_overview": tvl_data,
                    "top_yields": yields_data[:10] if isinstance(yields_data, list) and yields_data else []
                }
            
            cache_manager.set(cache_key, data, 300)
            return data
            
        except Exception as e:
            raise Exception(f"Failed to get DeFi analysis: {str(e)}")
    
    async def get_price_history(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        cache_key = f"price_history_{symbol}_{days}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            coin_id = self._format_coin_id(symbol)
            data = await coingecko_client.get_price_history(coin_id, days)
            cache_manager.set(cache_key, data, 900)
            return data
        except Exception as e:
            raise Exception(f"Failed to get price history for {symbol}: {str(e)}")
    
    async def get_advanced_coin_analysis(self, symbol: str) -> Dict[str, Any]:
        cache_key = f"advanced_analysis_{symbol.lower()}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            coin_id = self._format_coin_id(symbol)
            
            tasks = [
                coingecko_client.get_coin_data(coin_id),
                coingecko_client.get_price_history(coin_id, days=30),
                cryptocompare_client.get_social_data(symbol.upper()),
                self._get_defi_involvement(symbol.upper())
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            analysis = {}
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    if i == 0: analysis["coin_data"] = result
                    elif i == 1: analysis["price_history"] = result
                    elif i == 2: analysis["social_data"] = result
                    elif i == 3: analysis["defi_data"] = result
            
            cache_manager.set(cache_key, analysis, 300)
            return analysis
            
        except Exception as e:
            raise Exception(f"Failed advanced analysis for {symbol}: {str(e)}")
    
    async def _get_defi_involvement(self, symbol: str) -> Dict[str, Any]:
        try:
            protocols = await defillama_client.get_protocols()
            if protocols:
                relevant_protocols = [p for p in protocols if symbol.lower() in p.get("name", "").lower()]
                return {"protocols": relevant_protocols[:5]}
            return {"protocols": []}
        except:
            return {"protocols": []}
    
    def _format_comprehensive_data(self, data: Dict[str, Any]) -> str:
        formatted = "📊 COMPREHENSIVE CRYPTO MARKET ANALYSIS\n\n"
        
        if "global_data" in data and data["global_data"].get("data"):
            global_info = data["global_data"]["data"]
            total_mcap = global_info.get("total_market_cap", {}).get("usd", 0)
            total_volume = global_info.get("total_volume", {}).get("usd", 0)
            btc_dominance = global_info.get("market_cap_percentage", {}).get("btc", 0)
            eth_dominance = global_info.get("market_cap_percentage", {}).get("eth", 0)
            
            formatted += f"💰 Total Market Cap: ${total_mcap/1e12:.2f}T\n"
            formatted += f"📈 24h Volume: ${total_volume/1e9:.1f}B\n"
            formatted += f"₿ Bitcoin Dominance: {btc_dominance:.1f}%\n"
            formatted += f"Ξ Ethereum Dominance: {eth_dominance:.1f}%\n\n"
        
        if "trending" in data and data["trending"].get("coins"):
            formatted += "🔥 TRENDING CRYPTOCURRENCIES\n"
            for i, coin in enumerate(data["trending"]["coins"][:5], 1):
                name = coin.get("item", {}).get("name", "Unknown")
                symbol = coin.get("item", {}).get("symbol", "")
                score = coin.get("item", {}).get("score", 0)
                formatted += f"{i}. {name} ({symbol.upper()}) - Score: {score}\n"
            formatted += "\n"
        
        if "defi_protocols" in data and data["defi_protocols"]:
            formatted += "🏦 TOP DeFi PROTOCOLS\n"
            for i, protocol in enumerate(data["defi_protocols"][:5], 1):
                name = protocol.get("name", "Unknown")
                tvl = protocol.get("tvl", 0)
                chain = protocol.get("chain", "Unknown")
                formatted += f"{i}. {name} ({chain}): ${tvl/1e9:.2f}B TVL\n"
            formatted += "\n"
        
        if "news" in data and data["news"]:
            formatted += "📰 LATEST CRYPTO NEWS\n"
            for i, article in enumerate(data["news"][:3], 1):
                title = article.get("title", "No title")[:60] + "..."
                source = article.get("source", "Unknown")
                formatted += f"{i}. {title} - {source}\n"
            formatted += "\n"
        
        if "market_data" in data and data["market_data"]:
            formatted += "💎 TOP PERFORMING COINS (24h)\n"
            valid_coins = [coin for coin in data["market_data"][:20] if coin.get("price_change_percentage_24h") is not None]
            sorted_coins = sorted(valid_coins, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)
            for i, coin in enumerate(sorted_coins[:5], 1):
                name = coin.get("name", "Unknown")
                symbol = coin.get("symbol", "").upper()
                price = coin.get("current_price", 0)
                change = coin.get("price_change_percentage_24h", 0)
                formatted += f"{i}. {name} ({symbol}): ${price:,.4f} (+{change:.2f}%)\n"
        
        return formatted
    
    async def research_with_context(self, query: str) -> str:
        try:
            if not config.GEMINI_API_KEY or not self.model:
                return "❌ Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
            
            system_prompt = """You are an advanced Web3 and DeFi research analyst with access to real-time market data, 
            DeFi protocol information, social sentiment, and breaking news. Provide comprehensive, actionable insights 
            that combine multiple data sources for superior analysis.
            
            Guidelines:
            - Synthesize data from multiple sources (price, DeFi, social, news)
            - Provide specific recommendations with risk assessments
            - Include both technical and fundamental analysis
            - Reference current market conditions and news events
            - Use clear, professional language with data-driven insights
            - Highlight opportunities and risks clearly
            """
            
            market_context = ""
            try:
                if any(keyword in query.lower() for keyword in 
                       ["market", "overview", "analysis", "trending", "defi", "protocols"]):
                    comprehensive_data = await self.get_comprehensive_market_data()
                    market_context = f"\n\nCURRENT MARKET ANALYSIS:\n{self._format_comprehensive_data(comprehensive_data)}"
                
                for symbol in self.symbol_map.keys():
                    if symbol in query.lower() or symbol.upper() in query:
                        analysis_data = await self.get_advanced_coin_analysis(symbol)
                        if "coin_data" in analysis_data:
                            coin_info = analysis_data["coin_data"]
                            market_data = coin_info.get("market_data", {})
                            current_price = market_data.get("current_price", {}).get("usd", 0)
                            price_change = market_data.get("price_change_percentage_24h", 0)
                            market_cap = market_data.get("market_cap", {}).get("usd", 0)
                            volume = market_data.get("total_volume", {}).get("usd", 0)
                            ath = market_data.get("ath", {}).get("usd", 0)
                            ath_change = market_data.get("ath_change_percentage", {}).get("usd", 0)
                            
                            market_context += f"\n\n{symbol.upper()} DETAILED ANALYSIS:\n"
                            market_context += f"Current Price: ${current_price:,.4f}\n"
                            market_context += f"24h Change: {price_change:+.2f}%\n"
                            market_context += f"Market Cap: ${market_cap/1e9:.2f}B\n"
                            market_context += f"24h Volume: ${volume/1e9:.2f}B\n"
                            market_context += f"ATH: ${ath:,.4f} ({ath_change:+.2f}% from ATH)\n"
                        break
                
                if "defi" in query.lower():
                    defi_data = await self.get_defi_analysis()
                    if "top_protocols" in defi_data and defi_data["top_protocols"]:
                        market_context += "\n\nTOP DeFi PROTOCOLS BY TVL:\n"
                        for protocol in defi_data["top_protocols"][:5]:
                            name = protocol.get("name", "Unknown")
                            tvl = protocol.get("tvl", 0)
                            change = protocol.get("change_1d", 0)
                            market_context += f"• {name}: ${tvl/1e9:.2f}B TVL ({change:+.2f}%)\n"
                
            except Exception as e:
                market_context = f"\n\nNote: Some enhanced data unavailable ({str(e)})"
            
            full_prompt = f"{system_prompt}\n\nQuery: {query}\n\nReal-time Market Context:{market_context}"
            
            response = self.model.generate_content(full_prompt)
            return response.text if response.text else "❌ No response generated. Please try rephrasing your query."
            
        except Exception as e:
            return f"❌ Enhanced research failed: {str(e)}"
    
    async def close(self):
        await coingecko_client.close()
        await cryptocompare_client.close()
        await defillama_client.close()
        await news_aggregator.close()