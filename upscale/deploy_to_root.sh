#!/bin/bash

# Deployment script to download upscale folder contents to root directory
# This script should be run on a Vast.ai instance

echo "Deploying upscale application to root directory..."

# Install git if not already installed
apt-get update
apt-get install -y git

# Clone repository to temporary location
cd /tmp
rm -rf upscale-repo 2>/dev/null
git clone https://github.com/YOUR_USERNAME/video-upscale-vastai.git upscale-repo
cd upscale-repo

# Copy all files to workspace root
echo "Copying files to /workspace..."
cp -r * /workspace/

# Go to workspace
cd /workspace

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