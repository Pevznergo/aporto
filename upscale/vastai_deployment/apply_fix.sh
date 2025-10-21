#!/bin/bash
# Complete fix script for VAST deployment
# Run this on the VAST server after git pull

set -e

cd /workspace/aporto

echo "🔧 Applying complete fix..."
echo ""

# 1. Patch basicsr
echo "Step 1: Patching basicsr..."
DEGRADATIONS=$(find /workspace/aporto/.venv -name "degradations.py" -path "*/basicsr/data/degradations.py" 2>/dev/null | head -n1)

if [ -z "$DEGRADATIONS" ]; then
    echo "❌ Error: Could not find basicsr degradations.py"
    echo "Is the venv activated and basicsr installed?"
    exit 1
fi

echo "Found: $DEGRADATIONS"

if grep -q "from torchvision.transforms.functional_tensor import rgb_to_grayscale" "$DEGRADATIONS"; then
    echo "Applying patch..."
    cp "$DEGRADATIONS" "${DEGRADATIONS}.bak"
    sed -i 's/from torchvision\.transforms\.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/' "$DEGRADATIONS"
    echo "✅ Patched"
else
    echo "✅ Already patched"
fi
echo ""

# 2. Ensure VENV_PYTHON is in .env
echo "Step 2: Updating .env..."
if ! grep -q "^VENV_PYTHON=" /workspace/aporto/.env 2>/dev/null; then
    echo "Adding VENV_PYTHON..."
    # Insert at the beginning of file
    tmpfile=$(mktemp)
    echo "# Python interpreter (for subprocess calls)" > "$tmpfile"
    echo "VENV_PYTHON=/workspace/aporto/.venv/bin/python" >> "$tmpfile"
    echo "" >> "$tmpfile"
    cat /workspace/aporto/.env >> "$tmpfile"
    mv "$tmpfile" /workspace/aporto/.env
    echo "✅ Added VENV_PYTHON"
else
    echo "✅ VENV_PYTHON already present"
fi
echo ""

# 3. Test imports
echo "Step 3: Testing imports..."
/workspace/aporto/.venv/bin/python3 -c "
import sys
print(f'Python: {sys.executable}')
try:
    from realesrgan.utils import RealESRGANer
    print('✅ RealESRGANer import OK')
except Exception as e:
    print(f'❌ RealESRGANer import failed: {e}')
    sys.exit(1)

try:
    from gfpgan import GFPGANer
    print('✅ GFPGANer import OK')
except Exception as e:
    print(f'❌ GFPGANer import failed: {e}')
    sys.exit(1)
"
echo ""

# 4. Restart service
echo "Step 4: Restarting service..."
systemctl restart vast-upscale.service
sleep 2
echo ""

# 5. Check service status
echo "Step 5: Service status..."
if systemctl is-active --quiet vast-upscale.service; then
    echo "✅ Service is running"
else
    echo "❌ Service is not running"
    systemctl status vast-upscale.service --no-pager | head -20
    exit 1
fi
echo ""

echo "🎉 Fix applied successfully!"
echo ""
echo "Monitor logs with: tail -f /workspace/server.log"
echo "Check service: systemctl status vast-upscale.service"
