# Web3 Research Co-Pilot

AI-powered cryptocurrency research assistant built with LangChain and Gradio.

## Features

- **Real-time Market Analysis**: CoinGecko, DeFiLlama, Etherscan integration
- **AI Research Agent**: Powered by Google Gemini
- **Interactive Interface**: Modern Gradio UI
- **Data Visualization**: Price charts and market overviews
- **AIRAA Integration**: Webhook support for external platforms

## Quick Start

1. **Clone and Setup**
```bash
git clone <repository-url>
cd web3-research-agent
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run Application**
```bash
python app.py
```

## Required API Keys

- `GEMINI_API_KEY`: Google Gemini AI (required)
- `ETHERSCAN_API_KEY`: Ethereum blockchain data
- `COINGECKO_API_KEY`: Cryptocurrency market data (optional)
- `AIRAA_WEBHOOK_URL`: External integration (optional)

## Deployment

### Docker
```bash
docker build -t web3-research-agent .
docker run -p 7860:7860 --env-file .env web3-research-agent
```

### Hugging Face Spaces
Upload repository to HF Spaces with environment variables configured.

## Architecture

- **Agent**: LangChain-based research agent with memory
- **Tools**: Modular API integrations (CoinGecko, DeFiLlama, Etherscan)
- **UI**: Gradio interface with chat and visualization
- **Cache**: Optimized caching for API responses
- **Integration**: AIRAA webhook support

## Usage Examples

- "Bitcoin price analysis and market sentiment"
- "Top DeFi protocols by TVL"
- "Ethereum gas prices and network stats" 
- "Compare BTC vs ETH performance"

Built with ❤️ for Web3 research
