#!/bin/bash

# Setup script for Vast.ai instance
echo "Setting up Video Upscaling Application on Vast.ai instance..."

# Update package list
apt-get update

# Install system dependencies
apt-get install -y python3 python3-pip git wget ffmpeg openssh-client unzip

# Upgrade pip
pip3 install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Download Real-ESRGAN models
echo "Downloading Real-ESRGAN models..."
mkdir -p models
if [ ! -f "models/realesr-general-x4v3.pth" ]; then
    echo "Downloading realesr-general-x4v3 model..."
    wget -O models/realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
else
    echo "Real-ESRGAN model already exists"
fi

# Make scripts executable
chmod +x run_upscale.sh
chmod +x start_server.sh

echo "Setup completed successfully!"
echo "You can now start the server with: ./start_server.sh"