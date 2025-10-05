#!/bin/bash
set -euo pipefail

# Startup script for video upscaling server (path-agnostic)
echo "Starting Video Upscaling Server..."

# Change to this script's directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure python3/pip3 available
PY=${PYTHON_BIN:-python3}
PIP=${PIP_BIN:-pip3}

# Install any missing dependencies
$PIP install -r requirements.txt

# Download models if not present
if [ ! -f "models/realesr-general-x4v3.pth" ]; then
    echo "Downloading Real-ESRGAN model..."
    mkdir -p models
    wget -O models/realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth || true
fi

# Start the server
export FLASK_ENV=production
export PYTHONUNBUFFERED=1

echo "Server starting on port 5000..."
exec $PY server.py
