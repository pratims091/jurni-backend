#!/usr/bin/env python3
"""Run Travel Planner Service using ADK's built-in API server."""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Add the current directory to Python path so ADK can find travel_planner_agent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("TRAVEL_PLANNER_PORT", 8002))
    host = os.getenv("TRAVEL_PLANNER_HOST", "0.0.0.0")
    
    print(f"🚀 Starting Travel Planner Service using ADK API server on {host}:{port}")
    print("📝 This will start the ADK's built-in API server")
    print("🛑 Press Ctrl+C to stop the service")
    print("")
    
    # Set PYTHONPATH environment variable to include current directory
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__)) + ':' + env.get('PYTHONPATH', '')
    
    # Run the ADK API server
    try:
        # Run adk api_server command from the travel_planner_service directory
        # pointing to the travel_planner_agent subdirectory
        subprocess.run([
            "adk", "api_server", "travel_planner_agent",
            "--host", host,
            "--port", str(port)
        ], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting ADK API server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
        sys.exit(0)
