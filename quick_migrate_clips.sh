#!/bin/bash
# Quick migration script for adding status and channel to clips table

set -e

echo "🔧 Quick Clips Migration"
echo ""

# Check if PostgreSQL or SQLite
if [ -n "$POSTGRES_URL" ]; then
    echo "📊 Detected PostgreSQL"
    echo ""
    echo "Adding status column..."
    psql "$POSTGRES_URL" -c "ALTER TABLE clip ADD COLUMN IF NOT EXISTS status VARCHAR;" || echo "  (column may already exist)"
    
    echo "Adding channel column..."
    psql "$POSTGRES_URL" -c "ALTER TABLE clip ADD COLUMN IF NOT EXISTS channel VARCHAR;" || echo "  (column may already exist)"
    
    echo ""
    echo "✅ PostgreSQL migration complete!"
    
elif [ -f "app.db" ]; then
    echo "📊 Detected SQLite (app.db)"
    echo ""
    echo "Adding status column..."
    sqlite3 app.db "ALTER TABLE clip ADD COLUMN status VARCHAR;" 2>/dev/null || echo "  ℹ️  status column already exists"
    
    echo "Adding channel column..."
    sqlite3 app.db "ALTER TABLE clip ADD COLUMN channel VARCHAR;" 2>/dev/null || echo "  ℹ️  channel column already exists"
    
    echo ""
    echo "✅ SQLite migration complete!"
    
else
    echo "❌ Database not found!"
    echo ""
    echo "Please set POSTGRES_URL environment variable or ensure app.db exists"
    exit 1
fi

echo ""
echo "Next steps:"
echo "1. Restart backend:"
echo "   sudo systemctl restart aporto-api"
echo ""
echo "2. Test on Clips tab - change status/channel"
