import asyncio
from typing import Dict, Any, List, Optional
from src.api_clients import coingecko_client
from src.cache_manager import cache_manager
import json

class PortfolioAnalyzer:
    def __init__(self):
        self.symbol_map = {
            "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "ada": "cardano",
            "dot": "polkadot", "bnb": "binancecoin", "usdc": "usd-coin", 
            "usdt": "tether", "xrp": "ripple", "avax": "avalanche-2",
            "link": "chainlink", "matic": "matic-network", "uni": "uniswap"
        }
    
    def _format_coin_id(self, symbol: str) -> str:
        return self.symbol_map.get(symbol.lower(), symbol.lower())
    
    async def analyze_portfolio(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            coin_ids = [self._format_coin_id(h["symbol"]) for h in holdings]
            
            tasks = []
            for coin_id in coin_ids:
                tasks.append(coingecko_client.get_coin_data(coin_id))
                tasks.append(coingecko_client.get_price_history(coin_id, days=30))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            portfolio_value = 0
            portfolio_change_24h = 0
            asset_allocation = []
            risk_metrics = []
            
            for i, holding in enumerate(holdings):
                coin_data_idx = i * 2
                price_history_idx = i * 2 + 1
                
                if not isinstance(results[coin_data_idx], Exception):
                    coin_data = results[coin_data_idx]
                    market_data = coin_data.get("market_data", {})
                    current_price = market_data.get("current_price", {}).get("usd", 0)
                    price_change_24h = market_data.get("price_change_percentage_24h", 0)
                    
                    holding_value = current_price * holding["amount"]
                    portfolio_value += holding_value
                    portfolio_change_24h += holding_value * (price_change_24h / 100)
                    
                    volatility = 0
                    if not isinstance(results[price_history_idx], Exception):
                        price_history = results[price_history_idx]
                        prices = [p[1] for p in price_history.get("prices", [])]
                        if len(prices) > 1:
                            price_changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                            volatility = sum(abs(change) for change in price_changes) / len(price_changes)
                    
                    asset_allocation.append({
                        "symbol": holding["symbol"].upper(),
                        "name": coin_data.get("name", "Unknown"),
                        "value": holding_value,
                        "percentage": 0,
                        "amount": holding["amount"],
                        "price": current_price,
                        "change_24h": price_change_24h
                    })
                    
                    risk_metrics.append({
                        "symbol": holding["symbol"].upper(),
                        "volatility": volatility,
                        "market_cap_rank": coin_data.get("market_cap_rank", 999)
                    })
            
            for asset in asset_allocation:
                asset["percentage"] = (asset["value"] / portfolio_value) * 100 if portfolio_value > 0 else 0
            
            portfolio_change_percentage = (portfolio_change_24h / portfolio_value) * 100 if portfolio_value > 0 else 0
            
            avg_volatility = sum(r["volatility"] for r in risk_metrics) / len(risk_metrics) if risk_metrics else 0
            
            diversification_score = len([a for a in asset_allocation if a["percentage"] >= 5])
            
            risk_level = "Low" if avg_volatility < 0.05 else "Medium" if avg_volatility < 0.10 else "High"
            
            return {
                "total_value": portfolio_value,
                "change_24h": portfolio_change_24h,
                "change_24h_percentage": portfolio_change_percentage,
                "asset_allocation": sorted(asset_allocation, key=lambda x: x["value"], reverse=True),
                "risk_metrics": {
                    "overall_risk": risk_level,
                    "avg_volatility": avg_volatility,
                    "diversification_score": diversification_score,
                    "largest_holding_percentage": max([a["percentage"] for a in asset_allocation]) if asset_allocation else 0
                },
                "recommendations": self._generate_recommendations(asset_allocation, risk_metrics)
            }
            
        except Exception as e:
            raise Exception(f"Portfolio analysis failed: {str(e)}")
    
    def _generate_recommendations(self, allocation: List[Dict[str, Any]], risk_metrics: List[Dict[str, Any]]) -> List[str]:
        recommendations = []
        
        if not allocation:
            return ["Unable to generate recommendations - no valid portfolio data"]
        
        largest_holding = max(allocation, key=lambda x: x["percentage"])
        if largest_holding["percentage"] > 50:
            recommendations.append(f"Consider reducing {largest_holding['symbol']} position (currently {largest_holding['percentage']:.1f}%) to improve diversification")
        
        high_risk_assets = [r for r in risk_metrics if r["volatility"] > 0.15]
        if len(high_risk_assets) > len(allocation) * 0.6:
            recommendations.append("Portfolio has high volatility exposure - consider adding stable assets like BTC or ETH")
        
        small_cap_heavy = len([r for r in risk_metrics if r["market_cap_rank"] > 100])
        if small_cap_heavy > len(allocation) * 0.4:
            recommendations.append("High small-cap exposure detected - consider balancing with top 20 cryptocurrencies")
        
        if len(allocation) < 5:
            recommendations.append("Consider diversifying into 5-10 different cryptocurrencies to reduce risk")
        
        stablecoin_exposure = sum(a["percentage"] for a in allocation if a["symbol"] in ["USDC", "USDT", "DAI"])
        if stablecoin_exposure < 10:
            recommendations.append("Consider allocating 10-20% to stablecoins for portfolio stability")
        
        return recommendations[:5]
    
    async def compare_portfolios(self, portfolio1: List[Dict[str, Any]], portfolio2: List[Dict[str, Any]]) -> Dict[str, Any]:
        analysis1 = await self.analyze_portfolio(portfolio1)
        analysis2 = await self.analyze_portfolio(portfolio2)
        
        return {
            "portfolio_1": analysis1,
            "portfolio_2": analysis2,
            "comparison": {
                "value_difference": analysis2["total_value"] - analysis1["total_value"],
                "performance_difference": analysis2["change_24h_percentage"] - analysis1["change_24h_percentage"],
                "risk_comparison": f"Portfolio 2 is {'higher' if analysis2['risk_metrics']['avg_volatility'] > analysis1['risk_metrics']['avg_volatility'] else 'lower'} risk",
                "diversification_comparison": f"Portfolio 2 is {'more' if analysis2['risk_metrics']['diversification_score'] > analysis1['risk_metrics']['diversification_score'] else 'less'} diversified"
            }
        }

portfolio_analyzer = PortfolioAnalyzer()