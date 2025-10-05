#!/bin/bash

# Setup script for Video Upscaling Application
echo "Setting up Video Upscaling Application..."

# Update package list
echo "Updating package list..."
apt-get update

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y python3 python3-pip git wget ffmpeg openssh-client

# Upgrade pip
echo "Upgrading pip..."
pip3 install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Download Real-ESRGAN models
echo "Downloading Real-ESRGAN models..."
mkdir -p models
wget -O models/realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth

echo "Setup completed successfully!"
echo "You can now run the application with:"
echo "  python upscale_app.py <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>"