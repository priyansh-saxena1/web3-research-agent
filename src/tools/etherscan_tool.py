from typing import Dict, Any, Optional
from pydantic import BaseModel, PrivateAttr
from src.tools.base_tool import BaseWeb3Tool, Web3ToolInput
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class EtherscanTool(BaseWeb3Tool):
    name: str = "etherscan_data"
    description: str = """Get Ethereum blockchain data from Etherscan.
    Useful for: transaction analysis, address information, gas prices, token data.
    Input: Ethereum address, transaction hash, or general blockchain query."""
    args_schema: type[BaseModel] = Web3ToolInput
    enabled: bool = True  # Add enabled as a Pydantic field
    
    _base_url: str = PrivateAttr(default="https://api.etherscan.io/api")
    _api_key: Optional[str] = PrivateAttr(default=None)
    
    def __init__(self):
        super().__init__()
        self._api_key = config.ETHERSCAN_API_KEY
        self.enabled = bool(self._api_key)
        
        if not self.enabled:
            logger.warning("Etherscan API key not configured - limited functionality")
    
    async def _arun(self, query: str, filters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        if not self.enabled:
            return "⚠️ **Etherscan Service Limited**\n\nEtherscan functionality requires an API key.\nGet yours free at: https://etherscan.io/apis\n\nSet environment variable: `ETHERSCAN_API_KEY=your_key`"
        
        try:
            filters = filters or {}
            
            if filters.get("type") == "gas_prices":
                return await self._get_gas_prices()
            elif filters.get("type") == "eth_stats":
                return await self._get_eth_stats()
            elif self._is_address(query):
                return await self._get_address_info(query)
            elif self._is_tx_hash(query):
                return await self._get_transaction_info(query)
            else:
                return await self._get_gas_prices()
                
        except Exception as e:
            logger.error(f"Etherscan error: {e}")
            return f"⚠️ Etherscan service temporarily unavailable"
    
    def _is_address(self, query: str) -> bool:
        return (
            len(query) == 42 
            and query.startswith("0x") 
            and all(c in "0123456789abcdefABCDEF" for c in query[2:])
        )
    
    def _is_tx_hash(self, query: str) -> bool:
        return (
            len(query) == 66 
            and query.startswith("0x")
            and all(c in "0123456789abcdefABCDEF" for c in query[2:])
        )
    
    async def _get_gas_prices(self) -> str:
        try:
            params = {
                "module": "gastracker",
                "action": "gasoracle",
                "apikey": self._api_key
            }
            
            data = await self.make_request(self._base_url, params)
            
            if not data or data.get("status") != "1":
                error_msg = data.get("message", "Unknown error") if data else "No response"
                logger.warning(f"Etherscan gas price error: {error_msg}")
                return "⚠️ Gas price data temporarily unavailable"
            
            result_data = data.get("result", {})
            if not result_data:
                return "❌ No gas price data in response"
            
            safe_gas = result_data.get("SafeGasPrice", "N/A")
            standard_gas = result_data.get("StandardGasPrice", "N/A")
            fast_gas = result_data.get("FastGasPrice", "N/A")
            
            # Validate gas prices are numeric
            try:
                if safe_gas != "N/A":
                    float(safe_gas)
                if standard_gas != "N/A":
                    float(standard_gas)
                if fast_gas != "N/A":
                    float(fast_gas)
            except (ValueError, TypeError):
                return "⚠️ Invalid gas price data received"
            
            result = "⛽ **Ethereum Gas Prices:**\n\n"
            result += f"🐌 **Safe**: {safe_gas} gwei\n"
            result += f"⚡ **Standard**: {standard_gas} gwei\n"
            result += f"🚀 **Fast**: {fast_gas} gwei\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Gas prices error: {e}")
            return "⚠️ Gas price service temporarily unavailable"
    
    async def _get_eth_stats(self) -> str:
        params = {
            "module": "stats",
            "action": "ethsupply",
            "apikey": self._api_key
        }
        
        data = await self.make_request(self._base_url, params)
        
        if data.get("status") != "1":
            return "Ethereum stats unavailable"
        
        eth_supply = int(data.get("result", 0)) / 1e18
        
        result = "📊 **Ethereum Network Stats:**\n\n"
        result += f"💎 **ETH Supply**: {eth_supply:,.0f} ETH\n"
        
        return result
    
    async def _get_address_info(self, address: str) -> str:
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": "10",
            "sort": "desc",
            "apikey": self._api_key
        }
        
        data = await self.make_request(self._base_url, params)
        if data.get("status") != "1":
            return f"Address information unavailable for {address}"
        
        balance_wei = int(data.get("result", 0))
        balance_eth = balance_wei / 1e18
        
        result = f"📍 **Address Information:**\n\n"
        result += f"**Address**: {address}\n"
        result += f"💰 **Balance**: {balance_eth:.4f} ETH\n"
        
        return result
    
    async def _get_transaction_info(self, tx_hash: str) -> str:
        params = {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
            "apikey": self._api_key
        }
        
        data = await self.make_request(self._base_url, params)
        
        if not data.get("result"):
            return f"Transaction not found: {tx_hash}"
        
        tx = data.get("result", {})
        value_wei = int(tx.get("value", "0x0"), 16)
        value_eth = value_wei / 1e18
        gas_price = int(tx.get("gasPrice", "0x0"), 16) / 1e9
        
        result = f"📝 **Transaction Information:**\n\n"
        result += f"**Hash**: {tx_hash}\n"
        result += f"**From**: {tx.get('from', 'N/A')}\n"
        result += f"**To**: {tx.get('to', 'N/A')}\n"
        result += f"💰 **Value**: {value_eth:.4f} ETH\n"
        result += f"⛽ **Gas Price**: {gas_price:.2f} gwei\n"
        
        return result
