#!/bin/bash

# One-line deployment for Vast.ai instances
# Usage: curl -s https://raw.githubusercontent.com/YOUR_USERNAME/video-upscale-vastai/main/deploy_oneline.sh | bash

echo "Starting deployment from GitHub..."

cd /workspace
rm -rf video-upscale-vastai 2>/dev/null
git clone https://github.com/YOUR_USERNAME/video-upscale-vastai.git
cd video-upscale-vastai
chmod +x *.sh
./setup_vastai.sh
nohup ./start_server.sh > server.log 2>&1 &

echo "Deployment completed!"
echo "Server running on port 5000"
echo "Test with: curl http://localhost:5000/health"