#!/usr/bin/env python3
"""
Quick test for ChartDataTool cleanup functionality
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.chart_data_tool import ChartDataTool

async def test_chart_tool_cleanup():
    """Test that ChartDataTool works and cleanup doesn't throw errors"""
    print("🧪 Testing ChartDataTool...")
    
    tool = ChartDataTool()
    
    try:
        # Test basic functionality
        print("📊 Testing price chart data...")
        result = await tool._arun("price_chart", "bitcoin", "7d")
        print(f"✅ Chart data result: {len(result)} characters")
        
        # Test cleanup method exists and works
        print("🧹 Testing cleanup method...")
        await tool.cleanup()
        print("✅ Cleanup method executed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    success = await test_chart_tool_cleanup()
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
