#!/bin/bash
# Restart the upscale server with correct environment

cd /workspace/aporto

echo "Stopping old server..."
pkill -f 'python.*server.py' || true
sleep 2

echo "Loading environment from .env..."
set -a
source .env
set +a

echo "Environment loaded:"
echo "  VENV_PYTHON=$VENV_PYTHON"
echo "  REALESRGAN_MODEL_PATH=$REALESRGAN_MODEL_PATH"
echo "  GFPGAN_MODEL_PATH=$GFPGAN_MODEL_PATH"

echo "Starting server..."
nohup .venv/bin/python upscale/vastai_deployment/server.py > /workspace/server.log 2>&1 &

sleep 2

PID=$(ps aux | grep 'python.*server.py' | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
    echo "✅ Server started with PID: $PID"
    echo ""
    echo "Check logs: tail -f /workspace/server.log"
    echo "Check health: curl http://localhost:5000/health"
else
    echo "❌ Failed to start server"
    exit 1
fi
