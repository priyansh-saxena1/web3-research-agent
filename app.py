import gradio as gr
import os
import json
from src.enhanced_agent import EnhancedResearchAgent
from src.portfolio_analyzer import portfolio_analyzer
from src.visualizations import create_price_chart, create_market_overview, create_comparison_chart
from src.cache_manager import cache_manager
import asyncio

research_agent = EnhancedResearchAgent()

async def process_research_query(query, history):
    try:
        if not query.strip():
            return history + [["Please enter a research query.", ""]]
        
        response = await research_agent.research_with_context(query)
        return history + [[query, response]]
    except Exception as e:
        error_msg = f"Enhanced research failed: {str(e)}"
        return history + [[query, error_msg]]

def research_query_sync(query, history):
    return asyncio.run(process_research_query(query, history))

async def get_market_data():
    try:
        data = await research_agent.get_comprehensive_market_data()
        chart = create_market_overview(data)
        return chart
    except Exception as e:
        return f"Enhanced market data unavailable: {str(e)}"

def get_market_data_sync():
    return asyncio.run(get_market_data())

async def get_price_chart(symbol):
    try:
        if not symbol.strip():
            return "Please enter a cryptocurrency symbol"
        
        data = await research_agent.get_price_history(symbol)
        chart = create_price_chart(data, symbol)
        return chart
    except Exception as e:
        return f"Chart generation failed: {str(e)}"

def get_price_chart_sync(symbol):
    return asyncio.run(get_price_chart(symbol))

async def analyze_portfolio_async(portfolio_text):
    try:
        if not portfolio_text.strip():
            return "Please enter your portfolio holdings in JSON format"
        
        holdings = json.loads(portfolio_text)
        analysis = await portfolio_analyzer.analyze_portfolio(holdings)
        
        result = f"📊 PORTFOLIO ANALYSIS\n\n"
        result += f"💰 Total Value: ${analysis['total_value']:,.2f}\n"
        result += f"📈 24h Change: ${analysis['change_24h']:+,.2f} ({analysis['change_24h_percentage']:+.2f}%)\n\n"
        
        result += "🏦 ASSET ALLOCATION:\n"
        for asset in analysis['asset_allocation'][:10]:
            result += f"• {asset['name']} ({asset['symbol']}): {asset['percentage']:.1f}% (${asset['value']:,.2f})\n"
        
        result += f"\n⚠️ RISK ASSESSMENT:\n"
        result += f"Overall Risk: {analysis['risk_metrics']['overall_risk']}\n"
        result += f"Diversification Score: {analysis['risk_metrics']['diversification_score']}/10\n"
        result += f"Largest Position: {analysis['risk_metrics']['largest_holding_percentage']:.1f}%\n\n"
        
        result += "💡 RECOMMENDATIONS:\n"
        for i, rec in enumerate(analysis['recommendations'], 1):
            result += f"{i}. {rec}\n"
        
        return result
        
    except json.JSONDecodeError:
        return "❌ Invalid JSON format. Please use format: [{'symbol': 'BTC', 'amount': 1.0}, {'symbol': 'ETH', 'amount': 10.0}]"
    except Exception as e:
        return f"❌ Portfolio analysis failed: {str(e)}"

async def get_defi_analysis_async():
    try:
        data = await research_agent.get_defi_analysis()
        
        result = "🏦 DeFi ECOSYSTEM ANALYSIS\n\n"
        
        if "top_protocols" in data:
            result += "📊 TOP PROTOCOLS BY TVL:\n"
            for i, protocol in enumerate(data["top_protocols"][:10], 1):
                name = protocol.get("name", "Unknown")
                tvl = protocol.get("tvl", 0)
                chain = protocol.get("chain", "Unknown")
                change = protocol.get("change_1d", 0)
                result += f"{i:2d}. {name} ({chain}): ${tvl/1e9:.2f}B TVL ({change:+.2f}%)\n"
        
        if "top_yields" in data:
            result += "\n💰 HIGH YIELD OPPORTUNITIES:\n"
            for i, pool in enumerate(data["top_yields"][:5], 1):
                symbol = pool.get("symbol", "Unknown")
                apy = pool.get("apy", 0)
                tvl = pool.get("tvlUsd", 0)
                result += f"{i}. {symbol}: {apy:.2f}% APY (${tvl/1e6:.1f}M TVL)\n"
        
        return result
        
    except Exception as e:
        return f"❌ DeFi analysis failed: {str(e)}"

def clear_cache():
    cache_manager.clear()
    return "Cache cleared successfully"

def analyze_portfolio_sync(portfolio_text):
    return asyncio.run(analyze_portfolio_async(portfolio_text))

def get_defi_analysis_sync():
    return asyncio.run(get_defi_analysis_async())

with gr.Blocks(
    title="Web3 Research Co-Pilot",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="gray"),
    css="""
    .container { max-width: 1200px; margin: 0 auto; }
    .header { text-align: center; padding: 20px; }
    .chat-container { min-height: 400px; }
    .chart-container { min-height: 500px; }
    """
) as app:
    
    gr.Markdown("# 🚀 Web3 Research Co-Pilot", elem_classes=["header"])
    gr.Markdown("*AI-powered cryptocurrency research with real-time data integration*", elem_classes=["header"])
    
    with gr.Tabs():
        
        with gr.Tab("🤖 Research Chat"):
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        value=[],
                        height=400,
                        elem_classes=["chat-container"],
                        show_label=False
                    )
                    
                    with gr.Row():
                        query_input = gr.Textbox(
                            placeholder="Ask about crypto markets, prices, trends, analysis...",
                            scale=4,
                            show_label=False
                        )
                        submit_btn = gr.Button("Research", variant="primary")
                    
                    gr.Examples(
                        examples=[
                            "What's the current Bitcoin price and trend?",
                            "Compare Ethereum vs Solana DeFi ecosystems",
                            "Analyze top DeFi protocols and TVL trends",
                            "What are the trending coins and latest crypto news?",
                            "Show me high-yield DeFi opportunities with risk analysis"
                        ],
                        inputs=query_input
                    )
                
                with gr.Column(scale=1):
                    gr.Markdown("### 📊 Quick Actions")
                    market_btn = gr.Button("Market Overview", size="sm")
                    market_output = gr.HTML()
                    
                    clear_btn = gr.Button("Clear Cache", size="sm", variant="secondary")
                    clear_output = gr.Textbox(show_label=False, interactive=False)
        
        with gr.Tab("📈 Price Charts"):
            with gr.Row():
                symbol_input = gr.Textbox(
                    label="Cryptocurrency Symbol",
                    placeholder="BTC, ETH, SOL, etc.",
                    value="BTC"
                )
                chart_btn = gr.Button("Generate Chart", variant="primary")
            
            chart_output = gr.HTML(elem_classes=["chart-container"])
            
            gr.Examples(
                examples=["BTC", "ETH", "SOL", "ADA", "DOT"],
                inputs=symbol_input
            )
        
        with gr.Tab("💼 Portfolio Analysis"):
            with gr.Row():
                with gr.Column(scale=1):
                    portfolio_input = gr.Textbox(
                        label="Portfolio Holdings (JSON Format)",
                        placeholder='[{"symbol": "BTC", "amount": 1.0}, {"symbol": "ETH", "amount": 10.0}, {"symbol": "SOL", "amount": 50.0}]',
                        lines=5,
                        info="Enter your crypto holdings in JSON format with symbol and amount"
                    )
                    portfolio_btn = gr.Button("Analyze Portfolio", variant="primary")
                
                with gr.Column(scale=2):
                    portfolio_output = gr.Textbox(
                        label="Portfolio Analysis Results",
                        lines=20,
                        show_copy_button=True,
                        interactive=False
                    )
            
            gr.Examples(
                examples=[
                    '[{"symbol": "BTC", "amount": 0.5}, {"symbol": "ETH", "amount": 5.0}]',
                    '[{"symbol": "BTC", "amount": 1.0}, {"symbol": "ETH", "amount": 10.0}, {"symbol": "SOL", "amount": 100.0}]'
                ],
                inputs=portfolio_input
            )
        
        with gr.Tab("🏦 DeFi Analytics"):
            defi_btn = gr.Button("Get DeFi Ecosystem Analysis", variant="primary", size="lg")
            defi_output = gr.Textbox(
                label="DeFi Analysis Results",
                lines=25,
                show_copy_button=True,
                interactive=False,
                info="Comprehensive DeFi protocol analysis with TVL data and yield opportunities"
            )
        
        with gr.Tab("ℹ️ About"):
            gr.Markdown("""
            ## 🚀 Enhanced Features
            - **Multi-API Integration**: CoinGecko, CryptoCompare, and DeFiLlama data sources
            - **AI-Powered Analysis**: Google Gemini 2.5 Flash with contextual market intelligence
            - **DeFi Analytics**: Protocol TVL analysis, yield farming opportunities, and ecosystem insights
            - **Portfolio Analysis**: Risk assessment, diversification scoring, and personalized recommendations
            - **News Integration**: Real-time crypto news aggregation and sentiment analysis
            - **Interactive Charts**: Advanced price visualizations with technical indicators
            - **Smart Caching**: Optimized performance with intelligent data caching (TTL-based)
            - **Rate Limiting**: Respectful API usage with automatic throttling
            
            ## 🎯 Core Capabilities
            1. **Enhanced Research Chat**: Context-aware conversations with real-time market data integration
            2. **Advanced Price Charts**: Interactive visualizations with 30-day historical data
            3. **Portfolio Optimization**: Comprehensive portfolio analysis with risk metrics and recommendations
            4. **DeFi Intelligence**: Protocol rankings, TVL trends, and high-yield opportunity identification
            5. **Market Intelligence**: Global market metrics, trending assets, and breaking news analysis
            
            ## 💡 Query Examples
            - "Analyze Bitcoin vs Ethereum DeFi ecosystem performance"
            - "What are the top DeFi protocols by TVL with lowest risk?"
            - "Show me high-yield farming opportunities under 15% volatility"
            - "Compare my portfolio risk to market benchmarks"
            - "Latest crypto news impact on altcoin market sentiment"
            - "Which Layer 1 protocols have strongest DeFi adoption?"
            
            ## 🔧 Technical Architecture
            - **Async Processing**: Non-blocking operations for optimal performance
            - **Error Handling**: Comprehensive exception management with graceful degradation
            - **Symbol Mapping**: Intelligent cryptocurrency identifier resolution
            - **Data Validation**: Input sanitization and response formatting
            """)
    
    submit_btn.click(
        research_query_sync,
        inputs=[query_input, chatbot],
        outputs=chatbot
    ).then(lambda: "", outputs=query_input)
    
    query_input.submit(
        research_query_sync,
        inputs=[query_input, chatbot],
        outputs=chatbot
    ).then(lambda: "", outputs=query_input)
    
    chart_btn.click(
        get_price_chart_sync,
        inputs=symbol_input,
        outputs=chart_output
    )
    
    symbol_input.submit(
        get_price_chart_sync,
        inputs=symbol_input,
        outputs=chart_output
    )
    
    market_btn.click(
        get_market_data_sync,
        outputs=market_output
    )
    
    clear_btn.click(
        clear_cache,
        outputs=clear_output
    )
    
    portfolio_btn.click(
        analyze_portfolio_sync,
        inputs=portfolio_input,
        outputs=portfolio_output
    )
    
    defi_btn.click(
        get_defi_analysis_sync,
        outputs=defi_output
    )

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=5000,
        share=False,
        show_error=True
    )
