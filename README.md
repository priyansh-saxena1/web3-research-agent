# 🚀 Web3 Research Co-Pilot

AI-powered cryptocurrency research assistant with comprehensive Web3 data analysis capabilities.

## Features

- **LangChain AI Agent**: Advanced query processing with Google Gemini
- **Real-time Data**: CoinGecko, DeFiLlama, Etherscan integration  
- **Interactive UI**: Gradio-based chat interface with visualizations
- **AIRAA Integration**: Research data forwarding to external platforms
- **Production Ready**: Comprehensive error handling and async architecture

## Quick Start

### 1. Environment Setup

```bash
export GEMINI_API_KEY="your_gemini_api_key"
export ETHERSCAN_API_KEY="your_etherscan_key"  # Optional
export COINGECKO_API_KEY="your_coingecko_key"  # Optional
```

### 2. Installation

```bash
pip install -r requirements.txt
```

### 3. Launch

```bash
python launch.py
```

## API Keys

- **GEMINI_API_KEY** (Required): [Get from Google AI Studio](https://makersuite.google.com/app/apikey)
- **ETHERSCAN_API_KEY** (Optional): [Get from Etherscan.io](https://etherscan.io/apis)
- **COINGECKO_API_KEY** (Optional): [Get from CoinGecko](https://www.coingecko.com/en/api/pricing)

## Architecture

```
├── app.py                 # Main Gradio application
├── src/
│   ├── agent/            # LangChain AI agent
│   ├── tools/            # Web3 data tools
│   ├── api/              # External integrations
│   └── utils/            # Configuration & utilities
└── launch.py             # Launch script
```

## Usage Examples

- "What is the current price of Bitcoin?"
- "Analyze Ethereum's DeFi ecosystem"
- "Show me gas prices and network stats"
- "Research the top DeFi protocols by TVL"

## Deployment

Configured for HuggingFace Spaces with automatic dependency management.

---

**Built with minimal, expert-level code and production-grade error handling.**

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
