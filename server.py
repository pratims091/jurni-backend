#!/usr/bin/env python3
"""
Simple startup script for development server.
Usage: python start_server.py [--port PORT] [--host HOST]
"""

import argparse
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn


def main():
    parser = argparse.ArgumentParser(description='Start Jurni Backend Development Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload on code changes')
    
    args = parser.parse_args()
    
    print("🚀 Starting Jurni Backend Development Server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Reload: {args.reload}")
    print(f"   API Documentation: http://{args.host}:{args.port}/docs")
    print("   Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
