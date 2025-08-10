import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def minimal_test():
    try:
        print("Testing minimal imports...")
        
        from src.utils.config import config
        print("✅ Config imported")
        
        from src.utils.logger import get_logger
        print("✅ Logger imported")
        
        from src.tools.base_tool import BaseWeb3Tool
        print("✅ Base tool imported")
        
        from src.tools.coingecko_tool import CoinGeckoTool
        tool = CoinGeckoTool()
        print("✅ CoinGecko tool created")
        
        from src.agent.research_agent import Web3ResearchAgent
        print("✅ Research agent imported")
        
        print("🎉 All core components working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    minimal_test()
