#!/bin/bash
# Simple backend startup - just load .env and start uvicorn

# Load .env variables
[ -f .env ] && set -a && source .env && set +a

# Start backend exactly like before, but with .env loaded
nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 >> backend.log 2>&1 &

echo "Backend started with PID: $!"
echo $! > backend.pid