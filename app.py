from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime
import time
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
            logger.info("Initializing Web3 Research Service...")
            
            if config.GEMINI_API_KEY:
                logger.info("AI research capabilities enabled")
                self.agent = Web3ResearchAgent()
                self.enabled = self.agent.enabled
            else:
                logger.info("AI research capabilities disabled - API key required")
                self.agent = None
                self.enabled = False
            
            # Initialize integrations
            logger.info("Initializing external integrations...")
            try:
                self.airaa = AIRAAIntegration()
            except Exception as e:
                logger.warning("External integration unavailable")
                self.airaa = None
            
            # Initialize visualization tools
            try:
                self.viz = CryptoVisualizations()
            except Exception as e:
                logger.warning("Visualization tools unavailable")
                self.viz = None
                
            logger.info(f"Service initialized successfully (AI enabled: {self.enabled})")
            
        except Exception as e:
            logger.error(f"Service initialization failed")
            self.enabled = False
            self.agent = None
            self.airaa = None
            self.viz = None
    
    async def process_query(self, query: str) -> QueryResponse:
        """Process research query with comprehensive analysis"""
        logger.info("Processing research request...")
        
        if not query.strip():
            logger.warning("Empty query received")
            return QueryResponse(
                success=False,
                response="Please provide a research query.", 
                error="Empty query"
            )
            
        try:
            if not self.enabled:
                logger.info("Processing in limited mode")
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
                
                # Check for chart data and generate visualizations
                visualizations = []
                chart_data = await self._extract_chart_data_from_response(response)
                if chart_data:
                    chart_html = await self._generate_chart_from_data(chart_data)
                    if chart_html:
                        visualizations.append(chart_html)
                        logger.info("✅ Chart generated from structured data")
                
                # Clean the response for user display
                cleaned_response = self._clean_agent_response(response)
                    
                # Generate visualizations if relevant data is available  
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
                    response=cleaned_response, 
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
    
    async def _extract_chart_data_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract chart data JSON from agent response"""
        try:
            import re
            import json
            
            logger.info(f"🔍 Checking response for chart data (length: {len(response)} chars)")
            
            # Look for JSON objects containing chart_type - find opening brace and matching closing brace
            chart_data_found = None
            lines = response.split('\n')
            
            for i, line in enumerate(lines):
                if '"chart_type"' in line and line.strip().startswith('{'):
                    # Found potential start of chart JSON
                    json_start = i
                    brace_count = 0
                    json_lines = []
                    
                    for j in range(i, len(lines)):
                        current_line = lines[j]
                        json_lines.append(current_line)
                        
                        # Count braces to find matching close
                        brace_count += current_line.count('{') - current_line.count('}')
                        
                        if brace_count == 0:
                            # Found complete JSON object
                            json_text = '\n'.join(json_lines)
                            try:
                                chart_data = json.loads(json_text.strip())
                                if chart_data.get("chart_type") and chart_data.get("chart_type") != "error":
                                    logger.info(f"✅ Found valid chart data: {chart_data.get('chart_type')}")
                                    return chart_data
                            except json.JSONDecodeError:
                                # Try without newlines
                                try:
                                    json_text_clean = json_text.replace('\n', '').replace('  ', ' ')
                                    chart_data = json.loads(json_text_clean)
                                    if chart_data.get("chart_type") and chart_data.get("chart_type") != "error":
                                        logger.info(f"✅ Found valid chart data (cleaned): {chart_data.get('chart_type')}")
                                        return chart_data
                                except json.JSONDecodeError:
                                    continue
                            break
            
            # Fallback to original regex approach for single-line JSON
            json_pattern = r'\{[^{}]*"chart_type"[^{}]*\}|\{(?:[^{}]|\{[^{}]*\})*"chart_type"(?:[^{}]|\{[^{}]*\})*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            logger.info(f"   Found {len(matches)} potential chart data objects")
            
            for match in matches:
                try:
                    # Clean up the JSON
                    cleaned_match = match.replace('\\"', '"').replace('\\n', '\n')
                    chart_data = json.loads(cleaned_match)
                    
                    if chart_data.get("chart_type") and chart_data.get("chart_type") != "error":
                        logger.info(f"✅ Valid chart data found: {chart_data.get('chart_type')}")
                        return chart_data
                        
                except json.JSONDecodeError:
                    continue
                    
            logger.info("⚠️ No valid chart data found in response")
            return None
            
        except Exception as e:
            logger.error(f"Chart data extraction error: {e}")
            return None
    
    async def _generate_chart_from_data(self, chart_data: Dict[str, Any]) -> Optional[str]:
        """Generate HTML visualization from chart data"""
        try:
            if not self.viz:
                logger.warning("Visualization tools not available")
                return None
                
            chart_type = chart_data.get("chart_type")
            data = chart_data.get("data", {})
            config = chart_data.get("config", {})
            
            logger.info(f"Generating {chart_type} chart with data keys: {list(data.keys())}")
            
            if chart_type == "price_chart":
                fig = self.viz.create_price_chart(data, data.get("symbol", "BTC"))
            elif chart_type == "market_overview":
                fig = self.viz.create_market_overview(data.get("coins", []))
            elif chart_type == "defi_tvl":
                fig = self.viz.create_defi_tvl_chart(data.get("protocols", []))
            elif chart_type == "portfolio_pie":
                # Convert allocation data to the expected format
                allocations = {item["name"]: item["value"] for item in data.get("allocations", [])}
                fig = self.viz.create_portfolio_pie_chart(allocations)
            elif chart_type == "gas_tracker":
                fig = self.viz.create_gas_tracker(data)
            else:
                logger.warning(f"Unknown chart type: {chart_type}")
                return None
                
            # Convert to HTML - use div_id and config for embedding
            chart_id = f'chart_{chart_type}_{int(time.time())}'
            
            # Generate HTML with inline Plotly for reliable rendering
            html = fig.to_html(
                include_plotlyjs='inline',  # Embed Plotly directly - no CDN issues
                div_id=chart_id,
                config={'responsive': True, 'displayModeBar': False}
            )
            
            # With inline Plotly, we need to extract the body content only
            import re
            # Extract everything between <body> and </body>
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
            if body_match:
                chart_html = body_match.group(1).strip()
                logger.info(f"✅ Chart HTML generated ({len(chart_html)} chars) - inline format")
                return chart_html
            else:
                # Fallback - return the full HTML minus the html/head/body tags
                # Remove full document structure, keep only the content
                cleaned_html = re.sub(r'<html[^>]*>.*?<body[^>]*>', '', html, flags=re.DOTALL)
                cleaned_html = re.sub(r'</body>.*?</html>', '', cleaned_html, flags=re.DOTALL)
                logger.info(f"✅ Chart HTML generated ({len(cleaned_html)} chars) - cleaned format")
                return cleaned_html.strip()
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return None
    def _clean_agent_response(self, response: str) -> str:
        """Clean agent response by removing JSON data blocks"""
        try:
            import re
            
            # Method 1: Remove complete JSON objects with balanced braces that contain chart_type
            lines = response.split('\n')
            cleaned_lines = []
            skip_mode = False
            brace_count = 0
            
            for line in lines:
                if not skip_mode:
                    if '"chart_type"' in line and line.strip().startswith('{'):
                        # Found start of chart JSON - start skipping
                        skip_mode = True
                        brace_count = line.count('{') - line.count('}')
                        if brace_count == 0:
                            # Single line JSON, skip this line
                            skip_mode = False
                        continue
                    else:
                        cleaned_lines.append(line)
                else:
                    # In skip mode - count braces to find end
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        # Found end of JSON block
                        skip_mode = False
                    # Skip this line in any case
            
            cleaned = '\n'.join(cleaned_lines)
            
            # Method 2: Fallback regex for any remaining JSON patterns
            json_patterns = [
                r'\{[^{}]*"chart_type"[^{}]*\}',  # Simple single-line JSON
                r'```json\s*\{.*?"chart_type".*?\}\s*```',  # Markdown JSON blocks
            ]
            
            for pattern in json_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
            
            # Clean up extra whitespace
            cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
            cleaned = cleaned.strip()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Response cleaning error: {e}")
            return response

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
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        
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
            
            [data-theme="light"] {
                --background: #ffffff;
                --surface: #f8f9fa;
                --surface-elevated: #ffffff;
                --text: #1a1a1a;
                --text-secondary: #4a5568;
                --text-muted: #718096;
                --border: rgba(0, 0, 0, 0.08);
                --border-focus: rgba(0, 102, 255, 0.3);
                --shadow: rgba(0, 0, 0, 0.1);
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
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
            .header-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 100%;
            }
            .header-text {
                flex: 1;
                text-align: center;
            }
            .theme-toggle {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 0.75rem;
                color: var(--text);
                cursor: pointer;
                transition: all 0.2s ease;
                font-size: 1.1rem;
                min-width: 44px;
                height: 44px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .theme-toggle:hover {
                background: var(--surface-elevated);
                border-color: var(--primary);
                transform: translateY(-1px);
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
            .message-content h1, .message-content h2, .message-content h3, .message-content h4 {
                color: var(--accent);
                margin: 1.25rem 0 0.5rem 0;
                font-weight: 600;
                line-height: 1.3;
            }
            .message-content h1 { font-size: 1.25rem; }
            .message-content h2 { font-size: 1.1rem; }
            .message-content h3 { font-size: 1rem; }
            .message-content h4 { font-size: 0.95rem; }
            .message-content p {
                margin: 0.75rem 0;
                line-height: 1.65;
                color: var(--text);
            }
            .message-content ul, .message-content ol {
                margin: 0.75rem 0;
                padding-left: 1.5rem;
                line-height: 1.6;
            }
            .message-content li {
                margin: 0.3rem 0;
                line-height: 1.6;
            }
            .message-content table {
                width: 100%;
                border-collapse: collapse;
                margin: 1rem 0;
                font-size: 0.9rem;
            }
            .message-content th, .message-content td {
                border: 1px solid var(--border);
                padding: 0.5rem 0.75rem;
                text-align: left;
            }
            .message-content th {
                background: var(--surface);
                font-weight: 600;
                color: var(--accent);
            }
            .message-content strong {
                color: var(--accent);
                font-weight: 600;
            }
            .message-content em {
                color: var(--text-secondary);
                font-style: italic;
            }
            .message-content code {
                background: rgba(0, 102, 255, 0.12);
                border: 1px solid rgba(0, 102, 255, 0.25);
                padding: 0.2rem 0.45rem;
                border-radius: 4px;
                font-family: 'SF Mono', Consolas, 'Courier New', monospace;
                font-size: 0.85rem;
                color: var(--accent);
                font-weight: 500;
            }
            .message-content pre {
                background: var(--background);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
                overflow-x: auto;
                font-family: 'SF Mono', Consolas, 'Courier New', monospace;
                font-size: 0.85rem;
                line-height: 1.5;
            }
            .message-content pre code {
                background: none;
                border: none;
                padding: 0;
                font-size: inherit;
            }
            .message-content blockquote {
                border-left: 3px solid var(--accent);
                padding-left: 1rem;
                margin: 1rem 0;
                color: var(--text-secondary);
                font-style: italic;
                background: rgba(0, 212, 170, 0.05);
                padding: 0.75rem 0 0.75rem 1rem;
                border-radius: 0 4px 4px 0;
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
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .example-title i {
                color: var(--primary);
                font-size: 1rem;
                width: 20px;
                text-align: center;
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
            .loading-indicator {
                display: none;
                background: var(--surface-elevated);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                text-align: center;
                color: var(--text-secondary);
            }
            .loading-indicator.active {
                display: block;
            }
            .loading-spinner {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 2px solid var(--border);
                border-top-color: var(--primary);
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 0.5rem;
            }
            .status-indicator {
                position: fixed;
                top: 20px;
                right: 20px;
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 0.75rem 1rem;
                font-size: 0.85rem;
                color: var(--text-secondary);
                opacity: 0;
                transform: translateY(-10px);
                transition: all 0.3s ease;
                z-index: 1000;
            }
            .status-indicator.show {
                opacity: 1;
                transform: translateY(0);
            }
            .status-indicator.processing {
                border-color: var(--primary);
                background: linear-gradient(135deg, rgba(0, 102, 255, 0.05), rgba(0, 102, 255, 0.02));
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
                
                .header-content {
                    flex-direction: column;
                    gap: 1rem;
                }
                
                .header-text {
                    text-align: center;
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
        <div id="statusIndicator" class="status-indicator">
            <span id="statusText">Ready</span>
        </div>
        
        <div class="container">
            <div class="header">
                <div class="header-content">
                    <div class="header-text">
                        <h1><span class="brand">Web3</span> Research Co-Pilot</h1>
                        <p>Professional cryptocurrency analysis and market intelligence</p>
                    </div>
                    <button id="themeToggle" class="theme-toggle" title="Toggle theme">
                        <i class="fas fa-moon"></i>
                    </button>
                </div>
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
                <div id="loadingIndicator" class="loading-indicator">
                    <div class="loading-spinner"></div>
                    <span id="loadingText">Processing your research query...</span>
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
                    <div class="example-title"><i class="fas fa-chart-line"></i> Market Analysis</div>
                    <div class="example-desc">Bitcoin trends, institutional flows, and market sentiment analysis</div>
                </div>
                <div class="example" onclick="setQuery('Compare top DeFi protocols by TVL, yield, and risk metrics across chains')">
                    <div class="example-title"><i class="fas fa-coins"></i> DeFi Intelligence</div>
                    <div class="example-desc">Protocol comparison, yield analysis, and cross-chain opportunities</div>
                </div>
                <div class="example" onclick="setQuery('Evaluate Ethereum Layer 2 scaling solutions and adoption metrics')">
                    <div class="example-title"><i class="fas fa-layer-group"></i> Layer 2 Research</div>
                    <div class="example-desc">Scaling solutions, transaction costs, and ecosystem growth</div>
                </div>
                <div class="example" onclick="setQuery('Find optimal yield farming strategies with risk assessment')">
                    <div class="example-title"><i class="fas fa-seedling"></i> Yield Optimization</div>
                    <div class="example-desc">Cross-chain opportunities, APY tracking, and risk analysis</div>
                </div>
                <div class="example" onclick="setQuery('Track whale movements and large Bitcoin transactions today')">
                    <div class="example-title"><i class="fas fa-fish"></i> Whale Tracking</div>
                    <div class="example-desc">Large transactions, wallet analysis, and market impact</div>
                </div>
                <div class="example" onclick="setQuery('Analyze gas fees and network congestion across blockchains')">
                    <div class="example-title"><i class="fas fa-tachometer-alt"></i> Network Analytics</div>
                    <div class="example-desc">Gas prices, network utilization, and cost comparisons</div>
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
                const loadingIndicator = document.getElementById('loadingIndicator');
                const statusIndicator = document.getElementById('statusIndicator');
                const statusText = document.getElementById('statusText');
                const query = input.value.trim();

                if (!query) {
                    showStatus('Please enter a research query', 'warning');
                    return;
                }

                console.log('Sending research query');
                addMessage('user', query);
                input.value = '';

                // Update UI states
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<span class="loading">Processing</span>';
                loadingIndicator.classList.add('active');
                showStatus('Processing research query...', 'processing');

                try {
                    console.log('Making API request...');
                    const requestStart = Date.now();
                    
                    const response = await fetch('/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, chat_history: chatHistory })
                    });

                    const requestTime = Date.now() - requestStart;
                    console.log(`Request completed in ${requestTime}ms`);

                    if (!response.ok) {
                        throw new Error(`Request failed with status ${response.status}`);
                    }

                    const result = await response.json();
                    console.log('Response received successfully');

                    if (result.success) {
                        addMessage('assistant', result.response, result.sources, result.visualizations);
                        showStatus('Research complete', 'success');
                        console.log('Analysis completed successfully');
                    } else {
                        console.log('Analysis request failed');
                        addMessage('assistant', result.response || 'Analysis temporarily unavailable. Please try again.', [], []);
                        showStatus('Request failed', 'error');
                    }
                } catch (error) {
                    console.error('Request error occurred');
                    addMessage('assistant', 'Connection error. Please check your network and try again.');
                    showStatus('Connection error', 'error');
                } finally {
                    // Reset UI states
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = 'Research';
                    loadingIndicator.classList.remove('active');
                    input.focus();
                    console.log('Request completed');
                    
                    // Hide status after delay
                    setTimeout(() => hideStatus(), 3000);
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
                    console.log('Processing visualizations:', visualizations.length);
                    visualizationHtml = visualizations.map((viz, index) => {
                        console.log(`Visualization ${index}:`, viz.substring(0, 100));
                        return `<div class="visualization-container" id="viz-${Date.now()}-${index}">${viz}</div>`;
                    }).join('');
                }

                // Format content based on sender
                let formattedContent = content;
                if (sender === 'assistant') {
                    // Convert markdown to HTML for assistant responses
                    try {
                        formattedContent = marked.parse(content);
                    } catch (error) {
                        // Fallback to basic formatting if marked.js fails
                        console.warn('Markdown parsing failed, using fallback:', error);
                        formattedContent = content
                            .replace(/\\n/g, '<br>')
                            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                            .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                            .replace(/`(.*?)`/g, '<code>$1</code>');
                    }
                } else {
                    // Simple line breaks for user messages
                    formattedContent = content.replace(/\\n/g, '<br>');
                }

                messageDiv.innerHTML = `
                    <div class="message-content">
                        ${formattedContent}
                        ${sourcesHtml}
                    </div>
                    ${visualizationHtml}
                    <div class="message-meta">${new Date().toLocaleTimeString()}</div>
                `;

                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                // Execute any scripts in the visualizations after DOM insertion
                if (visualizations && visualizations.length > 0) {
                    console.log('Executing visualization scripts...');
                    setTimeout(() => {
                        const scripts = messageDiv.querySelectorAll('script');
                        console.log(`Found ${scripts.length} scripts to execute`);
                        
                        scripts.forEach((script, index) => {
                            console.log(`Executing script ${index}:`, script.textContent.substring(0, 200) + '...');
                            try {
                                // Execute script in global context using Function constructor
                                const scriptFunction = new Function(script.textContent);
                                scriptFunction.call(window);
                                console.log(`Script ${index} executed successfully`);
                            } catch (error) {
                                console.error(`Script ${index} execution error:`, error);
                                console.error(`Script content preview:`, script.textContent.substring(0, 500));
                            }
                        });
                        console.log('All visualization scripts executed');
                    }, 100);
                }

                chatHistory.push({ role: sender, content });
                if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);
            }

            function setQuery(query) {
                document.getElementById('queryInput').value = query;
                setTimeout(() => sendQuery(), 100);
            }
            
            // Status management functions
            function showStatus(message, type = 'info') {
                const statusIndicator = document.getElementById('statusIndicator');
                const statusText = document.getElementById('statusText');
                
                statusText.textContent = message;
                statusIndicator.className = `status-indicator show ${type}`;
            }
            
            function hideStatus() {
                const statusIndicator = document.getElementById('statusIndicator');
                statusIndicator.classList.remove('show');
            }

            // Theme toggle functionality
            function toggleTheme() {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                const themeIcon = document.querySelector('#themeToggle i');
                
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                
                // Update icon
                if (newTheme === 'light') {
                    themeIcon.className = 'fas fa-sun';
                } else {
                    themeIcon.className = 'fas fa-moon';
                }
            }
            
            // Initialize theme
            function initializeTheme() {
                const savedTheme = localStorage.getItem('theme') || 'dark';
                const themeIcon = document.querySelector('#themeToggle i');
                
                document.documentElement.setAttribute('data-theme', savedTheme);
                
                if (savedTheme === 'light') {
                    themeIcon.className = 'fas fa-sun';
                } else {
                    themeIcon.className = 'fas fa-moon';
                }
            }

            // Event listeners
            document.getElementById('queryInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendQuery();
            });

            document.getElementById('sendBtn').addEventListener('click', (e) => {
                console.log('Research button clicked');
                e.preventDefault();
                sendQuery();
            });
            
            document.getElementById('themeToggle').addEventListener('click', toggleTheme);

            // Initialize
            document.addEventListener('DOMContentLoaded', () => {
                console.log('Application initialized');
                initializeTheme();
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
    """Process research query with sanitized logging"""
    # Log incoming request without exposing sensitive data
    query_preview = request.query[:50] + "..." if len(request.query) > 50 else request.query
    logger.info(f"Query received: {query_preview}")
    
    start_time = datetime.now()
    
    try:
        # Process the query
        result = await service.process_query(request.query)
        
        # Log result without sensitive details
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Query processed in {processing_time:.2f}s - Success: {result.success}")
        
        if result.success:
            logger.info(f"Response generated: {len(result.response)} characters")
        else:
            logger.info("Query processing failed")
        
        return result
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Query processing error after {processing_time:.2f}s")
        
        return QueryResponse(
            success=False,
            response="We're experiencing technical difficulties. Please try again in a moment.",
            error="System temporarily unavailable"
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
