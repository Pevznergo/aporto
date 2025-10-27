#!/bin/bash

# Startup script for video upscaling server
echo "Starting Video Upscaling Server..."

# Change to workspace directory
cd /workspace/aporto

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded"
fi

# Verify models exist
if [ ! -f "upscale/models/realesr-general-x4v3.pth" ]; then
    echo "❌ Real-ESRGAN model not found at upscale/models/realesr-general-x4v3.pth"
    echo "   Please run install.sh first"
    exit 1
fi

if [ ! -f "upscale/models/GFPGANv1.4.pth" ]; then
    echo "❌ GFPGAN model not found at upscale/models/GFPGANv1.4.pth"
    echo "   Please run install.sh first"
    exit 1
fi

# Start the server
echo "🚀 Starting server on port 5000..."
python3 upscale/vastai_deployment/server.py