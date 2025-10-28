#!/usr/bin/env python3
"""
Model validation script to check if the model files are valid and can be loaded.
This script is used during installation to verify that the downloaded model files are not corrupted.
"""

import os
import sys
import torch

def validate_model(model_path, model_name):
    """Validate that a model file exists and can be loaded."""
    print(f"Validating {model_name}...")
    
    # Check if file exists
    if not os.path.exists(model_path):
        print(f"❌ {model_name} not found at {model_path}")
        return False
    
    # Check if file is not empty
    if os.path.getsize(model_path) == 0:
        print(f"❌ {model_name} is empty")
        return False
    
    # Try to load the model file
    try:
        torch.load(model_path, map_location=torch.device('cpu'))
        print(f"✅ {model_name} is valid")
        return True
    except Exception as e:
        print(f"❌ {model_name} is corrupted: {e}")
        return False

def main():
    """Main function to validate all model files."""
    print("🔍 Validating model files...")
    
    # Define model files to validate
    models = [
        ("models/GFPGANv1.4.pth", "GFPGAN"),
        ("models/realesr-general-x4v3.pth", "Real-ESRGAN")
    ]
    
    all_valid = True
    
    for model_path, model_name in models:
        # Check if we're in the right directory
        if not os.path.exists(model_path):
            # Try to find the model in the upscale directory
            upscale_model_path = os.path.join("upscale", model_path)
            if os.path.exists(upscale_model_path):
                model_path = upscale_model_path
            else:
                # Try with absolute path from workspace
                workspace_model_path = os.path.join("/workspace/aporto", model_path)
                if os.path.exists(workspace_model_path):
                    model_path = workspace_model_path
        
        if not validate_model(model_path, model_name):
            all_valid = False
    
    if all_valid:
        print("\n🎉 All model files are valid!")
        return 0
    else:
        print("\n❌ Some model files are invalid or missing!")
        return 1

if __name__ == "__main__":
    sys.exit(main())