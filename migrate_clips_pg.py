#!/usr/bin/env python3
"""
PostgreSQL migration: add status and channel to clip table
"""
import os
import psycopg2
from urllib.parse import urlparse

# Get PostgreSQL URL from environment
postgres_url = os.getenv('POSTGRES_URL')

if not postgres_url:
    print("❌ POSTGRES_URL not set in environment")
    exit(1)

print("🔧 PostgreSQL Migration for Clips")
print(f"Database: {urlparse(postgres_url).netloc}")
print()

try:
    # Connect to database
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    print("✅ Connected to database")
    print()
    
    # Add status column
    print("Adding status column...")
    try:
        cursor.execute("ALTER TABLE clip ADD COLUMN IF NOT EXISTS status VARCHAR")
        conn.commit()
        print("  ✅ status column added")
    except Exception as e:
        print(f"  ℹ️  {e}")
        conn.rollback()
    
    # Add channel column
    print("Adding channel column...")
    try:
        cursor.execute("ALTER TABLE clip ADD COLUMN IF NOT EXISTS channel VARCHAR")
        conn.commit()
        print("  ✅ channel column added")
    except Exception as e:
        print(f"  ℹ️  {e}")
        conn.rollback()
    
    # Verify columns exist
    print()
    print("Verifying columns...")
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'clip' 
        AND column_name IN ('status', 'channel')
        ORDER BY column_name
    """)
    columns = [row[0] for row in cursor.fetchall()]
    
    if 'status' in columns and 'channel' in columns:
        print("  ✅ Both columns confirmed in database")
    else:
        print(f"  ⚠️  Found columns: {columns}")
    
    cursor.close()
    conn.close()
    
    print()
    print("🎉 Migration completed successfully!")
    print()
    print("Next steps:")
    print("1. Restart backend: sudo systemctl restart aporto-api")
    print("2. Refresh frontend in browser")
    print("3. Go to Clips tab and test status/channel dropdowns")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    exit(1)
