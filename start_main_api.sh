#!/bin/bash

# Start script for Main API Service
echo "🔧 Starting Main API Service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please copy env.example to .env and configure it."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment for Main API Service..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    poetry install
else
    source venv/bin/activate
fi

echo "🚀 Starting Main API Service on port 8001..."
echo "📝 Logs will be written to logs/main_api.log"
echo "📊 API Documentation: http://localhost:8001/docs"
echo "🏥 Health Check: http://localhost:8001/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start the service
python -m app.main
