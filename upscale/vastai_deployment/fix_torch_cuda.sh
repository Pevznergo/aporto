#!/bin/bash
# Fix PyTorch CUDA Installation
# Reinstalls PyTorch with proper CUDA support

set -e

CUDA_VERSION="${1:-12.1}"  # Default to CUDA 12.1, or use argument

echo "🔧 Fixing PyTorch CUDA Installation"
echo "===================================="
echo ""
echo "Target CUDA version: $CUDA_VERSION"
echo ""

# Activate virtual environment
if [ ! -f ".venv/bin/activate" ]; then
    echo "❌ Virtual environment not found at .venv/"
    echo "Please run install.sh first"
    exit 1
fi

source .venv/bin/activate

# Determine the correct PyTorch index URL based on CUDA version
if [ "$CUDA_VERSION" = "12.1" ]; then
    INDEX_URL="https://download.pytorch.org/whl/cu121"
    echo "Using CUDA 12.1 wheels"
elif [ "$CUDA_VERSION" = "11.8" ]; then
    INDEX_URL="https://download.pytorch.org/whl/cu118"
    echo "Using CUDA 11.8 wheels"
elif [ "$CUDA_VERSION" = "cpu" ]; then
    INDEX_URL="https://download.pytorch.org/whl/cpu"
    echo "⚠️  Using CPU-only version (CUDA will NOT work)"
else
    echo "❌ Unsupported CUDA version: $CUDA_VERSION"
    echo "Supported versions: 12.1, 11.8, cpu"
    exit 1
fi

echo ""
echo "1️⃣ Checking current NVIDIA driver..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=driver_version --format=csv,noheader
    DRIVER_CUDA=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' || echo "unknown")
    echo "   Driver CUDA version: $DRIVER_CUDA"
else
    echo "   ⚠️  nvidia-smi not found"
fi

echo ""
echo "2️⃣ Uninstalling current PyTorch..."
pip uninstall -y torch torchvision torchaudio || true

echo ""
echo "3️⃣ Installing PyTorch with CUDA $CUDA_VERSION..."
pip install --no-cache-dir \
    --extra-index-url "$INDEX_URL" \
    torch==2.4.1 \
    torchvision==0.19.1 \
    torchaudio==2.4.1

echo ""
echo "4️⃣ Verifying installation..."
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA compiled version: {torch.version.cuda if hasattr(torch.version, \"cuda\") else \"N/A\"}')
print(f'CUDA available: {torch.cuda.is_available()}')

if torch.cuda.is_available():
    print(f'✅ CUDA is working!')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'Device count: {torch.cuda.device_count()}')
    
    # Test a simple CUDA operation
    try:
        x = torch.rand(3, 3).cuda()
        print(f'✅ CUDA tensor test passed')
    except Exception as e:
        print(f'⚠️  CUDA tensor test failed: {e}')
else:
    print('❌ CUDA is still NOT available')
    print('')
    print('Possible issues:')
    print('1. NVIDIA drivers not installed or not working')
    print('2. Driver CUDA version is too old for PyTorch CUDA $CUDA_VERSION')
    print('3. GPU not properly detected by the system')
    print('')
    print('Try running: nvidia-smi')
"

CUDA_STATUS=$?

echo ""
if [ $CUDA_STATUS -eq 0 ]; then
    echo "✅ PyTorch CUDA installation successful!"
    echo ""
    echo "Next steps:"
    echo "1. Restart the server: systemctl restart vast-upscale.service"
    echo "2. Check logs: tail -f /workspace/server.log"
else
    echo "❌ CUDA is still not working"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check NVIDIA drivers: nvidia-smi"
    echo "2. Try different CUDA version: bash $0 11.8"
    echo "3. Check server logs: tail -f /workspace/server.log"
fi

echo ""
