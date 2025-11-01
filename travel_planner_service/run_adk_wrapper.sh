#!/bin/bash
# Wrapper script to run ADK with correct Python path

cd /Users/dishant.rana/g_hack/jurni_backend/travel_planner_service
source venv/bin/activate

# Set PYTHONPATH to include current directory
export PYTHONPATH="/Users/dishant.rana/g_hack/jurni_backend/travel_planner_service:$PYTHONPATH"

# Set Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS="/Users/dishant.rana/g_hack/jurni_backend/travel_planner_service/serviceAccount.json"

# Run ADK API server with SQLite database for session storage
adk api_server travel_planner_agent --host 0.0.0.0 --port 8002 --session_db_url "sqlite:///sessions.db"

