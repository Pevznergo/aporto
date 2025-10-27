#!/bin/bash
# CUDA Diagnostic Script
# Checks CUDA installation and PyTorch compatibility

set -e

echo "🔍 CUDA Diagnostics"
echo "==================="
echo ""

# 1. Check NVIDIA driver
echo "1️⃣ NVIDIA Driver:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    echo ""
    echo "CUDA Version from driver:"
    nvidia-smi | grep "CUDA Version" || echo "  Could not detect CUDA version"
else
    echo "  ❌ nvidia-smi not found - NVIDIA drivers not installed?"
fi
echo ""

# 2. Check CUDA toolkit installation
echo "2️⃣ CUDA Toolkit:"
if command -v nvcc &> /dev/null; then
    nvcc --version | grep "release"
else
    echo "  ℹ️  nvcc not found (CUDA toolkit not installed, but not required if drivers are OK)"
fi
echo ""

# 3. Check PyTorch installation
echo "3️⃣ PyTorch:"
if [ -f ".venv/bin/python" ]; then
    source .venv/bin/activate
    python -c "
import torch
import sys

print(f'  PyTorch version: {torch.__version__}')
print(f'  CUDA available: {torch.cuda.is_available()}')
print(f'  CUDA compiled: {torch.version.cuda if hasattr(torch.version, \"cuda\") else \"N/A\"}')

if torch.cuda.is_available():
    print(f'  Device count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')
        print(f'    Compute capability: {torch.cuda.get_device_capability(i)}')
else:
    print('  ⚠️  CUDA NOT AVAILABLE')
    print('')
    print('  Possible reasons:')
    print('  - PyTorch installed without CUDA support (CPU-only version)')
    print('  - CUDA version mismatch between PyTorch and drivers')
    print('  - NVIDIA drivers not properly installed')
    print('')
    
    # Check if torch was installed from the correct index
    import subprocess
    result = subprocess.run(['pip', 'show', 'torch'], capture_output=True, text=True)
    print('  Current torch installation:')
    for line in result.stdout.split('\n'):
        if 'Version' in line or 'Location' in line:
            print(f'    {line}')
"
else
    echo "  ❌ Virtual environment not found at .venv/"
fi
echo ""

# 4. Recommendations
echo "4️⃣ Recommendations:"
echo ""

# Check if we're in a virtual environment
if [ -f ".venv/bin/python" ]; then
    source .venv/bin/activate
    
    # Check if CUDA is available
    CUDA_AVAILABLE=$(python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "false")
    
    if [ "$CUDA_AVAILABLE" = "False" ]; then
        echo "  ⚠️  CUDA is not available. To fix:"
        echo ""
        echo "  Option 1: Reinstall PyTorch with CUDA 12.1 (recommended for most GPUs)"
        echo "    Run: bash upscale/vastai_deployment/fix_torch_cuda.sh"
        echo ""
        echo "  Option 2: Try CUDA 11.8 if you have older GPU:"
        echo "    Run: bash upscale/vastai_deployment/fix_torch_cuda.sh 11.8"
        echo ""
        echo "  Option 3: Disable CUDA requirement (not recommended):"
        echo "    Edit .env and set: CUT_REQUIRE_CUDA=0"
    else
        echo "  ✅ CUDA is working correctly!"
    fi
fi

echo ""
echo "For more help, check: /workspace/server.log"
