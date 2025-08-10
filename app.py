import gradio as gr
import asyncio
import json
from datetime import datetime
from typing import List, Tuple

from src.agent.research_agent import Web3ResearchAgent
from src.api.airaa_integration import AIRAAIntegration  
from src.visualizations import create_price_chart, create_market_overview
from src.utils.logger import get_logger
from src.utils.config import config

logger = get_logger(__name__)

class Web3CoPilotApp:
    def __init__(self):
        try:
            self.agent = Web3ResearchAgent()
            self.airaa = AIRAAIntegration()
        except Exception as e:
            logger.error(f"App initialization failed: {e}")
            raise
    
    async def process_query(self, query: str, history: List[Tuple[str, str]]):
        if not query.strip():
            yield history, ""
            return
        
        try:
            history.append((query, "🔍 Researching..."))
            yield history, ""
            
            result = await self.agent.research_query(query)
            
            if result["success"]:
                response = result["result"]
                sources = ", ".join(result.get("sources", []))
                response += f"\n\n---\n📊 **Sources**: {sources}\n⏰ **Generated**: {datetime.now().strftime('%H:%M:%S')}"
                
                if config.AIRAA_WEBHOOK_URL:
                    asyncio.create_task(self.airaa.send_research_data(result))
            else:
                response = f"❌ Error: {result.get('error', 'Research failed')}"
            
            history[-1] = (query, response)
            yield history, ""
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            history[-1] = (query, f"❌ System error: {str(e)}")
            yield history, ""
    
    def get_chart_data(self, symbol: str):
        try:
            if not symbol.strip():
                return "Please enter a symbol"
            
            data = asyncio.run(self.agent.get_price_history(symbol))
            return create_price_chart(data, symbol)
        except Exception as e:
            logger.error(f"Chart error: {e}")
            return f"Chart unavailable: {str(e)}"
    
    def get_market_overview(self):
        try:
            data = asyncio.run(self.agent.get_comprehensive_market_data())
            return create_market_overview(data)
        except Exception as e:
            logger.error(f"Market overview error: {e}")
            return f"Market data unavailable: {str(e)}"
    
    def create_interface(self):
        with gr.Blocks(title=config.UI_TITLE, theme=gr.themes.Soft()) as demo:
            gr.Markdown(f"""
            # 🚀 {config.UI_TITLE}
            {config.UI_DESCRIPTION}
            **Powered by**: Gemini AI • CoinGecko • DeFiLlama • Etherscan
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(label="Research Assistant", height=650)
                    
                    with gr.Row():
                        query_input = gr.Textbox(
                            placeholder="Ask about crypto markets, DeFi protocols, or on-chain data...",
                            label="Research Query", lines=2
                        )
                        submit_btn = gr.Button("🔍 Research", variant="primary")
                    
                    clear_btn = gr.Button("🗑️ Clear", variant="secondary")
                
                with gr.Column(scale=1):
                    gr.Markdown("### 💡 Example Queries")
                    
                    examples = [
                        "Bitcoin price analysis",
                        "Top DeFi protocols by TVL",
                        "Ethereum vs Solana comparison",
                        "Trending cryptocurrencies",
                        "DeFi yield opportunities"
                    ]
                    
                    for example in examples:
                        gr.Button(example, size="sm").click(
                            lambda x=example: x, outputs=query_input
                        )
                    
                    gr.Markdown("### 📈 Visualizations")
                    chart_output = gr.Plot(label="Charts")
                    
                    symbol_input = gr.Textbox(placeholder="BTC, ETH, SOL...", label="Chart Symbol")
                    chart_btn = gr.Button("📊 Generate Chart")
                    
                    market_btn = gr.Button("🌐 Market Overview")
            
            submit_btn.click(
                self.process_query,
                inputs=[query_input, chatbot],
                outputs=[chatbot, query_input]
            )
            
            query_input.submit(
                self.process_query,
                inputs=[query_input, chatbot],
                outputs=[chatbot, query_input]
            )
            
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, query_input])
            
            chart_btn.click(
                self.get_chart_data,
                inputs=symbol_input,
                outputs=chart_output
            )
            
            market_btn.click(
                self.get_market_overview,
                outputs=chart_output
            )
        
        return demo

if __name__ == "__main__":
    app = Web3CoPilotApp()
    interface = app.create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
