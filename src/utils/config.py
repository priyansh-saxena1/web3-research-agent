import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    # LLM Configuration - Both Ollama and Gemini available
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")  # Enable Gemini when API key provided
    USE_OLLAMA_ONLY: bool = not bool(os.getenv("GEMINI_API_KEY"))  # Auto-detect based on API key
    
    # Available API Keys
    COINGECKO_API_KEY: Optional[str] = None  # Not available - costs money
    CRYPTOCOMPARE_API_KEY: Optional[str] = os.getenv("CRYPTOCOMPARE_API_KEY")  # Available
    ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")  # Available
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"  # Upgraded to Llama 3.1 8B for HF Spaces with 16GB RAM
    USE_OLLAMA_FALLBACK: bool = True
    
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    CRYPTOCOMPARE_BASE_URL: str = "https://min-api.cryptocompare.com/data"
    
    CACHE_TTL: int = 300
    RATE_LIMIT_DELAY: float = 2.0
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    UI_TITLE: str = "Web3 Research Co-Pilot"
    UI_DESCRIPTION: str = "AI-powered crypto research assistant"
    
    AIRAA_WEBHOOK_URL: Optional[str] = os.getenv("AIRAA_WEBHOOK_URL")
    AIRAA_API_KEY: Optional[str] = os.getenv("AIRAA_API_KEY")

config = Config()
