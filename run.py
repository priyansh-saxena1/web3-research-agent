#!/usr/bin/env python3

"""
Web3 Research Co-Pilot Application
Complete production-ready crypto research assistant powered by AI
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("🚀 Starting Web3 Research Co-Pilot...")
    
    try:
        from app import Web3CoPilotApp
        
        app = Web3CoPilotApp()
        interface = app.create_interface()
        
        print("✅ Application initialized successfully!")
        print("🌐 Launching web interface...")
        print("📍 Local URL: http://localhost:7860")
        
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_api=False,
            quiet=False
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
