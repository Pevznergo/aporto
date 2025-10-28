#!/bin/bash
# Script to fix corrupted or missing model files for Real-ESRGAN and GFPGAN
# This script will download fresh copies of the model files if they are missing or corrupted

set -e

echo "Fixing model files for Real-ESRGAN and GFPGAN..."

# Create models directory if it doesn't exist
mkdir -p models

# Function to check if a file is valid (not empty and can be loaded by Python)
check_file_valid() {
    local file_path="$1"
    
    # Check if file exists
    if [ ! -f "$file_path" ]; then
        echo "File not found: $file_path"
        return 1
    fi
    
    # Check if file is not empty
    if [ ! -s "$file_path" ]; then
        echo "File is empty: $file_path"
        return 1
    fi
    
    # Try to load the file with Python to check if it's valid
    python3 -c "
import torch
try:
    torch.load('$file_path', map_location=torch.device('cpu'))
    exit(0)
except Exception as e:
    print(f'File is corrupted: {e}')
    exit(1)
" 2>/dev/null
    
    return $?
}

# Fix Real-ESRGAN model
REAL_ESRGAN_PATH="models/realesr-general-x4v3.pth"
if check_file_valid "$REAL_ESRGAN_PATH"; then
    echo "Real-ESRGAN model is already valid."
else
    echo "Fixing Real-ESRGAN model..."
    # Remove corrupted file if it exists
    if [ -f "$REAL_ESRGAN_PATH" ]; then
        echo "Removing corrupted Real-ESRGAN model file..."
        rm "$REAL_ESRGAN_PATH"
    fi
    
    # Download fresh copy
    echo "Downloading fresh Real-ESRGAN model..."
    wget -O "$REAL_ESRGAN_PATH" "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth"
    
    # Validate the downloaded file
    if check_file_valid "$REAL_ESRGAN_PATH"; then
        echo "Successfully fixed Real-ESRGAN model!"
    else
        echo "Failed to validate downloaded Real-ESRGAN model."
        exit 1
    fi
fi

# Fix GFPGAN model
GFPGAN_PATH="models/GFPGANv1.4.pth"
if check_file_valid "$GFPGAN_PATH"; then
    echo "GFPGAN model is already valid."
else
    echo "Fixing GFPGAN model..."
    # Remove corrupted file if it exists
    if [ -f "$GFPGAN_PATH" ]; then
        echo "Removing corrupted GFPGAN model file..."
        rm "$GFPGAN_PATH"
    fi
    
    # Download fresh copy
    echo "Downloading fresh GFPGAN model..."
    wget -O "$GFPGAN_PATH" "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"
    
    # Validate the downloaded file
    if check_file_valid "$GFPGAN_PATH"; then
        echo "Successfully fixed GFPGAN model!"
    else
        echo "Failed to validate downloaded GFPGAN model."
        exit 1
    fi
fi

echo ""
echo "Model files have been fixed successfully!"
echo "You can now restart your upscaling service."