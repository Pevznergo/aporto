#!/bin/bash

# Video Upscaling Script for Vast.ai L4 Server
# Usage: ./run_upscale.sh <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>"
    echo "Example: $0 user 192.168.1.100 /path/to/input.mp4 /path/to/output.mp4"
    exit 1
fi

SSH_USER=$1
SSH_HOST=$2
REMOTE_INPUT_PATH=$3
REMOTE_OUTPUT_PATH=$4

echo "Starting video upscaling process..."
echo "SSH User: $SSH_USER"
echo "SSH Host: $SSH_HOST"
echo "Remote Input: $REMOTE_INPUT_PATH"
echo "Remote Output: $REMOTE_OUTPUT_PATH"

# Run the upscaling application
python upscale_app.py "$SSH_USER" "$SSH_HOST" "$REMOTE_INPUT_PATH" "$REMOTE_OUTPUT_PATH"

if [ $? -eq 0 ]; then
    echo "Video upscaling completed successfully!"
else
    echo "Video upscaling failed!"
    exit 1
fi