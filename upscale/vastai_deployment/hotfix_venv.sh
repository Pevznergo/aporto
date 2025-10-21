#!/bin/bash
# Quick hotfix for VAST instance to use correct venv

set -e

echo "🔧 Applying venv hotfix..."

# 1. Add VENV_PYTHON to .env if not present
if ! grep -q "VENV_PYTHON" /workspace/aporto/.env 2>/dev/null; then
    echo "Adding VENV_PYTHON to .env..."
    sed -i '1i# Python interpreter (for subprocess calls)\nVENV_PYTHON=/workspace/aporto/.venv/bin/python\n' /workspace/aporto/.env
else
    echo "VENV_PYTHON already in .env"
fi

# 2. Patch basicsr degradations.py
echo "Patching basicsr..."
DEGRADATIONS_FILE=$(find /workspace/aporto/.venv -name "degradations.py" -path "*/basicsr/data/degradations.py" 2>/dev/null | head -n1)

if [ -z "$DEGRADATIONS_FILE" ]; then
    echo "❌ Could not locate basicsr degradations.py"
    exit 1
fi

echo "Found: $DEGRADATIONS_FILE"

if grep -q "from torchvision.transforms.functional_tensor import rgb_to_grayscale" "$DEGRADATIONS_FILE"; then
    cp "$DEGRADATIONS_FILE" "${DEGRADATIONS_FILE}.bak"
    sed -i 's/from torchvision\.transforms\.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/' "$DEGRADATIONS_FILE"
    echo "✅ Patched basicsr"
else
    echo "✅ basicsr already patched"
fi

# 3. Restart service
echo "Restarting service..."
systemctl restart vast-upscale.service

echo "✅ Hotfix complete!"
echo ""
echo "Check status: systemctl status vast-upscale.service"
echo "Check logs: tail -f /workspace/server.log"
