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

load_dotenv()

from src.agent.research_agent import Web3ResearchAgent
from src.api.airaa_integration import AIRAAIntegration  
from src.utils.logger import get_logger
from src.utils.config import config

logger = get_logger(__name__)

app = FastAPI(
    title="Web3 Research Co-Pilot",
    description="AI-powered cryptocurrency research assistant",
    version="1.0.0"
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = []

class QueryResponse(BaseModel):
    success: bool
    response: str
    sources: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
    error: Optional[str] = None

class Web3CoPilotService:
    def __init__(self):
        try:
            logger.info("🚀 Initializing Web3CoPilotService...")
            logger.info(f"📋 GEMINI_API_KEY configured: {'Yes' if config.GEMINI_API_KEY else 'No'}")
            
            if config.GEMINI_API_KEY:
                logger.info("🤖 Initializing AI agent...")
                self.agent = Web3ResearchAgent()
                logger.info("✅ AI agent initialized successfully")
            else:
                logger.warning("⚠️ GEMINI_API_KEY not found - AI features disabled")
                self.agent = None
            
            logger.info("🔗 Initializing AIRAA integration...")
            self.airaa = AIRAAIntegration()
            logger.info(f"🔗 AIRAA integration: {'Enabled' if self.airaa.enabled else 'Disabled'}")
            
            self.enabled = bool(config.GEMINI_API_KEY)
            logger.info(f"🎯 Web3CoPilotService initialized successfully (AI enabled: {self.enabled})")
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            self.agent = None
            self.airaa = None
            self.enabled = False
    
    async def process_query(self, query: str) -> QueryResponse:
        logger.info(f"🔍 Processing query: {query[:50]}{'...' if len(query) > 50 else ''}")
        
        if not query.strip():
            logger.warning("⚠️ Empty query received")
            return QueryResponse(success=False, response="Please enter a query.", error="Empty query")
        
        try:
            if not self.enabled:
                logger.info("🔧 AI disabled - providing limited response")
                response = """⚠️ **AI Agent Disabled**: GEMINI_API_KEY not configured.

**Limited Data Available:**
- CoinGecko API (basic crypto data)
- DeFiLlama API (DeFi protocols) 
- Etherscan API (gas prices)

Please configure GEMINI_API_KEY for full AI analysis."""
                return QueryResponse(success=True, response=response, sources=["Configuration"])
            
            logger.info("🤖 Sending query to AI agent...")
            result = await self.agent.research_query(query)
            logger.info(f"✅ AI agent responded: {result.get('success', False)}")
            
            if result.get("success"):
                response = result.get("result", "No response generated")
                sources = result.get("sources", [])
                metadata = result.get("metadata", {})
                
                # Send to AIRAA if enabled
                if self.airaa and self.airaa.enabled:
                    try:
                        logger.info("🔗 Sending data to AIRAA...")
                        await self.airaa.send_research_data(query, response)
                        logger.info("✅ Data sent to AIRAA successfully")
                    except Exception as e:
                        logger.warning(f"⚠️ AIRAA integration failed: {e}")
                
                logger.info("✅ Query processed successfully")
                return QueryResponse(success=True, response=response, sources=sources, metadata=metadata)
            else:
                error_msg = result.get("error", "Research failed. Please try again.")
                logger.error(f"❌ AI agent failed: {error_msg}")
                return QueryResponse(success=False, response=error_msg, error=error_msg)
            
        except Exception as e:
            logger.error(f"❌ Query processing error: {e}")
            error_msg = f"Error processing query: {str(e)}"
            return QueryResponse(success=False, response=error_msg, error=error_msg)

# Initialize service
logger.info("🚀 Starting Web3 Research Co-Pilot...")
service = Web3CoPilotService()

# API Routes
@app.get("/", response_class=HTMLResponse)
async def get_homepage(request: Request):
    logger.info("📄 Serving homepage")
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Web3 Research Co-Pilot</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚀</text></svg>">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif; 
                background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%); 
                color: #e6e6e6; 
                min-height: 100vh;
                overflow-x: hidden;
            }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { 
                text-align: center; 
                margin-bottom: 30px; 
                background: linear-gradient(135deg, #00d4aa, #4a9eff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .header h1 { 
                font-size: 3em; 
                margin-bottom: 10px; 
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .header p { 
                color: #b0b0b0; 
                font-size: 1.2em; 
                font-weight: 300;
            }
            .status { 
                padding: 15px; 
                border-radius: 12px; 
                margin-bottom: 25px; 
                text-align: center; 
                font-weight: 500;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            }
            .status.enabled { 
                background: linear-gradient(135deg, #1a4d3a, #2a5d4a); 
                border: 2px solid #00d4aa; 
                color: #00d4aa; 
            }
            .status.disabled { 
                background: linear-gradient(135deg, #4d1a1a, #5d2a2a); 
                border: 2px solid #ff6b6b; 
                color: #ff6b6b; 
            }
            .status.checking {
                background: linear-gradient(135deg, #3a3a1a, #4a4a2a); 
                border: 2px solid #ffdd59; 
                color: #ffdd59;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            .chat-container { 
                background: rgba(26, 26, 26, 0.8); 
                border-radius: 16px; 
                padding: 25px; 
                margin-bottom: 25px; 
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            .chat-messages { 
                height: 450px; 
                overflow-y: auto; 
                background: rgba(10, 10, 10, 0.6); 
                border-radius: 12px; 
                padding: 20px; 
                margin-bottom: 20px;
                border: 1px solid rgba(255,255,255,0.05);
            }
            .chat-messages::-webkit-scrollbar { width: 6px; }
            .chat-messages::-webkit-scrollbar-track { background: #2a2a2a; border-radius: 3px; }
            .chat-messages::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
            .chat-messages::-webkit-scrollbar-thumb:hover { background: #777; }
            .message { 
                margin-bottom: 20px; 
                padding: 16px; 
                border-radius: 12px; 
                transition: all 0.3s ease;
                position: relative;
            }
            .message:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
            .message.user { 
                background: linear-gradient(135deg, #2a2a3a, #3a3a4a); 
                border-left: 4px solid #00d4aa; 
                margin-left: 50px;
            }
            .message.assistant { 
                background: linear-gradient(135deg, #1a2a1a, #2a3a2a); 
                border-left: 4px solid #4a9eff; 
                margin-right: 50px;
            }
            .message .sender { 
                font-weight: 600; 
                margin-bottom: 8px; 
                font-size: 0.9em; 
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .message.user .sender { color: #00d4aa; }
            .message.assistant .sender { color: #4a9eff; }
            .message .content { line-height: 1.6; }
            .input-container { 
                display: flex; 
                gap: 12px; 
                align-items: stretch;
            }
            .input-container input { 
                flex: 1; 
                padding: 16px; 
                border: 2px solid #333; 
                background: rgba(42, 42, 42, 0.8); 
                color: #e6e6e6; 
                border-radius: 12px; 
                font-size: 16px;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
            }
            .input-container input:focus { 
                outline: none; 
                border-color: #00d4aa; 
                box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.2);
            }
            .input-container input::placeholder { color: #888; }
            .input-container button { 
                padding: 16px 24px; 
                background: linear-gradient(135deg, #00d4aa, #00b894); 
                color: #000; 
                border: none; 
                border-radius: 12px; 
                cursor: pointer; 
                font-weight: 600;
                font-size: 16px;
                transition: all 0.3s ease;
                white-space: nowrap;
            }
            .input-container button:hover:not(:disabled) { 
                background: linear-gradient(135deg, #00b894, #00a085); 
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3);
            }
            .input-container button:active { transform: translateY(0); }
            .input-container button:disabled { 
                background: #666; 
                cursor: not-allowed; 
                transform: none;
                box-shadow: none;
            }
            .examples { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 15px; 
                margin-top: 25px; 
            }
            .example-btn { 
                padding: 16px; 
                background: linear-gradient(135deg, #2a2a3a, #3a3a4a); 
                border: 2px solid #444; 
                border-radius: 12px; 
                cursor: pointer; 
                text-align: center; 
                transition: all 0.3s ease;
                font-weight: 500;
                position: relative;
                overflow: hidden;
            }
            .example-btn:before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(0, 212, 170, 0.1), transparent);
                transition: left 0.5s;
            }
            .example-btn:hover:before { left: 100%; }
            .example-btn:hover { 
                background: linear-gradient(135deg, #3a3a4a, #4a4a5a); 
                border-color: #00d4aa; 
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0, 212, 170, 0.2);
            }
            .loading { 
                color: #ffdd59; 
                font-style: italic; 
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .loading:after {
                content: '';
                width: 12px;
                height: 12px;
                border: 2px solid #ffdd59;
                border-top: 2px solid transparent;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .sources { 
                margin-top: 12px; 
                font-size: 0.85em; 
                color: #999; 
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }
            .sources .label { margin-right: 8px; font-weight: 600; }
            .sources span { 
                background: rgba(51, 51, 51, 0.8); 
                padding: 4px 8px; 
                border-radius: 6px; 
                font-size: 0.8em;
                border: 1px solid #555;
            }
            .welcome-message {
                background: linear-gradient(135deg, #1a2a4a, #2a3a5a);
                border-left: 4px solid #4a9eff;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 20px;
                text-align: center;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Web3 Research Co-Pilot</h1>
                <p>AI-powered cryptocurrency research assistant</p>
            </div>
            
            <div id="status" class="status checking">
                <span>🔄 Checking system status...</span>
            </div>
            
            <div class="chat-container">
                <div id="chatMessages" class="chat-messages">
                    <div class="welcome-message">
                        <div class="sender">🤖 AI Research Assistant</div>
                        <div>👋 Welcome! I'm your Web3 Research Co-Pilot. Ask me anything about cryptocurrency markets, DeFi protocols, blockchain analysis, or trading insights.</div>
                    </div>
                </div>
                <div class="input-container">
                    <input type="text" id="queryInput" placeholder="Ask about Bitcoin, Ethereum, DeFi yields, market analysis..." maxlength="500">
                    <button id="sendBtn" onclick="sendQuery()">🚀 Research</button>
                </div>
            </div>
            
            <div class="examples">
                <div class="example-btn" onclick="setQuery('What is the current Bitcoin price and market sentiment?')">
                    📈 Bitcoin Analysis
                </div>
                <div class="example-btn" onclick="setQuery('Show me the top DeFi protocols by TVL')">
                    🏦 DeFi Overview
                </div>
                <div class="example-btn" onclick="setQuery('What are the trending cryptocurrencies today?')">
                    🔥 Trending Coins
                </div>
                <div class="example-btn" onclick="setQuery('Analyze Ethereum gas prices and network activity')">
                    ⛽ Gas Tracker
                </div>
                <div class="example-btn" onclick="setQuery('Find the best yield farming opportunities')">
                    🌾 Yield Farming
                </div>
                <div class="example-btn" onclick="setQuery('Compare Solana vs Ethereum ecosystems')">
                    ⚖️ Ecosystem Compare
                </div>
            </div>
            
            <div class="footer">
                <p>Powered by AI • Real-time Web3 data • Built with ❤️</p>
            </div>
        </div>
        
        <script>
            let chatHistory = [];
            
            async function checkStatus() {
                try {
                    console.log('🔍 Checking system status...');
                    const response = await fetch('/status');
                    const status = await response.json();
                    console.log('📊 Status received:', status);
                    
                    const statusDiv = document.getElementById('status');
                    
                    if (status.enabled && status.gemini_configured) {
                        statusDiv.className = 'status enabled';
                        statusDiv.innerHTML = `
                            <span>✅ AI Research Agent: Online</span><br>
                            <small>Tools available: ${status.tools_available.join(', ')}</small>
                        `;
                        console.log('✅ System fully operational');
                    } else {
                        statusDiv.className = 'status disabled';
                        statusDiv.innerHTML = `
                            <span>⚠️ Limited Mode: GEMINI_API_KEY not configured</span><br>
                            <small>Basic data available: ${status.tools_available.join(', ')}</small>
                        `;
                        console.log('⚠️ System in limited mode');
                    }
                } catch (error) {
                    console.error('❌ Status check failed:', error);
                    const statusDiv = document.getElementById('status');
                    statusDiv.className = 'status disabled';
                    statusDiv.innerHTML = '<span>❌ Connection Error</span>';
                }
            }
            
            async function sendQuery() {
                const input = document.getElementById('queryInput');
                const sendBtn = document.getElementById('sendBtn');
                const query = input.value.trim();
                
                if (!query) {
                    input.focus();
                    return;
                }
                
                console.log('📤 Sending query:', query);
                
                // Add user message
                addMessage('user', query);
                input.value = '';
                
                // Show loading
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<span class="loading">Processing</span>';
                
                try {
                    const response = await fetch('/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, chat_history: chatHistory })
                    });
                    
                    const result = await response.json();
                    console.log('📥 Response received:', result);
                    
                    if (result.success) {
                        addMessage('assistant', result.response, result.sources);
                        console.log('✅ Query processed successfully');
                    } else {
                        addMessage('assistant', result.response || 'An error occurred');
                        console.log('⚠️ Query failed:', result.error);
                    }
                } catch (error) {
                    console.error('❌ Network error:', error);
                    addMessage('assistant', '❌ Network error. Please check your connection and try again.');
                } finally {
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = '🚀 Research';
                    input.focus();
                }
            }
            
            function addMessage(sender, content, sources = []) {
                console.log(`💬 Adding ${sender} message`);
                const messagesDiv = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                
                let sourcesHtml = '';
                if (sources && sources.length > 0) {
                    sourcesHtml = `<div class="sources"><span class="label">Sources:</span> ${sources.map(s => `<span>${s}</span>`).join('')}</div>`;
                }
                
                const senderIcon = sender === 'user' ? '👤' : '🤖';
                const senderName = sender === 'user' ? 'You' : 'AI Research Assistant';
                
                messageDiv.innerHTML = `
                    <div class="sender">${senderIcon} ${senderName}</div>
                    <div class="content">${content.replace(/\n/g, '<br>')}</div>
                    ${sourcesHtml}
                `;
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
                // Update chat history
                chatHistory.push({ role: sender, content });
                if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);
            }
            
            function setQuery(query) {
                console.log('📝 Setting query:', query);
                const input = document.getElementById('queryInput');
                input.value = query;
                input.focus();
                
                // Optional: auto-send after a short delay
                setTimeout(() => {
                    if (input.value === query) { // Only if user didn't change it
                        sendQuery();
                    }
                }, 100);
            }
            
            // Handle Enter key
            document.getElementById('queryInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendQuery();
                }
            });
            
            // Initialize
            document.addEventListener('DOMContentLoaded', function() {
                console.log('🚀 Web3 Research Co-Pilot initialized');
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
    logger.info("📊 Status endpoint called")
    status = {
        "enabled": service.enabled,
        "gemini_configured": bool(config.GEMINI_API_KEY),
        "tools_available": ["CoinGecko", "DeFiLlama", "Etherscan"],
        "airaa_enabled": service.airaa.enabled if service.airaa else False,
        "timestamp": datetime.now().isoformat()
    }
    logger.info(f"📊 Status response: {status}")
    return status

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    logger.info(f"📥 Query endpoint called: {request.query[:50]}{'...' if len(request.query) > 50 else ''}")
    result = await service.process_query(request.query)
    logger.info(f"📤 Query response: success={result.success}")
    return result

@app.get("/health")
async def health_check():
    logger.info("❤️ Health check endpoint called")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service_enabled": service.enabled,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🌟 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
