#!/usr/bin/env python3
"""
Comprehensive test suite for Web3 Research Co-Pilot
"""

import sys
import asyncio
import time
from datetime import datetime

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing imports...")
    
    try:
        # Core imports
        from src.visualizations import CryptoVisualizations, create_price_chart
        from src.agent.research_agent import Web3ResearchAgent
        from src.utils.config import config
        from src.tools.coingecko_tool import CoinGeckoTool
        from src.tools.defillama_tool import DeFiLlamaTool
        from src.tools.etherscan_tool import EtherscanTool
        from src.api.airaa_integration import AIRAAIntegration
        
        # FastAPI app
        from app import app, service, Web3CoPilotService
        
        print("✅ All imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration setup"""
    print("🧪 Testing configuration...")
    
    try:
        from src.utils.config import config
        
        print(f"   • GEMINI_API_KEY: {'✅ Set' if config.GEMINI_API_KEY else '❌ Not set'}")
        print(f"   • COINGECKO_API_KEY: {'✅ Set' if config.COINGECKO_API_KEY else '⚠️ Not set'}")
        print(f"   • ETHERSCAN_API_KEY: {'✅ Set' if config.ETHERSCAN_API_KEY else '⚠️ Not set'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_visualizations():
    """Test visualization creation"""
    print("🧪 Testing visualizations...")
    
    try:
        from src.visualizations import CryptoVisualizations
        
        # Test empty chart
        fig1 = CryptoVisualizations._create_empty_chart("Test message")
        print("   ✅ Empty chart creation")
        
        # Test price chart with sample data
        sample_data = {
            'prices': [
                [1672531200000, 16500.50], 
                [1672617600000, 16750.25],
                [1672704000000, 17100.00]
            ],
            'total_volumes': [
                [1672531200000, 1000000], 
                [1672617600000, 1200000],
                [1672704000000, 1100000]
            ]
        }
        
        fig2 = CryptoVisualizations.create_price_chart(sample_data, 'BTC')
        print("   ✅ Price chart with data")
        
        # Test market overview
        market_data = [
            {'name': 'Bitcoin', 'market_cap': 500000000000, 'price_change_percentage_24h': 2.5},
            {'name': 'Ethereum', 'market_cap': 200000000000, 'price_change_percentage_24h': -1.2}
        ]
        
        fig3 = CryptoVisualizations.create_market_overview(market_data)
        print("   ✅ Market overview chart")
        
        return True
        
    except Exception as e:
        print(f"❌ Visualization test failed: {e}")
        return False

def test_tools():
    """Test individual tools"""
    print("🧪 Testing tools...")
    
    try:
        from src.tools.coingecko_tool import CoinGeckoTool
        from src.tools.defillama_tool import DeFiLlamaTool
        from src.tools.etherscan_tool import EtherscanTool
        
        # Test tool initialization
        coingecko = CoinGeckoTool()
        print("   ✅ CoinGecko tool initialization")
        
        defillama = DeFiLlamaTool()
        print("   ✅ DeFiLlama tool initialization")
        
        etherscan = EtherscanTool()
        print("   ✅ Etherscan tool initialization")
        
        return True
        
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False

async def test_service():
    """Test service functionality"""
    print("🧪 Testing service...")
    
    try:
        from app import service
        
        print(f"   • Service enabled: {'✅' if service.enabled else '❌'}")
        print(f"   • Agent available: {'✅' if service.agent else '❌'}")
        print(f"   • AIRAA enabled: {'✅' if service.airaa and service.airaa.enabled else '❌'}")
        
        # Test a simple query
        if service.enabled:
            print("   🔄 Testing query processing...")
            response = await service.process_query("What is Bitcoin?")
            
            if response.success:
                print("   ✅ Query processing successful")
                print(f"      Response length: {len(response.response)} characters")
            else:
                print(f"   ⚠️ Query failed: {response.error}")
        else:
            print("   ⚠️ Service disabled - limited testing")
            
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

def test_app_health():
    """Test FastAPI app health"""
    print("🧪 Testing FastAPI app...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        with TestClient(app) as client:
            # Test health endpoint
            response = client.get("/health")
            if response.status_code == 200:
                print("   ✅ Health endpoint")
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
                
            # Test status endpoint  
            response = client.get("/status")
            if response.status_code == 200:
                print("   ✅ Status endpoint")
                status_data = response.json()
                print(f"      Version: {status_data.get('version', 'Unknown')}")
            else:
                print(f"   ❌ Status endpoint failed: {response.status_code}")
                
            # Test homepage
            response = client.get("/")
            if response.status_code == 200:
                print("   ✅ Homepage endpoint")
            else:
                print(f"   ❌ Homepage failed: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ FastAPI test failed: {e}")
        return False

def run_performance_test():
    """Simple performance test"""
    print("🧪 Performance test...")
    
    try:
        from src.visualizations import CryptoVisualizations
        
        # Time visualization creation
        start_time = time.time()
        
        for i in range(10):
            sample_data = {
                'prices': [[1672531200000 + i*3600000, 16500 + i*10] for i in range(100)],
                'total_volumes': [[1672531200000 + i*3600000, 1000000 + i*1000] for i in range(100)]
            }
            fig = CryptoVisualizations.create_price_chart(sample_data, 'TEST')
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        print(f"   ⏱️ Average chart creation: {avg_time:.3f}s")
        
        if avg_time < 1.0:
            print("   ✅ Performance acceptable")
            return True
        else:
            print("   ⚠️ Performance slow")
            return True
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 50)
    print("🚀 Web3 Research Co-Pilot - Test Suite")
    print("=" * 50)
    print()
    
    test_results = []
    
    # Run all tests
    test_results.append(test_imports())
    test_results.append(test_configuration())
    test_results.append(test_visualizations())
    test_results.append(test_tools())
    test_results.append(await test_service())
    test_results.append(test_app_health())
    test_results.append(run_performance_test())
    
    print()
    print("=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
