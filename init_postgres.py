#!/usr/bin/env python3
"""
PostgreSQL Database Initialization Script
Initialize tables and check connection to Neon PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel, Session

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Task, UpscaleTask, DownloadedVideo, Clip, ClipFragment


def test_connection(postgres_url: str) -> bool:
    """Test PostgreSQL connection"""
    try:
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version[:60]}...")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def init_database(postgres_url: str) -> bool:
    """Initialize database tables"""
    print("🏗️  Initializing database tables...")
    
    try:
        engine = create_engine(postgres_url, echo=False)
        
        # Create all tables
        SQLModel.metadata.create_all(engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            # Get list of tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"✅ Created/verified {len(tables)} tables:")
            for table in tables:
                print(f"  📄 {table}")
            
            # Check if our expected tables exist
            expected_tables = {'task', 'upscaletask', 'downloadedvideo', 'clip', 'clipfragment'}
            missing_tables = expected_tables - set(tables)
            
            if missing_tables:
                print(f"⚠️  Missing expected tables: {missing_tables}")
                return False
            
            print("✅ All expected tables are present")
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def get_database_info(postgres_url: str):
    """Get database information and statistics"""
    try:
        engine = create_engine(postgres_url)
        
        with engine.connect() as conn:
            # Database info
            result = conn.execute(text("SELECT current_database(), current_user;"))
            db_name, db_user = result.fetchone()
            print(f"📊 Database: {db_name} (user: {db_user})")
            
            # Table statistics
            print("\n📋 Table Statistics:")
            tables_info = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables 
                ORDER BY tablename;
            """)).fetchall()
            
            if tables_info:
                for row in tables_info:
                    schema, table, inserts, updates, deletes, live, dead = row
                    print(f"  📄 {table}: {live} records ({inserts} inserts, {updates} updates, {deletes} deletes)")
            else:
                print("  No user tables found or statistics not available")
                
        # Using SQLModel to get counts
        print("\n📊 Record Counts:")
        with Session(engine) as session:
            try:
                from sqlmodel import select
                task_count = len(session.exec(select(Task)).all())
                print(f"  📋 Tasks: {task_count}")
            except Exception:
                print("  📋 Tasks: table not accessible")
                
            try:
                upscale_count = len(session.exec(select(UpscaleTask)).all())
                print(f"  🚀 Upscale Tasks: {upscale_count}")
            except Exception:
                print("  🚀 Upscale Tasks: table not accessible")
                
            try:
                video_count = len(session.exec(select(DownloadedVideo)).all())
                print(f"  🎥 Downloaded Videos: {video_count}")
            except Exception:
                print("  🎥 Downloaded Videos: table not accessible")
                
            try:
                clip_count = len(session.exec(select(Clip)).all())
                print(f"  🎬 Clips: {clip_count}")
            except Exception:
                print("  🎬 Clips: table not accessible")
                
            try:
                fragment_count = len(session.exec(select(ClipFragment)).all())
                print(f"  🧩 Clip Fragments: {fragment_count}")
            except Exception:
                print("  🧩 Clip Fragments: table not accessible")
                
    except Exception as e:
        print(f"❌ Failed to get database info: {e}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize PostgreSQL database")
    parser.add_argument("--postgres", help="PostgreSQL connection URL")
    parser.add_argument("--test-only", action="store_true", help="Only test connection, don't initialize")
    parser.add_argument("--info-only", action="store_true", help="Only show database info")
    
    args = parser.parse_args()
    
    # Get PostgreSQL URL from environment or argument
    postgres_url = args.postgres or os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("❌ PostgreSQL URL not provided. Use --postgres argument or set POSTGRES_URL environment variable")
        return 1
    
    print("🐘 PostgreSQL Database Initialization")
    print("=" * 50)
    print(f"Database: {postgres_url[:50]}...")
    print()
    
    # Test connection
    if not test_connection(postgres_url):
        return 1
    
    if args.test_only:
        print("✅ Connection test completed successfully")
        return 0
    
    # Show database info
    if args.info_only:
        get_database_info(postgres_url)
        return 0
    
    # Initialize database
    if not init_database(postgres_url):
        return 1
    
    print()
    get_database_info(postgres_url)
    
    print("\n🎉 Database initialization completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())