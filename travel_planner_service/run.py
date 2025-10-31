#!/usr/bin/env python3
"""Run script for Travel Planner Service."""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("TRAVEL_PLANNER_PORT", 8002))
    host = os.getenv("TRAVEL_PLANNER_HOST", "0.0.0.0")
    
    print(f"🚀 Starting Travel Planner Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
