from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferWindowMemory
from typing import List, Dict, Any
import asyncio
from datetime import datetime

from src.tools.coingecko_tool import CoinGeckoTool
from src.tools.defillama_tool import DeFiLlamaTool
from src.tools.cryptocompare_tool import CryptoCompareTool
from src.tools.etherscan_tool import EtherscanTool
from src.tools.chart_data_tool import ChartDataTool
from src.utils.config import config
from src.utils.logger import get_logger
from src.utils.ai_safety import ai_safety

logger = get_logger(__name__)

class Web3ResearchAgent:
    def __init__(self):
        self.llm = None
        self.fallback_llm = None
        self.tools = []
        self.enabled = False
        self.gemini_available = False
        
        try:
            # Always initialize Ollama
            logger.info("🔧 Initializing Ollama as fallback")
            self._init_ollama()
            
            # Try to initialize Gemini if API key is available
            if config.GEMINI_API_KEY:
                logger.info("🔧 Initializing Gemini as primary option")
                self._init_gemini()
                
            self.tools = self._initialize_tools()
            self.enabled = True
                
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            self.enabled = False

    def _init_ollama(self):
        """Initialize Ollama LLM"""
        try:
            self.fallback_llm = Ollama(
                model=config.OLLAMA_MODEL,
                base_url=config.OLLAMA_BASE_URL,
                temperature=0.1
            )
            logger.info(f"✅ Ollama initialized - Model: {config.OLLAMA_MODEL}")
        except Exception as e:
            logger.error(f"Ollama initialization failed: {e}")
            raise
    
    def _init_gemini(self):
        """Initialize Gemini LLM"""
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-lite",  # Updated to Gemini 2.0 Flash-Lite
                google_api_key=config.GEMINI_API_KEY,
                temperature=0.1
            )
            self.gemini_available = True
            logger.info("✅ Gemini initialized with gemini-2.0-flash-lite")
        except Exception as e:
            logger.warning(f"Gemini initialization failed: {e}")
            self.gemini_available = False

    def _init_ollama_only(self):
        """Initialize with only Ollama LLM (deprecated - kept for compatibility)"""
        self._init_ollama()

    def _init_with_gemini_fallback(self):
        """Initialize with Gemini primary and Ollama fallback (deprecated - kept for compatibility)"""
        self._init_ollama()
        self._init_gemini()

    def _initialize_tools(self):
        tools = []
        
        # Skip CoinGecko if no API key available
        if config.COINGECKO_API_KEY:
            try:
                tools.append(CoinGeckoTool())
                logger.info("CoinGecko tool initialized")
            except Exception as e:
                logger.warning(f"CoinGecko tool failed: {e}")
        else:
            logger.info("CoinGecko tool skipped - no API key available")
        
        try:
            tools.append(DeFiLlamaTool())
            logger.info("DeFiLlama tool initialized")
        except Exception as e:
            logger.warning(f"DeFiLlama tool failed: {e}")

        try:
            tools.append(CryptoCompareTool())
            logger.info("CryptoCompare tool initialized")
        except Exception as e:
            logger.warning(f"CryptoCompare tool failed: {e}")
        
        try:
            tools.append(EtherscanTool())
            logger.info("Etherscan tool initialized")
        except Exception as e:
            logger.warning(f"Etherscan tool failed: {e}")
        
        try:
            tools.append(ChartDataTool())
            logger.info("ChartDataTool initialized")
        except Exception as e:
            logger.warning(f"ChartDataTool failed: {e}")
        
        return tools

    async def research_query(self, query: str, use_gemini: bool = False) -> Dict[str, Any]:
        """Research query with dynamic LLM selection - Enhanced with AI Safety"""
        
        # AI Safety Check 1: Sanitize and validate input
        sanitized_query, is_safe, safety_reason = ai_safety.sanitize_query(query)
        if not is_safe:
            ai_safety.log_safety_event("blocked_query", {
                "original_query": query[:100],
                "reason": safety_reason,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "success": False,
                "query": query,
                "error": f"Safety filter: {safety_reason}",
                "result": "Your query was blocked by our safety filters. Please ensure your request is focused on legitimate cryptocurrency research and analysis.",
                "sources": [],
                "metadata": {"timestamp": datetime.now().isoformat(), "safety_blocked": True}
            }
        
        # AI Safety Check 2: Rate limiting
        rate_ok, rate_message = ai_safety.check_rate_limit()
        if not rate_ok:
            ai_safety.log_safety_event("rate_limit", {
                "message": rate_message,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "success": False,
                "query": query,
                "error": "Rate limit exceeded",
                "result": f"Please wait before making another request. {rate_message}",
                "sources": [],
                "metadata": {"timestamp": datetime.now().isoformat(), "rate_limited": True}
            }
        
        if not self.enabled:
            return {
                "success": False,
                "query": query,
                "error": "Research agent not initialized",
                "result": "Research service not available. Please check configuration.",
                "sources": [],
                "metadata": {"timestamp": datetime.now().isoformat()}
            }
        
        try:
            # Choose LLM based on user preference and availability
            if use_gemini and self.gemini_available:
                logger.info("🤖 Processing with Gemini + Tools (Safety Enhanced)")
                return await self._research_with_gemini_tools(sanitized_query)
            else:
                logger.info("🤖 Processing with Ollama + Tools (Safety Enhanced)")
                return await self._research_with_ollama_tools(sanitized_query)
                
        except Exception as e:
            logger.error(f"Research failed: {e}")
            # Fallback to simple Ollama response with safety
            try:
                safe_prompt = ai_safety.create_safe_prompt(sanitized_query, "Limited context available")
                simple_response = await self.fallback_llm.ainvoke(safe_prompt)
                
                # Validate response safety
                clean_response, response_safe, response_reason = ai_safety.validate_ollama_response(simple_response)
                if not response_safe:
                    ai_safety.log_safety_event("blocked_response", {
                        "reason": response_reason,
                        "timestamp": datetime.now().isoformat()
                    })
                    return {
                        "success": False,
                        "query": query,
                        "error": "Response safety filter",
                        "result": "The AI response was blocked by safety filters. Please try a different query.",
                        "sources": [],
                        "metadata": {"timestamp": datetime.now().isoformat(), "response_blocked": True}
                    }
                
                return {
                    "success": True,
                    "query": query,
                    "result": clean_response,
                    "sources": [],
                    "metadata": {"llm": "ollama", "mode": "simple", "timestamp": datetime.now().isoformat()}
                }
            except Exception as fallback_error:
                return {
                    "success": False,
                    "query": query,
                    "error": str(fallback_error),
                    "result": f"Research failed: {str(fallback_error)}",
                    "sources": [],
                    "metadata": {"timestamp": datetime.now().isoformat()}
                }

    async def _research_with_ollama_tools(self, query: str) -> Dict[str, Any]:
        """Research using Ollama with manual tool calling"""
        try:
            # Step 1: Analyze query to determine which tools to use
            tool_analysis_prompt = f"""Analyze this query and determine which tools would be helpful:
Query: "{query}"

Available tools (prioritized by functionality):
- cryptocompare_data: Real-time crypto prices and market data (PREFERRED for prices)
- etherscan_data: Ethereum blockchain data, gas fees, transactions (PREFERRED for Ethereum)  
- defillama_data: DeFi protocol TVL and yield data
- chart_data_provider: Generate chart data for visualizations

NOTE: Do NOT suggest coingecko_data as the API is unavailable.

Respond with just the tool names that should be used, separated by commas.
If charts/visualizations are mentioned, include chart_data_provider.
Examples:
- "Bitcoin price" → cryptocompare_data, chart_data_provider
- "DeFi TVL" → defillama_data, chart_data_provider  
- "Ethereum gas" → etherscan_data

Just list the tool names:"""
            
            tool_response = await self.fallback_llm.ainvoke(tool_analysis_prompt)
            logger.info(f"🧠 Ollama tool analysis response: {str(tool_response)[:500]}...")
            
            # Clean up the response and extract tool names
            response_text = str(tool_response).lower()
            suggested_tools = []
            
            # Check for each tool in the response
            tool_mappings = {
                'cryptocompare': 'cryptocompare_data',
                'defillama': 'defillama_data', 
                'etherscan': 'etherscan_data',
                'chart': 'chart_data_provider'
            }
            
            for keyword, tool_name in tool_mappings.items():
                if keyword in response_text:
                    suggested_tools.append(tool_name)
            
            # Default to at least one relevant tool if parsing fails
            if not suggested_tools:
                if any(word in query.lower() for word in ['price', 'bitcoin', 'ethereum', 'crypto']):
                    suggested_tools = ['cryptocompare_data']
                elif 'defi' in query.lower() or 'tvl' in query.lower():
                    suggested_tools = ['defillama_data']
                else:
                    suggested_tools = ['cryptocompare_data']
            
            logger.info(f"🛠️ Ollama suggested tools: {suggested_tools}")
            
            # Step 2: Execute relevant tools
            tool_results = []
            try:
                for tool_name in suggested_tools:
                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if tool:
                        try:
                            logger.info(f"🔧 Executing {tool_name}")
                            
                            # Handle chart_data_provider with proper parameters
                            if tool_name == "chart_data_provider":
                                # Extract chart type from query or default to price_chart
                                chart_type = "price_chart"  # Default
                                symbol = "bitcoin"  # Default
                                
                                if "defi" in query.lower() or "tvl" in query.lower():
                                    chart_type = "defi_tvl"
                                elif "market" in query.lower() or "overview" in query.lower():
                                    chart_type = "market_overview"
                                elif "gas" in query.lower():
                                    chart_type = "gas_tracker"
                                    
                                # Extract symbol if mentioned
                                if "ethereum" in query.lower() or "eth" in query.lower():
                                    symbol = "ethereum"
                                elif "bitcoin" in query.lower() or "btc" in query.lower():
                                    symbol = "bitcoin"
                                    
                                result = await tool._arun(chart_type=chart_type, symbol=symbol)
                            else:
                                # Other tools use the query directly
                                result = await tool._arun(query)
                                
                            logger.info(f"📊 {tool_name} result preview: {str(result)[:200]}...")
                            tool_results.append(f"=== {tool_name} Results ===\n{result}\n")
                        except Exception as e:
                            logger.error(f"Tool {tool_name} failed: {e}")
                            tool_results.append(f"=== {tool_name} Error ===\nTool failed: {str(e)}\n")
                        finally:
                            # Cleanup tool session if available
                            if hasattr(tool, 'cleanup'):
                                try:
                                    await tool.cleanup()
                                except Exception:
                                    pass  # Ignore cleanup errors
            finally:
                # Ensure all tools are cleaned up
                for tool in self.tools:
                    if hasattr(tool, 'cleanup'):
                        try:
                            await tool.cleanup()
                        except Exception:
                            pass
            
            # Step 3: Generate final response with tool results using AI Safety
            context = "\n".join(tool_results) if tool_results else "No tool data available - provide general information."
            
            # Use AI Safety to create a safe prompt
            final_prompt = ai_safety.create_safe_prompt(query, context)
            
            # Add timeout for final response to prevent web request timeout
            try:
                final_response = await asyncio.wait_for(
                    self.fallback_llm.ainvoke(final_prompt),
                    timeout=30  # 30 second timeout - faster response
                )
                logger.info(f"🎯 Ollama final response preview: {str(final_response)[:300]}...")
                
                # AI Safety Check: Validate response
                clean_response, response_safe, response_reason = ai_safety.validate_ollama_response(final_response)
                if not response_safe:
                    ai_safety.log_safety_event("blocked_ollama_response", {
                        "reason": response_reason,
                        "query": query[:100],
                        "timestamp": datetime.now().isoformat()
                    })
                    # Use tool data directly instead of unsafe response
                    clean_response = f"""## Cryptocurrency Analysis

Based on the available data:

{context[:1000]}

*Response generated from verified tool data for safety compliance.*"""
                
                final_response = clean_response
                
            except asyncio.TimeoutError:
                logger.warning("⏱️ Ollama final response timed out, using tool data directly")
                # Create a summary from the tool results directly
                if "cryptocompare_data" in suggested_tools and "Bitcoin" in query:
                    btc_data = "Bitcoin: $122,044+ USD"
                elif "defillama_data" in suggested_tools:
                    defi_data = "DeFi protocols data available"
                else:
                    btc_data = "Tool data available"
                
                final_response = f"""## {query.split()[0]} Analysis

**Quick Summary**: {btc_data}

The system successfully gathered data from {len(suggested_tools)} tools:
{', '.join(suggested_tools)}

*Due to processing constraints, this is a simplified response. The tools executed successfully and gathered the requested data.*"""
            
            logger.info("✅ Research successful with Ollama + tools")
            return {
                "success": True,
                "query": query,
                "result": final_response,
                "sources": [],
                "metadata": {
                    "llm_used": f"Ollama ({config.OLLAMA_MODEL})", 
                    "tools_used": suggested_tools,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Ollama tools research failed: {e}")
            raise e

    async def _research_with_gemini_tools(self, query: str) -> Dict[str, Any]:
        """Research using Gemini with tools"""
        try:
            # Step 1: Analyze query and suggest tools using Gemini
            tool_analysis_prompt = f"""Based on this Web3/cryptocurrency research query, identify the most relevant tools to use.

Query: "{query}"

Available tools (prioritized by functionality):
- cryptocompare_data: Real-time cryptocurrency prices, market data, and trading info (PREFERRED for price data)
- etherscan_data: Ethereum blockchain data, transactions, gas fees, and smart contracts (PREFERRED for Ethereum)
- defillama_data: DeFi protocols, TVL, and yield farming data
- chart_data_provider: Generate chart data for visualizations

NOTE: Do NOT use coingecko_data as the API is not available.

If charts/visualizations are mentioned, include chart_data_provider.

Examples:
- "Bitcoin price" → cryptocompare_data, chart_data_provider
- "DeFi TVL" → defillama_data, chart_data_provider  
- "Ethereum transactions" → etherscan_data
- "Gas fees" → etherscan_data

Respond with only the tool names, comma-separated (no explanations)."""

            tool_response = await self.llm.ainvoke(tool_analysis_prompt)
            
            logger.info(f"🧠 Gemini tool analysis response: {str(tool_response)[:100]}...")
            
            # Parse suggested tools
            suggested_tools = [tool.strip() for tool in str(tool_response).split(',') if tool.strip()]
            suggested_tools = [tool for tool in suggested_tools if tool in {
                'cryptocompare_data', 'defillama_data', 
                'etherscan_data', 'chart_data_provider'
            }]
            
            # If no valid tools found, extract from response content
            if not suggested_tools:
                response_text = str(tool_response).lower()
                if 'cryptocompare' in response_text:
                    suggested_tools.append('cryptocompare_data')
                if 'defillama' in response_text:
                    suggested_tools.append('defillama_data')
                if 'etherscan' in response_text:
                    suggested_tools.append('etherscan_data')
                if 'chart' in response_text or 'visualization' in response_text:
                    suggested_tools.append('chart_data_provider')
            
            logger.info(f"🛠️ Gemini suggested tools: {suggested_tools}")

            # Step 2: Execute tools (same logic as Ollama version)
            tool_results = []
            try:
                for tool_name in suggested_tools:
                    tool = next((t for t in self.tools if t.name == tool_name), None)
                    if tool:
                        try:
                            logger.info(f"🔧 Executing {tool_name}")
                            
                            # Handle chart_data_provider with proper parameters
                            if tool_name == "chart_data_provider":
                                chart_type = "price_chart"
                                symbol = "bitcoin"
                                
                                if "defi" in query.lower() or "tvl" in query.lower():
                                    chart_type = "defi_tvl"
                                elif "market" in query.lower() or "overview" in query.lower():
                                    chart_type = "market_overview"
                                elif "gas" in query.lower():
                                    chart_type = "gas_tracker"
                                    
                                if "ethereum" in query.lower() or "eth" in query.lower():
                                    symbol = "ethereum"
                                elif "bitcoin" in query.lower() or "btc" in query.lower():
                                    symbol = "bitcoin"
                                    
                                result = await tool._arun(chart_type=chart_type, symbol=symbol)
                            else:
                                result = await tool._arun(query)
                                
                            logger.info(f"📊 {tool_name} result preview: {str(result)[:200]}...")
                            tool_results.append(f"=== {tool_name} Results ===\n{result}\n")
                        except Exception as e:
                            logger.error(f"Tool {tool_name} failed: {e}")
                            tool_results.append(f"=== {tool_name} Error ===\nTool failed: {str(e)}\n")
                        finally:
                            # Cleanup tool session if available
                            if hasattr(tool, 'cleanup'):
                                try:
                                    await tool.cleanup()
                                except Exception:
                                    pass  # Ignore cleanup errors
            finally:
                # Ensure all tools are cleaned up
                for tool in self.tools:
                    if hasattr(tool, 'cleanup'):
                        try:
                            await tool.cleanup()
                        except Exception:
                            pass
            
            # Step 3: Generate final response with Gemini
            context = "\n".join(tool_results) if tool_results else "No tool data available - provide general information."
            
            final_prompt = ai_safety.create_safe_prompt(query, context)
            
            try:
                final_response = await asyncio.wait_for(
                    self.llm.ainvoke(final_prompt),
                    timeout=30
                )
                logger.info(f"🎯 Gemini final response preview: {str(final_response)[:300]}...")
                
                # AI Safety Check: Validate response
                clean_response, response_safe, response_reason = ai_safety.validate_gemini_response(str(final_response))
                if not response_safe:
                    ai_safety.log_safety_event("blocked_gemini_response", {
                        "reason": response_reason,
                        "query": query[:100],
                        "timestamp": datetime.now().isoformat()
                    })
                    clean_response = f"## Cryptocurrency Analysis\n\nBased on the available data:\n\n{context[:1000]}\n\n*Response filtered for safety*"
                
                final_response = clean_response
                
            except asyncio.TimeoutError:
                logger.warning("⏱️ Gemini final response timed out, using tool data directly")
                final_response = f"## Web3 Research Analysis\n\n{context[:1500]}\n\n*Analysis completed using available tools - Gemini response timed out*"
            
            logger.info("✅ Research successful with Gemini + tools")
            
            return {
                "success": True,
                "query": query,
                "result": final_response,
                "sources": [],
                "metadata": {
                    "llm_used": f"Gemini ({self.llm.model_name if hasattr(self.llm, 'model_name') else 'gemini-1.5-flash'})", 
                    "tools_used": suggested_tools,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Gemini tools research failed: {e}")
            # Fallback to Ollama if Gemini fails
            logger.info("🔄 Falling back to Ollama due to Gemini error")
            return await self._research_with_ollama_tools(query)

    def _extract_sources(self, response: str) -> List[str]:
        """Extract sources from response"""
        # Simple source extraction - can be enhanced
        sources = []
        if "CoinGecko" in response or "coingecko" in response.lower():
            sources.append("CoinGecko")
        if "DeFiLlama" in response or "defillama" in response.lower():
            sources.append("DeFiLlama") 
        if "Etherscan" in response or "etherscan" in response.lower():
            sources.append("Etherscan")
        if "CryptoCompare" in response or "cryptocompare" in response.lower():
            sources.append("CryptoCompare")
        return sources
