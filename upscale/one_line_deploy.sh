#!/bin/bash

# One-line deployment command for Vast.ai instances
# Usage: Run this command directly on a Vast.ai instance
# curl -s https://raw.githubusercontent.com/YOUR_USERNAME/video-upscale-vastai/main/one_line_deploy.sh | bash

echo "Starting one-line deployment..."

# Download and execute the full deployment script
cd /workspace
wget -O deploy_from_github.sh https://raw.githubusercontent.com/YOUR_USERNAME/video-upscale-vastai/main/deploy_from_github.sh
chmod +x deploy_from_github.sh
./deploy_from_github.sh