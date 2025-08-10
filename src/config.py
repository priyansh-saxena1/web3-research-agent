import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    COINGECKO_API_KEY: Optional[str] = os.getenv("COINGECKO_API_KEY")
    CRYPTOCOMPARE_API_KEY: Optional[str] = os.getenv("CRYPTOCOMPARE_API_KEY")
    
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    CRYPTOCOMPARE_BASE_URL: str = "https://min-api.cryptocompare.com/data"
    
    CACHE_TTL: int = 300
    RATE_LIMIT_DELAY: float = 2.0
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30

config = Config()
