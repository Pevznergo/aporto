#!/bin/bash
cd /workspace/aporto/upscale/vastai_deployment

# Run setup if needed
if [ ! -f "/workspace/.setup_complete" ]; then
    echo "🚀 Running initial setup..."
    ./setup_vastai.sh
    touch /workspace/.setup_complete
fi

# Always apply the basicsr fix (idempotent)
echo "🔧 Applying compatibility fixes..."
chmod +x auto_fix_basicsr.sh
./auto_fix_basicsr.sh

# Start the server
./start_server.sh
