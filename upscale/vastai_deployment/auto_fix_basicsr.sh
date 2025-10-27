#!/bin/bash
# Automatic basicsr patch for torchvision compatibility
# This script can be run standalone or as part of setup
# It handles both venv and system-wide installations

set -e

echo "🩹 Auto-patching basicsr for torchvision compatibility..."

# Function to patch a file
patch_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        return 1
    fi
    
    if grep -q "from torchvision.transforms.functional_tensor import rgb_to_grayscale" "$file"; then
        echo "  📝 Patching: $file"
        cp "$file" "${file}.bak.$(date +%Y%m%d_%H%M%S)"
        sed -i 's/from torchvision\.transforms\.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/' "$file"
        echo "  ✅ Patched successfully"
        return 0
    else
        echo "  ✅ Already patched: $file"
        return 0
    fi
}

# Try multiple search strategies
FOUND=0

# Strategy 1: Search in venv (if exists)
if [ -d "/workspace/aporto/.venv" ]; then
    echo "Searching in venv..."
    DEGRADATIONS=$(find /workspace/aporto/.venv -name "degradations.py" -path "*/basicsr/data/degradations.py" 2>/dev/null | head -n1)
    if [ -n "$DEGRADATIONS" ]; then
        patch_file "$DEGRADATIONS" && FOUND=1
    fi
fi

# Strategy 2: Search in system-wide python packages
if [ $FOUND -eq 0 ]; then
    echo "Searching in system packages..."
    DEGRADATIONS=$(find /usr/local/lib -name "degradations.py" -path "*/basicsr/data/degradations.py" 2>/dev/null | head -n1)
    if [ -n "$DEGRADATIONS" ]; then
        patch_file "$DEGRADATIONS" && FOUND=1
    fi
fi

# Strategy 3: Use python to locate the module
if [ $FOUND -eq 0 ]; then
    echo "Searching using Python import..."
    
    # Try with venv python if available
    if [ -f "/workspace/aporto/.venv/bin/python3" ]; then
        DEGRADATIONS=$(/workspace/aporto/.venv/bin/python3 -c "import basicsr.data.degradations as m; print(m.__file__)" 2>/dev/null || echo "")
    else
        DEGRADATIONS=$(python3 -c "import basicsr.data.degradations as m; print(m.__file__)" 2>/dev/null || echo "")
    fi
    
    if [ -n "$DEGRADATIONS" ] && [ "$DEGRADATIONS" != "None" ]; then
        patch_file "$DEGRADATIONS" && FOUND=1
    fi
fi

# Strategy 4: Search in all common locations
if [ $FOUND -eq 0 ]; then
    echo "Searching in all common locations..."
    for py_dir in /usr/local/lib/python*/dist-packages /usr/lib/python*/dist-packages ~/.local/lib/python*/site-packages; do
        if [ -d "$py_dir" ]; then
            DEGRADATIONS=$(find "$py_dir" -name "degradations.py" -path "*/basicsr/data/degradations.py" 2>/dev/null | head -n1)
            if [ -n "$DEGRADATIONS" ]; then
                patch_file "$DEGRADATIONS" && FOUND=1
                break
            fi
        fi
    done
fi

if [ $FOUND -eq 0 ]; then
    echo "⚠️  basicsr degradations.py not found"
    echo "   This is normal if basicsr hasn't been installed yet"
    echo "   The fix will be applied when basicsr is installed"
    exit 0
fi

echo "🎉 Patch complete!"

# Verify the fix
echo ""
echo "🧪 Verifying fix..."
PYTHON_CMD="python3"
if [ -f "/workspace/aporto/.venv/bin/python3" ]; then
    PYTHON_CMD="/workspace/aporto/.venv/bin/python3"
fi

$PYTHON_CMD -c "
try:
    from realesrgan.utils import RealESRGANer
    print('✅ RealESRGANer import successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    exit(1)
" || echo "⚠️  Verification failed, but patch was applied"

exit 0
