#!/usr/bin/env python3
"""
Simple migration script to add status and channel fields to clip table.
Uses raw SQL commands compatible with both PostgreSQL and SQLite.
"""
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate():
    print("Starting migration: add status and channel to clip table...")
    
    # Import after path is set
    from app.db import engine
    
    with engine.begin() as conn:
        # Check dialect
        dialect = str(conn.dialect.name).lower()
        print(f"Database dialect: {dialect}")
        
        # Get raw connection
        raw_conn = conn.connection
        cursor = raw_conn.cursor()
        
        # Try to add status column
        try:
            if dialect == 'postgresql':
                print("  Adding status column (PostgreSQL)...")
                cursor.execute("ALTER TABLE clip ADD COLUMN IF NOT EXISTS status VARCHAR")
                print("  ✅ Added status column")
            else:  # SQLite
                print("  Checking if status column exists (SQLite)...")
                cursor.execute("PRAGMA table_info(clip)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'status' not in columns:
                    print("  Adding status column...")
                    cursor.execute("ALTER TABLE clip ADD COLUMN status VARCHAR")
                    print("  ✅ Added status column")
                else:
                    print("  ℹ️  status column already exists")
        except Exception as e:
            print(f"  ⚠️  Error with status column: {e}")
        
        # Try to add channel column
        try:
            if dialect == 'postgresql':
                print("  Adding channel column (PostgreSQL)...")
                cursor.execute("ALTER TABLE clip ADD COLUMN IF NOT EXISTS channel VARCHAR")
                print("  ✅ Added channel column")
            else:  # SQLite
                print("  Checking if channel column exists (SQLite)...")
                cursor.execute("PRAGMA table_info(clip)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'channel' not in columns:
                    print("  Adding channel column...")
                    cursor.execute("ALTER TABLE clip ADD COLUMN channel VARCHAR")
                    print("  ✅ Added channel column")
                else:
                    print("  ℹ️  channel column already exists")
        except Exception as e:
            print(f"  ⚠️  Error with channel column: {e}")
        
        # Commit is automatic with engine.begin()
    
    print("\n✅ Migration completed!")
    print("\nNext steps:")
    print("1. Restart backend: sudo systemctl restart aporto-api")
    print("2. Refresh frontend page")
    print("3. Go to Clips tab and test status/channel selects")

if __name__ == "__main__":
    migrate()
