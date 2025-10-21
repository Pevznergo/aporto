#!/bin/bash
# Diagnostic script to check VAST server state

echo "=== VAST Server Diagnostics ==="
echo ""

echo "1. Current Python executable:"
which python3
python3 --version
echo ""

echo "2. Virtual environment status:"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo "VENV_PYTHON env var: $VENV_PYTHON"
echo ""

echo "3. Check .env file:"
if [ -f /workspace/aporto/.env ]; then
    echo "Content:"
    cat /workspace/aporto/.env
else
    echo "❌ .env not found"
fi
echo ""

echo "4. Check basicsr degradations.py:"
DEGRADATIONS=$(find /workspace/aporto/.venv -name "degradations.py" -path "*/basicsr/data/degradations.py" 2>/dev/null | head -n1)
if [ -n "$DEGRADATIONS" ]; then
    echo "Found: $DEGRADATIONS"
    if grep -q "functional_tensor" "$DEGRADATIONS"; then
        echo "❌ Still has OLD import (functional_tensor)"
        echo "Line 8:"
        sed -n '8p' "$DEGRADATIONS"
    else
        echo "✅ Patched correctly"
        echo "Line 8:"
        sed -n '8p' "$DEGRADATIONS"
    fi
else
    echo "❌ degradations.py not found"
fi
echo ""

echo "5. Test imports in correct venv:"
/workspace/aporto/.venv/bin/python3 -c "
try:
    from realesrgan.utils import RealESRGANer
    print('✅ RealESRGANer import OK')
except Exception as e:
    print(f'❌ RealESRGANer import failed: {e}')

try:
    from gfpgan import GFPGANer
    print('✅ GFPGANer import OK')
except Exception as e:
    print(f'❌ GFPGANer import failed: {e}')
"
echo ""

echo "6. Service status:"
systemctl status vast-upscale.service --no-pager | head -20
echo ""

echo "7. Recent logs:"
tail -30 /workspace/server.log
