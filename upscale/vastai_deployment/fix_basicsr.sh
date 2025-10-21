#!/bin/bash
# Quick fix for basicsr torchvision compatibility issue
# Run this in your activated venv on the VAST instance

set -e

echo "🩹 Fixing basicsr torchvision import..."

# Activate venv if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source /workspace/aporto/.venv/bin/activate
fi

# Find the degradations.py file
DEGRADATIONS_FILE=$(python3 -c "
import sys
try:
    import basicsr.data.degradations as d
    import inspect
    print(inspect.getfile(d))
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
")

if [ -z "$DEGRADATIONS_FILE" ]; then
    echo "❌ Could not locate basicsr.data.degradations module"
    exit 1
fi

echo "📁 Found file: $DEGRADATIONS_FILE"

# Check if patch is needed
if grep -q "from torchvision.transforms.functional_tensor import rgb_to_grayscale" "$DEGRADATIONS_FILE"; then
    echo "🔧 Applying patch..."
    # Backup original
    cp "$DEGRADATIONS_FILE" "${DEGRADATIONS_FILE}.bak"
    echo "   Backup created: ${DEGRADATIONS_FILE}.bak"
    
    # Apply fix
    sed -i 's/from torchvision\.transforms\.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/' "$DEGRADATIONS_FILE"
    
    echo "✅ Patch applied successfully!"
else
    echo "✅ File already patched or no patch needed"
fi

# Test the import
echo "🧪 Testing import..."
python3 -c "
import torch
import torchvision
from realesrgan.utils import RealESRGANer
from gfpgan import GFPGANer
print('✅ All imports successful!')
print(f'PyTorch: {torch.__version__}')
print(f'TorchVision: {torchvision.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"

echo "🎉 Fix complete!"
