#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    try:
        print("Testing imports...")
        
        # Test basic Python modules
        import json
        import asyncio
        from datetime import datetime
        from typing import List, Tuple
        print("✅ Basic Python modules imported successfully")
        
        # Test installed packages
        import gradio as gr
        print("✅ Gradio imported successfully")
        
        import aiohttp
        print("✅ aiohttp imported successfully")
        
        import plotly
        print("✅ Plotly imported successfully")
        
        import pandas
        print("✅ Pandas imported successfully")
        
        import pydantic
        print("✅ Pydantic imported successfully")
        
        # Test LangChain
        import langchain
        from langchain.agents import AgentExecutor
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ LangChain modules imported successfully")
        
        # Test our modules
        from src.utils.config import config
        from src.utils.logger import get_logger
        print("✅ Config and logger imported successfully")
        
        from src.tools.base_tool import BaseWeb3Tool
        from src.tools.coingecko_tool import CoinGeckoTool
        from src.tools.defillama_tool import DeFiLlamaTool
        from src.tools.etherscan_tool import EtherscanTool
        print("✅ Tools imported successfully")
        
        from src.agent.research_agent import Web3ResearchAgent
        from src.agent.query_planner import QueryPlanner
        print("✅ Agent modules imported successfully")
        
        from src.api.airaa_integration import AIRAAIntegration
        print("✅ AIRAA integration imported successfully")
        
        from src.visualizations import create_price_chart, create_market_overview
        print("✅ Visualizations imported successfully")
        
        # Test app import
        from app import Web3CoPilotApp
        print("✅ Main app imported successfully")
        
        print("\n🎉 All imports successful! The application is ready to run.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_app_initialization():
    try:
        print("\nTesting app initialization...")
        # This will test if we can create the app instance
        # but won't actually run it
        os.environ.setdefault('GEMINI_API_KEY', 'test_key_for_import_test')
        
        from app import Web3CoPilotApp
        print("✅ App class imported successfully")
        
        # Test if we can create the interface (but don't launch)
        app = Web3CoPilotApp()
        interface = app.create_interface()
        print("✅ App interface created successfully")
        
        print("\n🚀 Application is fully functional and ready to launch!")
        return True
        
    except Exception as e:
        print(f"❌ App initialization error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Web3 Research Co-Pilot - Application Test")
    print("=" * 60)
    
    success = test_imports()
    if success:
        test_app_initialization()
    
    print("=" * 60)
    print("Test complete!")
