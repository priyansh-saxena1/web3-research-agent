#!/usr/bin/env python3
"""
Quick test to verify response cleaning works properly
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.research_agent import Web3ResearchAgent

async def test_response_cleaning():
    """Test that responses are properly cleaned of LangChain metadata"""
    print("🧪 Testing response cleaning...")
    
    agent = Web3ResearchAgent()
    
    if not agent.enabled:
        print("❌ Agent not enabled")
        return False
    
    try:
        print("📊 Testing simple Bitcoin price query...")
        result = await agent.research_query("What is Bitcoin current price?", use_gemini=True)
        
        if result['success']:
            response_content = result['result']
            print(f"✅ Query successful!")
            print(f"📈 Response type: {type(response_content)}")
            print(f"📄 Response preview: {response_content[:200]}...")
            
            # Check if response contains LangChain metadata (bad)
            if "additional_kwargs" in str(response_content) or "response_metadata" in str(response_content):
                print("❌ Response contains LangChain metadata - not properly cleaned")
                return False
            else:
                print("✅ Response properly cleaned - no LangChain metadata found")
                return True
        else:
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

async def main():
    success = await test_response_cleaning()
    if success:
        print("\n🎉 Response cleaning test passed!")
        return 0
    else:
        print("\n❌ Response cleaning test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
