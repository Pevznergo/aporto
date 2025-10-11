#!/bin/bash
# Startup script for Aporto Orchestrator with queue configuration

set -e

# Load environment variables
if [ -f "/opt/aporto/.env" ]; then
    echo "Loading environment from /opt/aporto/.env"
    export $(cat /opt/aporto/.env | grep -v '^#' | xargs)
else
    echo "Warning: /opt/aporto/.env not found"
fi

# Set default queue configurations if not set
export UPSCALE_UPLOAD_CONCURRENCY=${UPSCALE_UPLOAD_CONCURRENCY:-1}
export UPSCALE_CONCURRENCY=${UPSCALE_CONCURRENCY:-2}  
export UPSCALE_RESULT_DOWNLOAD_CONCURRENCY=${UPSCALE_RESULT_DOWNLOAD_CONCURRENCY:-1}

# Set cut processing defaults
export CUT_ON_GPU=${CUT_ON_GPU:-1}
export WHISPER_MODEL=${WHISPER_MODEL:-small}

echo "🚀 Starting Aporto Orchestrator with queue configuration:"
echo "  📤 Upload queue: ${UPSCALE_UPLOAD_CONCURRENCY} concurrent"
echo "  🎮 GPU processing: ${UPSCALE_CONCURRENCY} concurrent"
echo "  📥 Download queue: ${UPSCALE_RESULT_DOWNLOAD_CONCURRENCY} concurrent"
echo "  ✂️ Cut processing: GPU=${CUT_ON_GPU}, Model=${WHISPER_MODEL}"

# Change to app directory
cd /opt/aporto

# Start the application
exec python -m app.main