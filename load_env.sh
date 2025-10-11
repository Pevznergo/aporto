#!/bin/bash
# Script for loading environment variables from .env file into shell environment
# Usage: source load_env.sh

if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    set -a  # Automatically export all variables
    source .env
    set +a  # Disable automatic export
    echo "Environment variables loaded successfully!"
    echo "Available env vars: OPENAI_API_KEY, VAST_*, UPSCALE_*"
else
    echo "Warning: .env file not found in current directory"
fi