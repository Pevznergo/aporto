#!/usr/bin/env python3
"""
Migration script to add status and channel fields to clip table.
Run this once to update the database schema.
"""
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import engine

# Import text from sqlalchemy (available through SQLModel's dependencies)
try:
    from sqlmodel import text
except ImportError:
    from sqlalchemy import text

def migrate():
    print("Starting migration: add status and channel to clip table...")
    
    with engine.begin() as conn:
        # Check if we're using PostgreSQL or SQLite
        dialect = str(conn.dialect.name)
        print(f"Database dialect: {dialect}")
        
        # Try to add status column
        try:
            if dialect == 'postgresql':
                conn.execute(text("ALTER TABLE clip ADD COLUMN IF NOT EXISTS status VARCHAR"))
                print("✅ Added status column (PostgreSQL)")
            else:  # SQLite
                # SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
                # Check if column exists first
                result = conn.execute(text("PRAGMA table_info(clip)")).fetchall()
                columns = [row[1] for row in result]
                if 'status' not in columns:
                    conn.execute(text("ALTER TABLE clip ADD COLUMN status VARCHAR"))
                    print("✅ Added status column (SQLite)")
                else:
                    print("ℹ️  status column already exists")
        except Exception as e:
            print(f"⚠️  Error adding status column: {e}")
        
        # Try to add channel column
        try:
            if dialect == 'postgresql':
                conn.execute(text("ALTER TABLE clip ADD COLUMN IF NOT EXISTS channel VARCHAR"))
                print("✅ Added channel column (PostgreSQL)")
            else:  # SQLite
                result = conn.execute(text("PRAGMA table_info(clip)")).fetchall()
                columns = [row[1] for row in result]
                if 'channel' not in columns:
                    conn.execute(text("ALTER TABLE clip ADD COLUMN channel VARCHAR"))
                    print("✅ Added channel column (SQLite)")
                else:
                    print("ℹ️  channel column already exists")
        except Exception as e:
            print(f"⚠️  Error adding channel column: {e}")
    
    print("Migration completed!")

if __name__ == "__main__":
    migrate()
