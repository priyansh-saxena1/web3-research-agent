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

# 🚀 Web3 Research Co-Pilot

AI-powered cryptocurrency research assistant with real-time Web3 data analysis.

**Live Demo**: https://archcoder-web3-copilot.hf.space

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key**:
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key"
   ```

3. **Run**:
   ```bash
   python app.py
   ```

4. **Open**: http://localhost:7860

## Features

- 🤖 **AI Analysis** with Google Gemini
- 📊 **Real-time Data** from CoinGecko, DeFiLlama, Etherscan
- 📈 **Interactive Charts** and visualizations
- 💼 **Professional UI** with FastAPI

## API Keys

- **Required**: [GEMINI_API_KEY](https://aistudio.google.com/) 
- **Optional**: COINGECKO_API_KEY, ETHERSCAN_API_KEY

## Deploy to HuggingFace Spaces

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git push hf main
```

## Usage Examples

- "What's Bitcoin's current price?"
- "Show top DeFi protocols by TVL"
- "Analyze Ethereum gas prices"
- "Compare BTC vs ETH performance"

---

Built with ❤️ for Web3 research
