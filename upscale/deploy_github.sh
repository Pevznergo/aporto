#!/bin/bash

# Deployment script for Vast.ai instances
# This script can be used directly on a Vast.ai instance to deploy from GitHub

echo "Deploying Video Upscaling Application from GitHub..."

# Install git if not already installed
apt-get update
apt-get install -y git

# Clone repository
cd /workspace
if [ -d "video-upscale-vastai" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd video-upscale-vastai
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/YOUR_USERNAME/video-upscale-vastai.git
    cd video-upscale-vastai
fi

# Make scripts executable
chmod +x *.sh

# Run setup
echo "Running setup..."
./setup_vastai.sh

# Start server
echo "Starting server..."
nohup ./start_server.sh > server.log 2>&1 &

echo "Deployment completed!"
echo "Server is now running on port 5000"
echo "Test with: curl http://localhost:5000/health"