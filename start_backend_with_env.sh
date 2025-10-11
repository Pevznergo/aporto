#!/bin/bash
# Enhanced backend startup script with automatic .env loading
# This script loads environment variables from .env file and starts the backend

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting backend with environment variables..."

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    set -a  # Automatically export all variables
    source .env
    set +a  # Disable automatic export
    echo "✓ Environment variables loaded"
    
    # Verify key variables are loaded
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "✓ OPENAI_API_KEY loaded"
    else
        echo "⚠ Warning: OPENAI_API_KEY not set"
    fi
    
    if [ -n "$UPSCALE_CONCURRENCY" ]; then
        echo "✓ UPSCALE_CONCURRENCY = $UPSCALE_CONCURRENCY"
    else
        echo "⚠ Warning: UPSCALE_CONCURRENCY not set"
    fi
    
    if [ -n "$VAST_INSTANCE_ID" ]; then
        echo "✓ VAST_INSTANCE_ID = $VAST_INSTANCE_ID"
    else
        echo "⚠ Warning: VAST_INSTANCE_ID not set"
    fi
else
    echo "⚠ Warning: .env file not found"
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment .venv not found"
    echo "Please create it with: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Start the backend
echo "Starting FastAPI backend..."
if [ -f "backend.pid" ]; then
    OLD_PID=$(cat backend.pid)
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping existing backend process ($OLD_PID)..."
        kill "$OLD_PID"
        sleep 2
    fi
fi

# Start uvicorn with environment variables in background (like nohup)
nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 >> backend.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > backend.pid

echo "✓ Backend started with PID: $NEW_PID"
echo "✓ Logs: tail -f backend.log"
echo "✓ API: http://127.0.0.1:8000"
echo "✓ Running in background (nohup)"

# Wait a moment and check if process is still running
sleep 2
if kill -0 "$NEW_PID" 2>/dev/null; then
    echo "✓ Backend is running successfully!"
    echo "✓ Process will continue running even if you close terminal"
else
    echo "❌ Backend failed to start. Check backend.log for errors."
    exit 1
fi
