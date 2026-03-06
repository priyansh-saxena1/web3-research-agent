#!/usr/bin/env python3
"""
Complete pipeline test for Web3 Research Agent with Ollama fallback
Tests the entire flow: API calls → LLM processing → Response generation
"""

import asyncio
import sys
import os
sys.path.append('.')

async def test_complete_pipeline():
    print("🧪 Testing Complete Web3 Research Pipeline with Ollama Fallback")
    print("=" * 60)
    
    # Test 1: Initialize the research agent
    print("\n1️⃣ Testing Research Agent Initialization...")
    try:
        from src.agent.research_agent import Web3ResearchAgent
        agent = Web3ResearchAgent()
        
        if agent.enabled:
            print(f"✅ Primary LLM (Gemini) initialized successfully")
        else:
            print("⚠️ Primary LLM failed, will test Ollama fallback")
        
        print(f"✅ Agent initialized with {len(agent.tools)} tools")
        for tool in agent.tools:
            print(f"   - {tool.name}")
            
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test 2: Test Ollama connection
    print("\n2️⃣ Testing Ollama Connection...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama connected. Available models: {[m['name'] for m in models]}")
            
            # Test direct Ollama inference
            test_response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": "What is DeFi in one sentence?",
                    "stream": False
                },
                timeout=30
            )
            
            if test_response.status_code == 200:
                result = test_response.json()
                print(f"✅ Ollama inference test: {result['response'][:100]}...")
            else:
                print(f"❌ Ollama inference failed: {test_response.status_code}")
                
        else:
            print(f"❌ Ollama connection failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
    
    # Test 3: Test API integrations
    print("\n3️⃣ Testing API Integrations...")
    
    # Test DeFiLlama
    try:
        from src.tools.defillama_tool import DeFiLlamaTool
        defillama = DeFiLlamaTool()
        result = await defillama._arun("top 3 defi protocols")
        if result and "⚠️" not in result:
            print(f"✅ DeFiLlama API: {result[:80]}...")
        else:
            print(f"⚠️ DeFiLlama API: {result[:80]}...")
    except Exception as e:
        print(f"❌ DeFiLlama test failed: {e}")
    
    # Test CoinGecko
    try:
        from src.tools.coingecko_tool import CoinGeckoTool
        coingecko = CoinGeckoTool()
        result = await coingecko._arun("bitcoin price")
        if result and "⚠️" not in result:
            print(f"✅ CoinGecko API: {result[:80]}...")
        else:
            print(f"⚠️ CoinGecko API: {result[:80]}...")
    except Exception as e:
        print(f"❌ CoinGecko test failed: {e}")
    
    # Test Chart Data
    try:
        from src.tools.chart_data_tool import ChartDataTool
        chart_tool = ChartDataTool()
        result = await chart_tool._arun("price_chart", "bitcoin", "7d")
        if result and len(result) > 100:
            print(f"✅ Chart Data: Generated {len(result)} chars of chart data")
        else:
            print(f"⚠️ Chart Data: {result[:80]}...")
    except Exception as e:
        print(f"❌ Chart Data test failed: {e}")
    
    # Test 4: Test complete research query
    print("\n4️⃣ Testing Complete Research Query...")
    try:
        # Force Ollama fallback by setting GEMINI_API_KEY to invalid
        original_key = os.environ.get('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = 'invalid_key_for_testing'
        
        # Reinitialize agent to trigger fallback
        agent_fallback = Web3ResearchAgent()
        
        if agent_fallback.fallback_llm and agent_fallback.ollama_available:
            print("✅ Ollama fallback initialized successfully")
            
            # Test with simple query first
            simple_result = await agent_fallback.research_query(
                "What is Bitcoin? Give a brief answer."
            )
            
            if simple_result and simple_result.get('success'):
                response_text = simple_result.get('result', simple_result.get('response', 'No response text'))
                llm_used = simple_result.get('metadata', {}).get('llm_used', 'Unknown')
                print(f"✅ Query successful with {llm_used}: {response_text[:100]}...")
                
                # Now test with Web3 data integration  
                web3_result = await agent_fallback.research_query(
                    "Get Bitcoin price and explain current market trends"
                )
                
                if web3_result and web3_result.get('success'):
                    web3_response = web3_result.get('result', web3_result.get('response', 'No response text'))
                    web3_llm = web3_result.get('metadata', {}).get('llm_used', 'Unknown')
                    print(f"✅ Web3 integration with {web3_llm}: {web3_response[:100]}...")
                    print(f"   Sources: {web3_result.get('sources', [])}")
                    visualizations = web3_result.get('visualizations', web3_result.get('metadata', {}).get('visualizations', []))
                    print(f"   Visualizations: {len(visualizations)}")
                else:
                    print(f"⚠️ Web3 integration: {web3_result}")
                    
            else:
                print(f"❌ Query failed: {simple_result}")
        else:
            print("❌ Ollama fallback initialization failed")
            
        # Restore original key
        if original_key:
            os.environ['GEMINI_API_KEY'] = original_key
        else:
            os.environ.pop('GEMINI_API_KEY', None)
            
    except Exception as e:
        print(f"❌ Complete query test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Pipeline Test Complete!")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())
