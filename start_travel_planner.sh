#!/bin/bash

# Start script for Travel Planner Service
echo "🌍 Starting Travel Planner Service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please copy env.example to .env and configure it."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Navigate to travel planner service directory
cd travel_planner_service

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment for Travel Planner Service..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🚀 Starting Travel Planner Service on port 8002..."
echo "📝 Logs will be written to ../logs/travel_planner.log"
echo "📊 API Documentation: http://localhost:8002/docs"
echo "🏥 Health Check: http://localhost:8002/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start the service using ADK's built-in API server with wrapper
./run_adk_wrapper.sh
