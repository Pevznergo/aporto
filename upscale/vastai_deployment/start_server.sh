#!/bin/bash

# Startup script for video upscaling server
echo "Starting Video Upscaling Server..."

# Change to app directory
cd /app

# Install any missing dependencies
pip install -r requirements.txt

# Download models if not present
if [ ! -f "models/realesr-general-x4v3.pth" ]; then
    echo "Downloading Real-ESRGAN model..."
    mkdir -p models
    wget -O models/realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
fi

# Start the server
echo "Server starting on port 5000..."
python server.py