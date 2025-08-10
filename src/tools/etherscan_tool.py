from typing import Dict, Any, Optional
from pydantic import BaseModel, PrivateAttr
from src.tools.base_tool import BaseWeb3Tool, Web3ToolInput
from src.utils.config import config

class EtherscanTool(BaseWeb3Tool):
    name: str = "etherscan_data"
    description: str = """Get Ethereum blockchain data from Etherscan.
    Useful for: transaction analysis, address information, gas prices, token data.
    Input: Ethereum address, transaction hash, or general blockchain query."""
    args_schema: type[BaseModel] = Web3ToolInput
    
    _base_url: str = PrivateAttr(default="https://api.etherscan.io/api")
    _api_key: Optional[str] = PrivateAttr(default=None)
    
    def __init__(self):
        super().__init__()
        self._api_key = config.ETHERSCAN_API_KEY
    
    async def _arun(self, query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        if not self.api_key:
            return "❌ Etherscan API key not configured"
        
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
            return f"Etherscan error: {str(e)}"
    
    def _is_address(self, query: str) -> bool:
        return len(query) == 42 and query.startswith("0x")
    
    def _is_tx_hash(self, query: str) -> bool:
        return len(query) == 66 and query.startswith("0x")
    
    async def _get_gas_prices(self) -> str:
        params = {
            "module": "gastracker",
            "action": "gasoracle",
            "apikey": self.api_key
        }
        
        data = await self.make_request(self.base_url, params)
        
        if data.get("status") != "1":
            return "Gas price data unavailable"
        
        result_data = data.get("result", {})
        safe_gas = result_data.get("SafeGasPrice", "N/A")
        standard_gas = result_data.get("StandardGasPrice", "N/A")
        fast_gas = result_data.get("FastGasPrice", "N/A")
        
        result = "⛽ **Ethereum Gas Prices:**\n\n"
        result += f"🐌 **Safe**: {safe_gas} gwei\n"
        result += f"⚡ **Standard**: {standard_gas} gwei\n"
        result += f"🚀 **Fast**: {fast_gas} gwei\n"
        
        return result
    
    async def _get_eth_stats(self) -> str:
        params = {
            "module": "stats",
            "action": "ethsupply",
            "apikey": self.api_key
        }
        
        data = await self.make_request(self.base_url, params)
        
        if data.get("status") != "1":
            return "Ethereum stats unavailable"
        
        eth_supply = int(data.get("result", 0)) / 1e18
        
        result = "📊 **Ethereum Network Stats:**\n\n"
        result += f"💎 **ETH Supply**: {eth_supply:,.0f} ETH\n"
        
        return result
    
    async def _get_address_info(self, address: str) -> str:
        params = {
            "module": "account",
            "action": "balance", 
            "address": address,
            "tag": "latest",
            "apikey": self.api_key
        }
        
        data = await self.make_request(self.base_url, params)
        
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
            "apikey": self.api_key
        }
        
        data = await self.make_request(self.base_url, params)
        
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
