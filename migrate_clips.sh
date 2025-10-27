#!/bin/bash
# PostgreSQL migration: add status and channel to clip table

set -e

echo "🔧 PostgreSQL Migration for Clips"
echo ""

# Check if POSTGRES_URL is set
if [ -z "$POSTGRES_URL" ]; then
    echo "❌ POSTGRES_URL not set"
    echo "Export it first: export POSTGRES_URL='your_postgres_url'"
    exit 1
fi

echo "✅ POSTGRES_URL found"
echo ""

echo "Adding status column..."
psql "$POSTGRES_URL" -c "ALTER TABLE clip ADD COLUMN IF NOT EXISTS status VARCHAR;" && echo "  ✅ status column added"

echo "Adding channel column..."
psql "$POSTGRES_URL" -c "ALTER TABLE clip ADD COLUMN IF NOT EXISTS channel VARCHAR;" && echo "  ✅ channel column added"

echo ""
echo "Verifying columns..."
psql "$POSTGRES_URL" -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'clip' AND column_name IN ('status', 'channel') ORDER BY column_name;"

echo ""
echo "🎉 Migration completed!"
echo ""
echo "Next steps:"
echo "1. Restart backend: sudo systemctl restart aporto-api"
echo "2. Refresh frontend"
echo "3. Test on Clips tab"
