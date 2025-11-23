#!/usr/bin/env python3
"""
Debug wrapper for the MCP server.
Use this file to run and debug the server directly in PyCharm.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the MCP server
from main import mcp

if __name__ == "__main__":
    # You can set breakpoints anywhere in main.py and they'll be hit
    print("🐛 Starting MCP server in debug mode...")
    print("💡 Set breakpoints in main.py and interact via the MCP Inspector")
    print()
    
    # Run the server in development mode
    # This is equivalent to: uv run mcp dev main.py
    mcp.run(transport="stdio")

