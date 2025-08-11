from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
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

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
            
            # Initialize research agent (supports Ollama-only mode)
            if config.USE_OLLAMA_ONLY or config.GEMINI_API_KEY:
                logger.info("AI research capabilities enabled")
                self.agent = Web3ResearchAgent()
                self.enabled = self.agent.enabled
            else:
                logger.info("AI research capabilities disabled - configuration required")
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
    """Serve the main interface using templates"""
    return templates.TemplateResponse("index.html", {"request": request})
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

@app.post("/query/stream")
async def process_query_stream(request: QueryRequest):
    """Process research query with real-time progress updates"""
    query_preview = request.query[:50] + "..." if len(request.query) > 50 else request.query
    logger.info(f"Streaming query received: {query_preview}")
    
    async def generate_progress():
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Initializing research...', 'progress': 10})}\n\n"
            await asyncio.sleep(0.1)
            
            # Send tool selection status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing query and selecting tools...', 'progress': 20})}\n\n"
            await asyncio.sleep(0.5)
            
            # Send tools status
            if service.agent and service.agent.enabled:
                tools = [tool.name for tool in service.agent.tools]
                yield f"data: {json.dumps({'type': 'tools', 'message': f'Available tools: {tools}', 'progress': 30})}\n\n"
                await asyncio.sleep(0.5)
            
            # Send processing status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Executing tools and gathering data...', 'progress': 50})}\n\n"
            await asyncio.sleep(0.5)
            
            # Send Ollama processing status with heartbeats
            yield f"data: {json.dumps({'type': 'status', 'message': 'Ollama is analyzing data and generating response...', 'progress': 70})}\n\n"
            await asyncio.sleep(1.0)
            
            # Send additional heartbeat messages during processing
            yield f"data: {json.dumps({'type': 'status', 'message': 'Ollama is thinking deeply about your query...', 'progress': 75})}\n\n"
            await asyncio.sleep(2.0)
            
            yield f"data: {json.dumps({'type': 'status', 'message': 'Still processing... Ollama generates detailed responses', 'progress': 80})}\n\n"
            await asyncio.sleep(3.0)
            
            # Process the actual query with timeout and periodic heartbeats
            start_time = datetime.now()
            
            # Create a task for the query processing
            query_task = asyncio.create_task(service.process_query(request.query))
            
            try:
                # Send periodic heartbeats while waiting for Ollama
                heartbeat_count = 0
                while not query_task.done():
                    try:
                        # Wait for either completion or timeout
                        result = await asyncio.wait_for(asyncio.shield(query_task), timeout=10.0)
                        break  # Query completed
                    except asyncio.TimeoutError:
                        # Send heartbeat every 10 seconds
                        heartbeat_count += 1
                        elapsed = (datetime.now() - start_time).total_seconds()
                        
                        if elapsed > 300:  # 5 minute hard timeout
                            query_task.cancel()
                            raise asyncio.TimeoutError("Hard timeout reached")
                        
                        progress = min(85 + (heartbeat_count * 2), 95)  # Progress slowly from 85 to 95
                        yield f"data: {json.dumps({'type': 'status', 'message': f'Ollama is still working... ({elapsed:.0f}s elapsed)', 'progress': progress})}\n\n"
                        
                # If we get here, the query completed successfully
                result = query_task.result()
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Send completion status
                yield f"data: {json.dumps({'type': 'status', 'message': f'Analysis complete ({processing_time:.1f}s)', 'progress': 90})}\n\n"
                await asyncio.sleep(0.5)
                
                # Send final result
                yield f"data: {json.dumps({'type': 'result', 'data': result.dict(), 'progress': 100})}\n\n"
                
            except asyncio.TimeoutError:
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"Query processing timed out after {processing_time:.1f}s")
                
                # Send timeout result with available data
                yield f"data: {json.dumps({'type': 'result', 'data': {'success': False, 'response': 'Analysis timed out, but tools successfully gathered data. The system collected cryptocurrency prices, DeFi protocol information, and blockchain data. Please try a simpler query or try again.', 'sources': [], 'metadata': {'timeout': True, 'processing_time': processing_time}, 'visualizations': [], 'error': 'Processing timeout'}, 'progress': 100})}\n\n"
                
            except Exception as query_error:
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"Query processing failed: {query_error}")
                
                # Send error result
                yield f"data: {json.dumps({'type': 'result', 'data': {'success': False, 'response': f'Analysis failed: {str(query_error)}. The system was able to gather some data but encountered an error during final processing.', 'sources': [], 'metadata': {'error': True, 'processing_time': processing_time}, 'visualizations': [], 'error': str(query_error)}, 'progress': 100})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
        }
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
