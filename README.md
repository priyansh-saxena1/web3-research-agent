---
title: Web3 Research Co-Pilot
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "latest"
app_file: app.py
pinned: false
---

# Web3 Research Co-Pilot

A professional AI-powered cryptocurrency research assistant that provides real-time market analysis, DeFi intelligence, and blockchain insights through an elegant web interface.

🌐 **Live Demo**: https://archcoder-web3-copilot.hf.space

![Web3 Research Co-Pilot](https://img.shields.io/badge/Web3-Research%20Co--Pilot-0066ff?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green?style=for-the-badge&logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-0.3.0-purple?style=for-the-badge)

## ✨ Features

- **AI-Powered Research**: Advanced LLM analysis using Google Gemini
- **Real-Time Data**: Live market data from CoinGecko, DeFiLlama, and Etherscan
- **Interactive Visualizations**: Dynamic charts and graphs powered by Plotly
- **Professional UI**: Minimalist, responsive web interface
- **Multi-Chain Support**: Ethereum, DeFi protocols, and Layer 2 solutions
- **Comprehensive Analytics**: Market trends, yield optimization, and risk assessment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API Key (required)
- Optional: CoinGecko API Key (for higher rate limits)
- Optional: Etherscan API Key (for blockchain data)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Transcendental-Programmer/web3-research-agent.git
   cd web3-research-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```properties
   # Required
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Optional (for enhanced functionality)
   COINGECKO_API_KEY=your_coingecko_api_key_here
   ETHERSCAN_API_KEY=your_etherscan_api_key_here
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the interface**
   - **Local Development**: http://localhost:7860
   - **Production/Cloud**: Check your hosting platform's port forwarding
   - **Docker**: http://localhost:7860

## 🚀 HuggingFace Spaces Deployment

This project is configured for HuggingFace Spaces deployment with Docker SDK.

### Quick Deploy to HF Spaces

1. **Fork/Clone this repository**
2. **Create a new HuggingFace Space**:
   - Go to [HuggingFace Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose "Docker" as the SDK
   - Upload your repository files

3. **Configure Environment Variables**:
   In your Space settings, add:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   COINGECKO_API_KEY=your_coingecko_api_key  
   ETHERSCAN_API_KEY=your_etherscan_api_key
   ```

4. **Deploy via Git**:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   git push hf main
   ```

### HF Spaces Configuration

The project includes a proper `README.md` header for HF Spaces:
```yaml
title: Web3 Research Co-Pilot
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_file: app.py
```

## 🐳 Docker Deployment

### Local Docker

```bash
# Build the image
docker build -t web3-research-copilot .

# Run the container
docker run -p 7860:7860 \
  -e GEMINI_API_KEY=your_key_here \
  -e COINGECKO_API_KEY=your_key_here \
  -e ETHERSCAN_API_KEY=your_key_here \
  web3-research-copilot
```

### HuggingFace Spaces

This project is optimized for HuggingFace Spaces deployment:

1. **Create a new Space**:
   - Go to [HuggingFace Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose "Docker" as the SDK
   - Set visibility to "Public" or "Private"

2. **Configure Environment Variables**:
   In your Space settings, add:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   COINGECKO_API_KEY=your_coingecko_api_key  
   ETHERSCAN_API_KEY=your_etherscan_api_key
   ```

3. **Deploy**:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   git push hf main
   ```

**Live Example**: https://archcoder-web3-copilot.hf.space

## 🔄 Development Setup

### Adding HuggingFace Remote

To deploy to your HuggingFace Space:

```bash
# Add HuggingFace remote
git remote add hf https://huggingface.co/spaces/ArchCoder/web3-copilot

# Or for your own space
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

# Deploy to HF Spaces
git push hf main
```

## 📊 Testing

Run the comprehensive test suite:

```bash
python test_suite.py
```

Expected output:
```
🚀 Web3 Research Co-Pilot - Test Suite
==================================================
✅ All imports successful
✅ Configuration validated
✅ Visualizations working
✅ Tools initialized
✅ Service functional
✅ API endpoints healthy
✅ Performance acceptable

Tests passed: 7/7
Success rate: 100.0%
🎉 All tests passed!
```

## 🏗️ Project Structure

```
web3-research-agent/
├── app.py                      # Main FastAPI application
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project configuration
├── uv.lock                    # Dependency lock file
├── test_suite.py              # Comprehensive test suite
├── .env.example               # Environment template
├── src/                       # Source code
│   ├── __init__.py
│   ├── research_agent.py      # Main agent logic
│   ├── enhanced_agent.py      # Enhanced agent features
│   ├── config.py              # Configuration management
│   ├── cache_manager.py       # Response caching
│   ├── api_clients.py         # External API clients
│   ├── defillama_client.py    # DeFiLlama integration
│   ├── news_aggregator.py     # News and social data
│   ├── portfolio_analyzer.py  # Portfolio analysis
│   └── visualizations.py      # Chart generation
└── README.md                  # This file
```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key for AI analysis | ✅ |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COINGECKO_API_KEY` | CoinGecko API key for enhanced rate limits | None |
| `ETHERSCAN_API_KEY` | Etherscan API key for blockchain data | None |
| `AIRAA_WEBHOOK_URL` | AIRAA integration webhook URL | None |
| `AIRAA_API_KEY` | AIRAA API authentication key | None |

### Getting API Keys

1. **Google Gemini API**: 
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Create a new API key
   - Copy the key to your `.env` file

2. **CoinGecko API** (optional):
   - Sign up at [CoinGecko](https://www.coingecko.com/api)
   - Get your free API key
   - Provides higher rate limits

3. **Etherscan API** (optional):
   - Register at [Etherscan](https://etherscan.io/apis)
   - Create a free API key
   - Enables blockchain data queries

## 🎯 Usage Examples

### Market Analysis
```
"Analyze Bitcoin price trends and institutional adoption patterns"
```

### DeFi Research
```
"Compare top DeFi protocols by TVL, yield, and risk metrics"
```

### Layer 2 Analysis
```
"Evaluate Ethereum Layer 2 scaling solutions and adoption metrics"
```

### Yield Optimization
```
"Identify optimal yield farming strategies across multiple chains"
```

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/status` | GET | System status and configuration |
| `/query` | POST | Process research queries |
| `/health` | GET | Health check |

### Query API Example

```bash
curl -X POST "http://localhost:7860/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current Bitcoin price?"}'
```

## 🐛 Troubleshooting

### Port Access Issues

**Problem**: Can't access the app on http://localhost:7860 or http://0.0.0.0:7860

**Solutions**:

1. **Check if the app is running**:
   ```bash
   ps aux | grep "python app.py"
   ```

2. **Verify port binding**:
   ```bash
   netstat -tlnp | grep :7860
   ```

3. **For Development Environments (VS Code, etc.)**:
   - Look for port forwarding notifications
   - Check your IDE's "Ports" or "Forwarded Ports" tab
   - Use the forwarded URL provided by your development environment

4. **For Cloud/Remote Environments**:
   - The app binds to `0.0.0.0:7860` for external access
   - Use your platform's provided URL (not localhost)
   - Check firewall rules if on a VPS/server

5. **Local Network Access**:
   ```bash
   # Find your local IP
   hostname -I
   # Access via: http://YOUR_IP:7860
   ```

### Common Issues

1. **"GEMINI_API_KEY not configured"**
   - Ensure you've set the API key in your `.env` file
   - Verify the key is valid and has proper permissions

2. **"Connection refused" on port 7860**
   - Check if another process is using port 7860: `lsof -i :7860`
   - Ensure the app started successfully: `python app.py`

3. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.11+)

4. **Slow visualization loading**
   - Check your internet connection
   - API rate limits may be affecting data retrieval

### Getting Help

- Check the test suite: `python test_suite.py`
- Review logs in the terminal output
- Verify API keys are configured correctly
- Open an issue on GitHub with error details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini** for AI capabilities
- **CoinGecko** for comprehensive market data
- **DeFiLlama** for DeFi protocol analytics
- **Etherscan** for blockchain data
- **FastAPI** for the web framework
- **Plotly** for interactive visualizations

---

**Built with ❤️ for the Web3 community**
