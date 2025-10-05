#!/usr/bin/env python3
"""
Simple test script for Vast.ai instance
"""

def test_imports():
    """Test if all required modules can be imported."""
    modules = [
        "torch",
        "cv2",
        "numpy",
        "PIL",
        "basicsr",
        "gfpgan",
        "realesrgan",
        "flask"
    ]
    
    print("Testing Python module imports...")
    print("-" * 40)
    
    failed = []
    for module in modules:
        try:
            if module == "cv2":
                import cv2
            elif module == "PIL":
                from PIL import Image
            else:
                __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            failed.append(module)
    
    print("-" * 40)
    if failed:
        print(f"Failed to import: {', '.join(failed)}")
        return False
    else:
        print("All modules imported successfully!")
        return True

def test_model_files():
    """Test if model files exist."""
    import os
    
    model_files = [
        "models/realesr-general-x4v3.pth"
    ]
    
    print("\nChecking model files...")
    print("-" * 40)
    
    missing = []
    for model_file in model_files:
        if os.path.exists(model_file):
            print(f"✅ {model_file}")
        else:
            print(f"❌ {model_file} (MISSING)")
            missing.append(model_file)
    
    print("-" * 40)
    if missing:
        print(f"Missing model files: {', '.join(missing)}")
        return False
    else:
        print("All model files found!")
        return True

def main():
    """Main test function."""
    print("Testing Video Upscaling Application on Vast.ai instance")
    print("=" * 60)
    
    imports_ok = test_imports()
    models_ok = test_model_files()
    
    print("\n" + "=" * 60)
    if imports_ok and models_ok:
        print("✅ All tests passed! Application is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit(main())