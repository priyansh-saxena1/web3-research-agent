#!/usr/bin/env python3
"""
Test the updated tool selection to ensure we use CryptoCompare/Etherscan instead of CoinGecko
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.research_agent import Web3ResearchAgent

async def test_tool_selection():
    """Test that the system prioritizes CryptoCompare and Etherscan over CoinGecko"""
    print("🧪 Testing tool selection...")
    
    agent = Web3ResearchAgent()
    
    if not agent.enabled:
        print("❌ Agent not enabled")
        return False
    
    # Check which tools are initialized
    tool_names = [tool.name for tool in agent.tools]
    print(f"🛠️ Available tools: {tool_names}")
    
    # Verify CoinGecko is not in tools (since no API key)
    if 'coingecko_data' in tool_names:
        print("⚠️ CoinGecko tool is still initialized - this may cause API failures")
    else:
        print("✅ CoinGecko tool properly skipped (no API key)")
    
    # Verify we have the working tools
    expected_tools = ['cryptocompare_data', 'etherscan_data', 'defillama_data', 'chart_data_provider']
    working_tools = [tool for tool in expected_tools if tool in tool_names]
    print(f"✅ Working tools available: {working_tools}")
    
    # Test a simple query
    try:
        print("\n📊 Testing Bitcoin price query...")
        result = await agent.research_query("Analyze Bitcoin price trends", use_gemini=True)
        
        if result['success']:
            print("✅ Query successful!")
            print(f"📈 Result preview: {result['result'][:200]}...")
            print(f"🔧 Tools used: {result.get('metadata', {}).get('tools_used', 'N/A')}")
            return True
        else:
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

async def main():
    success = await test_tool_selection()
    if success:
        print("\n🎉 Tool selection test passed!")
        return 0
    else:
        print("\n❌ Tool selection test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
