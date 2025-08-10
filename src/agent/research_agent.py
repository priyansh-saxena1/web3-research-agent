from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from typing import List, Dict, Any
import asyncio
from datetime import datetime

from src.tools.coingecko_tool import CoinGeckoTool
from src.tools.defillama_tool import DeFiLlamaTool
from src.tools.etherscan_tool import EtherscanTool
from src.agent.query_planner import QueryPlanner
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class Web3ResearchAgent:
    def __init__(self):
        self.llm = None
        self.tools = []
        self.agent = None
        self.executor = None
        self.enabled = False
        
        if not config.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured - AI agent disabled")
            return
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=config.GEMINI_API_KEY,
                temperature=0.1,
                max_tokens=2048
            )
            
            self.tools = self._initialize_tools()
            self.query_planner = QueryPlanner(self.llm)
            self.memory = ConversationBufferWindowMemory(
                memory_key="chat_history", return_messages=True, k=10
            )
            
            self.agent = self._create_agent()
            self.executor = AgentExecutor(
                agent=self.agent, tools=self.tools, memory=self.memory,
                verbose=False, max_iterations=5, handle_parsing_errors=True
            )
            self.enabled = True
            logger.info("Web3ResearchAgent initialized successfully")
            
        except Exception as e:
            logger.error(f"Agent init failed: {e}")
            self.enabled = False
    
    def _initialize_tools(self):
        tools = []
        
        try:
            tools.append(CoinGeckoTool())
            logger.info("CoinGecko tool initialized")
        except Exception as e:
            logger.warning(f"CoinGecko tool failed: {e}")
        
        try:
            tools.append(DeFiLlamaTool())
            logger.info("DeFiLlama tool initialized")
        except Exception as e:
            logger.warning(f"DeFiLlama tool failed: {e}")
        
        try:
            tools.append(EtherscanTool())
            logger.info("Etherscan tool initialized")
        except Exception as e:
            logger.warning(f"Etherscan tool failed: {e}")
        
        return tools
    
    def _create_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Web3 research assistant. Use available tools to provide accurate, 
            data-driven insights about cryptocurrency markets, DeFi protocols, and blockchain data.
            
            Format responses with clear sections, emojis, and actionable insights."""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        return create_tool_calling_agent(self.llm, self.tools, prompt)
    
    async def research_query(self, query: str) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "success": False,
                "query": query,
                "error": "AI agent not configured. Please set GEMINI_API_KEY environment variable.",
                "result": "❌ **Service Unavailable**\n\nThe AI research agent requires a GEMINI_API_KEY to function.\n\nPlease:\n1. Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)\n2. Set environment variable: `export GEMINI_API_KEY='your_key'`\n3. Restart the application",
                "sources": [],
                "metadata": {"timestamp": datetime.now().isoformat()}
            }
        
        try:
            logger.info(f"Processing: {query}")
            
            research_plan = await self.query_planner.plan_research(query)
            
            enhanced_query = f"""
            Research Query: {query}
            Research Plan: {research_plan.get('steps', [])}
            Priority: {research_plan.get('priority', 'general')}
            
            Execute systematic research and provide comprehensive analysis.
            """
            
            result = await asyncio.to_thread(
                self.executor.invoke, {"input": enhanced_query}
            )
            
            return {
                "success": True,
                "query": query,
                "research_plan": research_plan,
                "result": result.get("output", "No response"),
                "sources": self._extract_sources(result.get("output", "")),
                "metadata": {
                    "tools_used": [tool.name for tool in self.tools],
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Research error: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "result": f"❌ **Research Error**: {str(e)}\n\nPlease try a different query or check your API configuration.",
                "sources": [],
                "metadata": {"timestamp": datetime.now().isoformat()}
            }
    
    async def get_price_history(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        try:
            coingecko_tool = next(t for t in self.tools if isinstance(t, CoinGeckoTool))
            return await coingecko_tool._arun(symbol, {"type": "price_history", "days": days})
        except Exception as e:
            logger.error(f"Price history error: {e}")
            return {}
    
    async def get_comprehensive_market_data(self) -> Dict[str, Any]:
        try:
            tasks = []
            for tool in self.tools:
                if isinstance(tool, CoinGeckoTool):
                    tasks.append(tool._arun("", {"type": "market_overview"}))
                elif isinstance(tool, DeFiLlamaTool):
                    tasks.append(tool._arun("", {"type": "tvl_overview"}))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            data = {}
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    if i == 0:
                        data["market"] = result
                    elif i == 1:
                        data["defi"] = result
            
            return data
        except Exception as e:
            logger.error(f"Market data error: {e}")
            return {}
    
    def _extract_sources(self, result_text: str) -> List[str]:
        sources = []
        if "CoinGecko" in result_text or "coingecko" in result_text.lower():
            sources.append("CoinGecko API")
        if "DeFiLlama" in result_text or "defillama" in result_text.lower():
            sources.append("DeFiLlama API") 
        if "Etherscan" in result_text or "etherscan" in result_text.lower():
            sources.append("Etherscan API")
        return sources
