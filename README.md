---
title: Web3 Research Co-Pilot
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
dockerfile: Dockerfile
license: mit
tags:
- cryptocurrency
- blockchain
- defi
- ai-research
- ollama
- llama3
pinned: false
header: default
short_description: AI-powered cryptocurrency research assistant with real-time data
suggested_hardware: t4-medium
---

# Web3 Research Co-Pilot 🚀

An AI-powered cryptocurrency research assistant that provides real-time blockchain analytics, DeFi insights, and market intelligence using Llama 8B and comprehensive API integrations.

## ✨ Features

- **🤖 AI-Powered Analysis**: Uses Llama 8B model via Ollama for intelligent responses
- **🔗 Real-Time Data**: Integrates with CryptoCompare, DeFiLlama, Etherscan APIs
- **🛡️ AI Safety**: Built-in content filtering and safety guardrails
- **📊 Interactive UI**: Modern web interface with dark/light themes
- **⚡ Streaming Responses**: Real-time progress updates during analysis
- **🔄 Comprehensive Tools**: 5+ specialized cryptocurrency research tools

## 🛠️ Technical Stack

- **Backend**: FastAPI with Python 3.11
- **AI Model**: Llama 3 8B via Ollama (local inference)
- **Frontend**: Vanilla JavaScript with modern CSS
- **APIs**: CryptoCompare, DeFiLlama, Etherscan, CoinGecko
- **Safety**: Custom AI safety module with content filtering
- **Deployment**: Docker for HuggingFace Spaces

## 🚀 Usage

Ask questions like:
- "Analyze Bitcoin price trends and institutional adoption patterns"
- "Compare top DeFi protocols by TVL and yield metrics"
- "What are the current Ethereum gas fees?"
- "Track whale movements in Bitcoin today"

## 🔧 Development

### Local Setup
```bash
# Clone the repository
git clone https://huggingface.co/spaces/your-username/web3-research-copilot
cd web3-research-copilot

# Install dependencies
pip install -r requirements.txt

# Start Ollama (in separate terminal)
ollama serve
ollama pull llama3:8b

# Run the application
python app.py
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -f Dockerfile.hf -t web3-copilot .
docker run -p 7860:7860 -p 11434:11434 web3-copilot
```

## 📁 Project Structure

```
├── app.py                 # Main FastAPI application
├── templates/             # HTML templates
├── static/               # CSS and JavaScript files
├── src/
│   ├── agent/            # AI research agent
│   ├── tools/            # API integration tools
│   └── utils/            # Configuration and safety
├── Dockerfile.hf         # HuggingFace Spaces Docker config
└── requirements.txt      # Python dependencies
```

## 🛡️ AI Safety Features

- Input sanitization and validation
- Rate limiting protection
- Content filtering for harmful requests
- Response safety validation
- Comprehensive logging for monitoring

## 📊 Supported APIs

- **CryptoCompare**: Price data and market statistics
- **DeFiLlama**: Protocol TVL and DeFi analytics  
- **Etherscan**: Ethereum network data and gas prices
- **CoinGecko**: Cryptocurrency market data
- **Custom Chart Data**: Historical price analysis

## 🤝 Contributing

This project implements responsible AI practices and focuses on legitimate cryptocurrency research and education.

## 📄 License

MIT License - see LICENSE file for details

---

Built with ❤️ for the crypto research community
