#!/bin/bash
# Quick apply script for clips status/channel feature

set -e

echo "🔧 Applying clips status/channel feature..."
echo ""

# 1. Apply database migration
echo "📊 Step 1: Applying database migration..."
python3 migrate_add_clip_fields.py
echo ""

# 2. Restart backend
echo "🔄 Step 2: Restarting backend..."
if systemctl is-active --quiet aporto-api 2>/dev/null; then
    echo "  Using systemd..."
    sudo systemctl restart aporto-api
    echo "  ✅ Backend restarted via systemd"
else
    echo "  ⚠️  systemd service not found"
    echo "  Please restart backend manually:"
    echo "    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
fi
echo ""

# 3. Check if frontend needs rebuild
echo "📦 Step 3: Checking frontend..."
if [ -d "web/node_modules" ]; then
    echo "  Frontend found at web/"
    if [ -f "web/.next/BUILD_ID" ]; then
        echo "  ⚠️  Production build detected"
        echo "  To apply frontend changes, run:"
        echo "    cd web && npm run build && npm run start"
    else
        echo "  ✅ Dev mode - changes will be applied automatically"
    fi
else
    echo "  ℹ️  No frontend directory found"
fi
echo ""

echo "🎉 Migration completed!"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 (or your frontend URL)"
echo "2. Go to Clips tab"
echo "3. Try changing Status or Channel for any clip"
echo "4. Check that values persist after page refresh"
echo ""
echo "For full documentation, see: CLIPS_STATUS_CHANNEL_UPDATE.md"
