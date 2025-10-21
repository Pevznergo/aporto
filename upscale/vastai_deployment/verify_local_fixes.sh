#!/bin/bash
# Verify that all local fixes are in place before pushing to git

echo "🔍 Verifying local fixes..."
echo ""

cd "$(dirname "$0")"
REPO_ROOT="$(cd ../.. && pwd)"

errors=0

# 1. Check upscale_app.py has VENV_PYTHON
echo "1. Checking upscale_app.py..."
if grep -q "VENV_PYTHON" upscale_app.py; then
    echo "   ✅ VENV_PYTHON support found"
else
    echo "   ❌ VENV_PYTHON support missing"
    errors=$((errors + 1))
fi

# 2. Check install.sh has VENV_PYTHON in .env
echo "2. Checking install.sh..."
if grep -q "VENV_PYTHON=/workspace/aporto/.venv/bin/python" install.sh; then
    echo "   ✅ VENV_PYTHON in .env template"
else
    echo "   ❌ VENV_PYTHON missing from .env template"
    errors=$((errors + 1))
fi

# 3. Check install.sh has basicsr patch
echo "3. Checking install.sh for basicsr patch..."
if grep -q "Patching basicsr" install.sh; then
    echo "   ✅ basicsr patch code present"
else
    echo "   ❌ basicsr patch missing"
    errors=$((errors + 1))
fi

# 4. Check requirements.txt versions
echo "4. Checking requirements.txt..."
if grep -q "torch==2.4.1" requirements.txt && \
   grep -q "torchvision==0.19.1" requirements.txt; then
    echo "   ✅ PyTorch versions pinned correctly"
else
    echo "   ❌ PyTorch versions not pinned correctly"
    errors=$((errors + 1))
fi

# 5. Check helper scripts exist
echo "5. Checking helper scripts..."
scripts=("apply_fix.sh" "diagnose.sh" "fix_basicsr.sh" "FIX_INSTRUCTIONS.md")
for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "   ✅ $script exists"
    else
        echo "   ❌ $script missing"
        errors=$((errors + 1))
    fi
done

echo ""
if [ $errors -eq 0 ]; then
    echo "🎉 All checks passed! Safe to push."
    echo ""
    echo "Next steps:"
    echo "  git add ."
    echo "  git commit -m 'Fix: VAST deployment venv and basicsr compatibility'"
    echo "  git push origin main"
    exit 0
else
    echo "❌ Found $errors error(s). Please fix before pushing."
    exit 1
fi
