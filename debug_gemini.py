#!/usr/bin/env python3
"""
Debug test to understand why Gemini responses aren't being cleaned
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.config import config

async def test_gemini_response_structure():
    """Test the structure of Gemini responses to understand the cleaning issue"""
    
    if not config.GEMINI_API_KEY:
        print("❌ No Gemini API key available")
        return False
    
    try:
        print("🧪 Testing Gemini response structure...")
        
        # Initialize Gemini
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=config.GEMINI_API_KEY,
            temperature=0.1
        )
        
        # Test simple query
        response = await llm.ainvoke("What is 2+2?")
        
        print(f"📄 Response type: {type(response)}")
        print(f"📄 Response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        if hasattr(response, 'content'):
            print(f"✅ Response has 'content' attribute")
            print(f"📝 Content: {response.content}")
            print(f"📝 Content type: {type(response.content)}")
        else:
            print("❌ Response does NOT have 'content' attribute")
            
        print(f"📄 Full response: {str(response)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    success = await test_gemini_response_structure()
    if success:
        print("\n🎉 Test completed!")
        return 0
    else:
        print("\n❌ Test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
