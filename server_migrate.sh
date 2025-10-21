#!/bin/bash
# Server Database Migration Script
# Migrates SQLite to PostgreSQL on production server

set -e  # Exit on any error

echo "🚀 Aporto Database Migration Script"
echo "===================================="

# Load environment variables
if [ -f .env ]; then
    echo "📋 Loading environment variables..."
    source load_env.sh
else
    echo "❌ .env file not found. Please create it first."
    exit 1
fi

# Check if POSTGRES_URL is set
if [ -z "$POSTGRES_URL" ]; then
    echo "❌ POSTGRES_URL is not set in environment variables"
    echo "💡 Please add your Neon PostgreSQL URL to .env file:"
    echo "   POSTGRES_URL=postgresql://username:password@host/database"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  test      - Test PostgreSQL connection only"
    echo "  init      - Initialize PostgreSQL database tables"
    echo "  info      - Show database information and statistics"
    echo "  migrate   - Migrate data from SQLite to PostgreSQL"
    echo "  full      - Full migration: init + migrate (default)"
    echo ""
    echo "Environment:"
    echo "  POSTGRES_URL - PostgreSQL connection URL (required)"
    echo "  SQLite file  - app.db (default)"
    echo ""
}

# Parse command
COMMAND=${1:-full}

case $COMMAND in
    "test")
        echo "🔍 Testing PostgreSQL connection..."
        python3 init_postgres.py --test-only
        ;;
    
    "init")
        echo "🏗️  Initializing PostgreSQL database..."
        python3 init_postgres.py
        ;;
    
    "info")
        echo "📊 Getting database information..."
        python3 init_postgres.py --info-only
        ;;
    
    "migrate")
        echo "📦 Migrating data from SQLite to PostgreSQL..."
        
        # Check if SQLite database exists
        if [ ! -f "app.db" ]; then
            echo "⚠️  No app.db file found. Nothing to migrate."
            echo "💡 If you have a different SQLite file, run:"
            echo "   python3 migrate_db.py --sqlite /path/to/your/database.db"
            exit 0
        fi
        
        # Show SQLite file info
        echo "📁 SQLite database found: app.db"
        echo "   Size: $(du -h app.db | cut -f1)"
        echo "   Modified: $(stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' app.db 2>/dev/null || stat -c '%y' app.db 2>/dev/null || echo 'unknown')"
        echo ""
        
        # Ask for confirmation
        read -p "🤔 Do you want to proceed with migration? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Migration cancelled by user"
            exit 0
        fi
        
        # Run migration
        python3 migrate_db.py
        ;;
    
    "full")
        echo "🔄 Full migration: Initialize + Migrate"
        echo ""
        
        # Step 1: Initialize PostgreSQL
        echo "Step 1: Initializing PostgreSQL database..."
        python3 init_postgres.py
        echo ""
        
        # Step 2: Migrate data if SQLite exists
        if [ -f "app.db" ]; then
            echo "Step 2: Migrating data..."
            read -p "🤔 Proceed with data migration? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                python3 migrate_db.py
            else
                echo "⏭️  Data migration skipped by user"
            fi
        else
            echo "Step 2: No SQLite database found, skipping data migration"
        fi
        
        echo ""
        echo "Step 3: Final database information..."
        python3 init_postgres.py --info-only
        ;;
    
    "help"|"-h"|"--help")
        show_usage
        exit 0
        ;;
    
    *)
        echo "❌ Unknown command: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac

echo ""
echo "✅ Operation completed successfully!"
echo ""
echo "💡 Next steps:"
echo "   1. Make sure POSTGRES_URL is set in your .env file"
echo "   2. Restart your application to use PostgreSQL"
echo "   3. Monitor logs to ensure everything works correctly"
echo ""
echo "🔧 Useful commands:"
echo "   ./check_env.sh          - Check environment variables"
echo "   ./server_migrate.sh info - Show database statistics"