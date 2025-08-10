from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import plotly
import plotly.graph_objects as go

load_dotenv()

from src.agent.research_agent import Web3ResearchAgent
from src.api.airaa_integration import AIRAAIntegration  
from src.utils.logger import get_logger
from src.utils.config import config
from src.visualizations import CryptoVisualizations

logger = get_logger(__name__)

app = FastAPI(
    title="Web3 Research Co-Pilot",
    description="Professional cryptocurrency research assistant",
    version="2.0.0"
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = []

class QueryResponse(BaseModel):
    success: bool
    response: str
    sources: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
    visualizations: Optional[List[str]] = []
    error: Optional[str] = None

class Web3CoPilotService:
    def __init__(self):
        try:
            logger.info("Initializing Web3 Research Co-Pilot...")
            
            if config.GEMINI_API_KEY:
                logger.info("Initializing AI research agent...")
                self.agent = Web3ResearchAgent()
                logger.info("AI research agent initialized")
            else:
                logger.warning("GEMINI_API_KEY not configured - limited functionality")
                self.agent = None
            
            logger.info("Initializing integrations...")
            self.airaa = AIRAAIntegration()
            
            self.enabled = bool(config.GEMINI_API_KEY)
            self.visualizer = CryptoVisualizations()
            
            logger.info(f"Service initialized (AI enabled: {self.enabled})")
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            self.agent = None
            self.airaa = None
            self.enabled = False
            self.visualizer = CryptoVisualizations()
    
    async def process_query(self, query: str) -> QueryResponse:
        """Process research query with visualizations"""
        logger.info(f"🔍 Processing query: {query[:100]}...")
        
        if not query.strip():
            logger.warning("⚠️ Empty query received")
            return QueryResponse(
                success=False, 
                response="Please provide a research query.", 
                error="Empty query"
            )
        
        try:
            if not self.enabled:
                logger.info("ℹ️ Processing in limited mode (no GEMINI_API_KEY)")
                response = """**Research Assistant - Limited Mode**

API access available for basic cryptocurrency data:
• Market prices and statistics
• DeFi protocol information  
• Network gas fees

Configure GEMINI_API_KEY environment variable for full AI analysis."""
                return QueryResponse(success=True, response=response, sources=["System"])
            
            logger.info("🤖 Processing with AI research agent...")
            logger.info(f"🛠️ Available tools: {[tool.name for tool in self.agent.tools] if self.agent else []}")
            
            result = await self.agent.research_query(query)
            logger.info(f"🔄 Agent research completed: success={result.get('success')}")
            
            if result.get("success"):
                response = result.get("result", "No analysis generated")
                sources = result.get("sources", [])
                metadata = result.get("metadata", {})
                
                logger.info(f"📊 Response generated: {len(response)} chars, {len(sources)} sources")
                
                # Generate visualizations if relevant data is available
                visualizations = []
                if metadata:
                    logger.info("📈 Checking for visualization data...")
                    vis_html = await self._generate_visualizations(metadata, query)
                    if vis_html:
                        visualizations.append(vis_html)
                        logger.info("✅ Visualization generated")
                
                # Send to AIRAA if enabled
                if self.airaa and self.airaa.enabled:
                    try:
                        await self.airaa.send_research_data(query, response)
                        logger.info("📤 Data sent to AIRAA")
                    except Exception as e:
                        logger.warning(f"⚠️ AIRAA integration failed: {e}")
                
                return QueryResponse(
                    success=True, 
                    response=response, 
                    sources=sources, 
                    metadata=metadata,
                    visualizations=visualizations
                )
            else:
                error_msg = result.get("error", "Research analysis failed")
                logger.error(f"❌ Research failed: {error_msg}")
                return QueryResponse(success=False, response=error_msg, error=error_msg)
            
        except Exception as e:
            logger.error(f"💥 Query processing error: {e}", exc_info=True)
            error_msg = f"Processing error: {str(e)}"
            return QueryResponse(success=False, response=error_msg, error=error_msg)
    
    async def _generate_visualizations(self, metadata: Dict[str, Any], query: str) -> Optional[str]:
        """Generate visualizations based on query and metadata"""
        try:
            # Check for price data
            if 'price_data' in metadata:
                symbol = self._extract_symbol_from_query(query)
                fig = self.visualizer.create_price_chart(metadata['price_data'], symbol)
                return plotly.io.to_html(fig, include_plotlyjs='cdn', div_id='price_chart')
            
            # Check for market data
            elif 'market_data' in metadata:
                fig = self.visualizer.create_market_overview(metadata['market_data'])
                return plotly.io.to_html(fig, include_plotlyjs='cdn', div_id='market_overview')
            
            # Check for DeFi data
            elif 'defi_data' in metadata:
                fig = self.visualizer.create_defi_tvl_chart(metadata['defi_data'])
                return plotly.io.to_html(fig, include_plotlyjs='cdn', div_id='defi_chart')
            
            return None
            
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}")
            return None
    
    def _extract_symbol_from_query(self, query: str) -> str:
        """Extract cryptocurrency symbol from query"""
        symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'AVAX', 'MATIC', 'DOT', 'LINK']
        query_upper = query.upper()
        for symbol in symbols:
            if symbol in query_upper:
                return symbol
        return 'BTC'  # Default

# Initialize service
service = Web3CoPilotService()

@app.get("/", response_class=HTMLResponse)
async def get_homepage(request: Request):
    """Serve minimalist, professional interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Web3 Research Co-Pilot</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22><path fill=%22%2300d4aa%22 d=%22M12 2L2 7v10c0 5.5 3.8 7.7 9 9 5.2-1.3 9-3.5 9-9V7l-10-5z%22/></svg>">
        
        <style>
            :root {
                --primary: #0066ff;
                --primary-dark: #0052cc;
                --accent: #00d4aa;
                --background: #000000;
                --surface: #111111;
                --surface-elevated: #1a1a1a;
                --text: #ffffff;
                --text-secondary: #a0a0a0;
                --text-muted: #666666;
                --border: rgba(255, 255, 255, 0.08);
                --border-focus: rgba(0, 102, 255, 0.3);
                --shadow: rgba(0, 0, 0, 0.4);
                --success: #00d4aa;
                --warning: #ffa726;
                --error: #f44336;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                background: var(--background);
                color: var(--text);
                line-height: 1.5;
                min-height: 100vh;
                font-weight: 400;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }

            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 2rem 1.5rem;
            }

            .header {
                text-align: center;
                margin-bottom: 2.5rem;
            }

            .header h1 {
                font-size: 2.25rem;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 0.5rem;
                letter-spacing: -0.025em;
            }

            .header .brand {
                color: var(--primary);
            }

            .header p {
                color: var(--text-secondary);
                font-size: 1rem;
                font-weight: 400;
            }

            .status {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1rem 1.5rem;
                margin-bottom: 2rem;
                text-align: center;
                transition: all 0.2s ease;
            }

            .status.online {
                border-color: var(--success);
                background: linear-gradient(135deg, rgba(0, 212, 170, 0.05), rgba(0, 212, 170, 0.02));
            }

            .status.offline {
                border-color: var(--error);
                background: linear-gradient(135deg, rgba(244, 67, 54, 0.05), rgba(244, 67, 54, 0.02));
            }

            .status.checking {
                border-color: var(--warning);
                background: linear-gradient(135deg, rgba(255, 167, 38, 0.05), rgba(255, 167, 38, 0.02));
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.8; }
            }

            .chat-interface {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 16px;
                overflow: hidden;
                margin-bottom: 2rem;
                backdrop-filter: blur(20px);
            }

            .chat-messages {
                height: 480px;
                overflow-y: auto;
                padding: 2rem;
                background: linear-gradient(180deg, var(--background), var(--surface));
            }

            .chat-messages::-webkit-scrollbar {
                width: 3px;
            }

            .chat-messages::-webkit-scrollbar-track {
                background: transparent;
            }

            .chat-messages::-webkit-scrollbar-thumb {
                background: var(--border);
                border-radius: 2px;
            }

            .message {
                margin-bottom: 2rem;
                opacity: 0;
                animation: messageSlide 0.4s cubic-bezier(0.2, 0, 0.2, 1) forwards;
            }

            @keyframes messageSlide {
                from { 
                    opacity: 0; 
                    transform: translateY(20px) scale(0.98); 
                }
                to { 
                    opacity: 1; 
                    transform: translateY(0) scale(1); 
                }
            }

            .message.user {
                text-align: right;
            }

            .message.assistant {
                text-align: left;
            }

            .message-content {
                display: inline-block;
                max-width: 75%;
                padding: 1.25rem 1.5rem;
                border-radius: 24px;
                font-size: 0.95rem;
                line-height: 1.6;
                position: relative;
            }

            .message.user .message-content {
                background: linear-gradient(135deg, var(--primary), var(--primary-dark));
                color: #ffffff;
                border-bottom-right-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 102, 255, 0.2);
            }

            .message.assistant .message-content {
                background: var(--surface-elevated);
                color: var(--text);
                border-bottom-left-radius: 8px;
                border: 1px solid var(--border);
            }

            .message-meta {
                font-size: 0.75rem;
                color: var(--text-muted);
                margin-top: 0.5rem;
                font-weight: 500;
            }

            .sources {
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid var(--border);
                font-size: 0.8rem;
                color: var(--text-secondary);
            }

            .sources span {
                display: inline-block;
                background: rgba(0, 102, 255, 0.1);
                border: 1px solid rgba(0, 102, 255, 0.2);
                padding: 0.25rem 0.75rem;
                border-radius: 6px;
                margin: 0.25rem 0.5rem 0.25rem 0;
                font-weight: 500;
                font-size: 0.75rem;
            }

            .input-area {
                padding: 2rem;
                background: linear-gradient(180deg, var(--surface), var(--surface-elevated));
                border-top: 1px solid var(--border);
            }

            .input-container {
                display: flex;
                gap: 1rem;
                align-items: stretch;
            }

            .input-field {
                flex: 1;
                padding: 1rem 1.5rem;
                background: var(--background);
                border: 2px solid var(--border);
                border-radius: 28px;
                color: var(--text);
                font-size: 0.95rem;
                outline: none;
                transition: all 0.2s cubic-bezier(0.2, 0, 0.2, 1);
                font-weight: 400;
            }

            .input-field:focus {
                border-color: var(--primary);
                box-shadow: 0 0 0 4px var(--border-focus);
                background: var(--surface);
            }

            .input-field::placeholder {
                color: var(--text-muted);
                font-weight: 400;
            }

            .send-button {
                padding: 1rem 2rem;
                background: linear-gradient(135deg, var(--primary), var(--primary-dark));
                color: #ffffff;
                border: none;
                border-radius: 28px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s cubic-bezier(0.2, 0, 0.2, 1);
                font-size: 0.95rem;
                box-shadow: 0 4px 12px rgba(0, 102, 255, 0.2);
            }

            .send-button:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(0, 102, 255, 0.3);
            }

            .send-button:active {
                transform: translateY(0);
            }

            .send-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
                box-shadow: 0 4px 12px rgba(0, 102, 255, 0.1);
            }

            .examples {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            }

            .example {
                background: linear-gradient(135deg, var(--surface), var(--surface-elevated));
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1.5rem;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.2, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }

            .example::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(0, 102, 255, 0.05), transparent);
                transition: left 0.5s ease;
            }

            .example:hover::before {
                left: 100%;
            }

            .example:hover {
                border-color: var(--primary);
                transform: translateY(-4px);
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
                background: linear-gradient(135deg, var(--surface-elevated), var(--surface));
            }

            .example-title {
                font-weight: 600;
                color: var(--text);
                margin-bottom: 0.5rem;
                font-size: 0.95rem;
            }

            .example-desc {
                font-size: 0.85rem;
                color: var(--text-secondary);
                font-weight: 400;
            }

            .loading {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--text-secondary);
                font-weight: 500;
            }

            .loading::after {
                content: '';
                width: 14px;
                height: 14px;
                border: 2px solid currentColor;
                border-top-color: transparent;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            .visualization-container {
                margin: 1.5rem 0;
                background: var(--surface-elevated);
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid var(--border);
            }

            .welcome {
                text-align: center;
                padding: 4rem 2rem;
                color: var(--text-secondary);
            }

            .welcome h3 {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: var(--text);
            }

            .welcome p {
                font-size: 0.95rem;
                font-weight: 400;
            }

            @media (max-width: 768px) {
                .container {
                    padding: 1rem;
                }
                
                .header h1 {
                    font-size: 1.75rem;
                }
                
                .chat-messages {
                    height: 400px;
                    padding: 1.5rem;
                }
                
                .message-content {
                    max-width: 85%;
                    padding: 1rem 1.25rem;
                }
                
                .input-area {
                    padding: 1.5rem;
                }
                
                .input-container {
                    flex-direction: column;
                    gap: 0.75rem;
                }
                
                .send-button {
                    align-self: stretch;
                }
                
                .examples {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><span class="brand">Web3</span> Research Co-Pilot</h1>
                <p>Professional cryptocurrency analysis and market intelligence</p>
            </div>

            <div id="status" class="status checking">
                <span>Initializing research systems...</span>
            </div>

            <div class="chat-interface">
                <div id="chatMessages" class="chat-messages">
                    <div class="welcome">
                        <h3>Welcome to Web3 Research Co-Pilot</h3>
                        <p>Ask about market trends, DeFi protocols, or blockchain analytics</p>
                    </div>
                </div>
                <div class="input-area">
                    <div class="input-container">
                        <input 
                            type="text" 
                            id="queryInput" 
                            class="input-field"
                            placeholder="Research Bitcoin trends, analyze DeFi yields, compare protocols..."
                            maxlength="500"
                        >
                        <button id="sendBtn" class="send-button">Research</button>
                    </div>
                </div>
            </div>

            <div class="examples">
                <div class="example" onclick="setQuery('Analyze Bitcoin price trends and institutional adoption patterns')">
                    <div class="example-title">Market Analysis</div>
                    <div class="example-desc">Bitcoin trends, institutional flows, and market sentiment</div>
                </div>
                <div class="example" onclick="setQuery('Compare top DeFi protocols by TVL, yield, and risk metrics')">
                    <div class="example-title">DeFi Intelligence</div>
                    <div class="example-desc">Protocol comparison, yield analysis, and risk assessment</div>
                </div>
                <div class="example" onclick="setQuery('Evaluate Ethereum Layer 2 scaling solutions and adoption metrics')">
                    <div class="example-title">Layer 2 Research</div>
                    <div class="example-desc">Scaling solutions, transaction costs, and ecosystem growth</div>
                </div>
                <div class="example" onclick="setQuery('Identify optimal yield farming strategies across multiple chains')">
                    <div class="example-title">Yield Optimization</div>
                    <div class="example-desc">Cross-chain opportunities, APY tracking, and risk analysis</div>
                </div>
            </div>
        </div>

        <script>
            let chatHistory = [];
            let messageCount = 0;

            async function checkStatus() {
                try {
                    const response = await fetch('/status');
                    const status = await response.json();
                    
                    const statusDiv = document.getElementById('status');
                    
                    if (status.enabled && status.gemini_configured) {
                        statusDiv.className = 'status online';
                        statusDiv.innerHTML = `
                            <span>Research systems online</span>
                            <div style="margin-top: 0.5rem; font-size: 0.85rem; opacity: 0.8;">
                                Tools: ${status.tools_available.join(' • ')}
                            </div>
                        `;
                    } else {
                        statusDiv.className = 'status offline';
                        statusDiv.innerHTML = `
                            <span>Limited mode - Configure GEMINI_API_KEY for full functionality</span>
                            <div style="margin-top: 0.5rem; font-size: 0.85rem; opacity: 0.8;">
                                Available: ${status.tools_available.join(' • ')}
                            </div>
                        `;
                    }
                } catch (error) {
                    const statusDiv = document.getElementById('status');
                    statusDiv.className = 'status offline';
                    statusDiv.innerHTML = '<span>Connection error</span>';
                }
            }

            async function sendQuery() {
                const input = document.getElementById('queryInput');
                const sendBtn = document.getElementById('sendBtn');
                const query = input.value.trim();

                if (!query) {
                    console.log('❌ Empty query, not sending');
                    return;
                }

                console.log('📤 Sending query:', query);
                addMessage('user', query);
                input.value = '';

                // Update button state
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<span class="loading">Processing</span>';

                try {
                    console.log('🔄 Making API request...');
                    const requestStart = Date.now();
                    
                    const response = await fetch('/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, chat_history: chatHistory })
                    });

                    const requestTime = Date.now() - requestStart;
                    console.log(`⏱️ Request completed in ${requestTime}ms`);

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const result = await response.json();
                    console.log('📥 Response received:', {
                        success: result.success,
                        responseLength: result.response?.length || 0,
                        sources: result.sources?.length || 0,
                        visualizations: result.visualizations?.length || 0
                    });

                    if (result.success) {
                        addMessage('assistant', result.response, result.sources, result.visualizations);
                        console.log('✅ Message added successfully');
                    } else {
                        console.error('❌ Query failed:', result.error);
                        addMessage('assistant', result.response || 'Analysis failed. Please try again.', [], []);
                    }
                } catch (error) {
                    console.error('💥 Request error:', error);
                    addMessage('assistant', `Connection error: ${error.message}. Please check your network and try again.`);
                } finally {
                    // Reset button state
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = 'Research';
                    input.focus();
                    console.log('🔄 Button state reset');
                }
            }

            function addMessage(sender, content, sources = [], visualizations = []) {
                const messagesDiv = document.getElementById('chatMessages');
                
                // Clear welcome message
                if (messageCount === 0) {
                    messagesDiv.innerHTML = '';
                }
                messageCount++;

                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;

                let sourcesHtml = '';
                if (sources && sources.length > 0) {
                    sourcesHtml = `
                        <div class="sources">
                            Sources: ${sources.map(s => `<span>${s}</span>`).join('')}
                        </div>
                    `;
                }

                let visualizationHtml = '';
                if (visualizations && visualizations.length > 0) {
                    visualizationHtml = visualizations.map(viz => 
                        `<div class="visualization-container">${viz}</div>`
                    ).join('');
                }

                messageDiv.innerHTML = `
                    <div class="message-content">
                        ${content.replace(/\n/g, '<br>')}
                        ${sourcesHtml}
                    </div>
                    ${visualizationHtml}
                    <div class="message-meta">${new Date().toLocaleTimeString()}</div>
                `;

                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                chatHistory.push({ role: sender, content });
                if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);
            }

            function setQuery(query) {
                document.getElementById('queryInput').value = query;
                setTimeout(() => sendQuery(), 100);
            }

            // Event listeners
            document.getElementById('queryInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendQuery();
            });

            document.getElementById('sendBtn').addEventListener('click', sendQuery);

            // Initialize
            document.addEventListener('DOMContentLoaded', () => {
                checkStatus();
                document.getElementById('queryInput').focus();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/status")
async def get_status():
    """System status endpoint"""
    status = {
        "enabled": service.enabled,
        "gemini_configured": bool(config.GEMINI_API_KEY),
        "tools_available": ["Market Data", "DeFi Analytics", "Network Metrics"],
        "airaa_enabled": service.airaa.enabled if service.airaa else False,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }
    return status

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process research query with detailed logging"""
    # Log incoming request
    logger.info(f"📥 Query received: {request.query[:100]}...")
    logger.info(f"📊 Chat history length: {len(request.chat_history) if request.chat_history else 0}")
    
    start_time = datetime.now()
    
    try:
        # Process the query
        result = await service.process_query(request.query)
        
        # Log result
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Query processed in {processing_time:.2f}s - Success: {result.success}")
        
        if result.success:
            logger.info(f"📤 Response length: {len(result.response)} chars")
            logger.info(f"🔗 Sources: {result.sources}")
            if result.visualizations:
                logger.info(f"📈 Visualizations: {len(result.visualizations)} charts")
        else:
            logger.error(f"❌ Query failed: {result.error}")
        
        return result
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"💥 Query processing exception after {processing_time:.2f}s: {e}")
        
        return QueryResponse(
            success=False,
            response=f"System error: {str(e)}",
            error=str(e)
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service_enabled": service.enabled,
        "version": "2.0.0"
    }

@app.get("/debug/tools")
async def debug_tools():
    """Debug endpoint to test tool availability and functionality"""
    try:
        if not service.enabled or not service.agent:
            return {
                "success": False,
                "error": "AI agent not enabled",
                "tools_available": False,
                "gemini_configured": bool(config.GEMINI_API_KEY)
            }
        
        tools_info = []
        for tool in service.agent.tools:
            tools_info.append({
                "name": tool.name,
                "description": getattr(tool, 'description', 'No description'),
                "enabled": getattr(tool, 'enabled', True)
            })
        
        # Test a simple API call
        test_result = None
        try:
            test_result = await service.process_query("What is the current Bitcoin price?")
        except Exception as e:
            test_result = {"error": str(e)}
        
        return {
            "success": True,
            "tools_count": len(service.agent.tools),
            "tools_info": tools_info,
            "test_query_result": {
                "success": test_result.success if hasattr(test_result, 'success') else False,
                "response_length": len(test_result.response) if hasattr(test_result, 'response') else 0,
                "sources": test_result.sources if hasattr(test_result, 'sources') else [],
                "error": test_result.error if hasattr(test_result, 'error') else None
            },
            "gemini_configured": bool(config.GEMINI_API_KEY),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Debug tools error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Web3 Research Co-Pilot...")
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
