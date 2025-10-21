#!/usr/bin/env python3
"""
Database Migration Script: SQLite to PostgreSQL
Migrates data from local SQLite database to PostgreSQL (Neon)
"""

import os
import sys
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlmodel import Session, select
import json

# Add current directory to Python path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Task, UpscaleTask, DownloadedVideo, TaskStatus, UpscaleStatus


class DatabaseMigrator:
    def __init__(self, sqlite_path: str, postgres_url: str):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.sqlite_conn = None
        self.postgres_engine = None
        
    def connect(self):
        """Connect to both databases"""
        print("🔌 Connecting to databases...")
        
        # SQLite connection
        if not os.path.exists(self.sqlite_path):
            print(f"❌ SQLite database not found at: {self.sqlite_path}")
            return False
            
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row  # Enable dict-like access
        print(f"✅ Connected to SQLite: {self.sqlite_path}")
        
        # PostgreSQL connection
        try:
            self.postgres_engine = create_engine(self.postgres_url)
            # Test connection
            with self.postgres_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Connected to PostgreSQL: {self.postgres_url[:50]}...")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            return False
            
        return True
    
    def get_table_info(self, table_name: str) -> Optional[List[str]]:
        """Get table columns from SQLite"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return columns if columns else None
        except sqlite3.OperationalError:
            return None
    
    def get_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all data from SQLite table"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return [dict(row) for row in cursor.fetchall()]
    
    def migrate_tasks(self) -> int:
        """Migrate Task table data"""
        print("\n📋 Migrating Tasks...")
        
        columns = self.get_table_info('task')
        if not columns:
            print("⚠️  Task table not found in SQLite, skipping...")
            return 0
        
        data = self.get_table_data('task')
        if not data:
            print("ℹ️  No tasks to migrate")
            return 0
        
        migrated = 0
        with Session(self.postgres_engine) as session:
            for row in data:
                try:
                    # Convert SQLite row to Task model
                    task_data = {
                        'url': row.get('url'),
                        'mode': row.get('mode', 'simple'),
                        'status': row.get('status', TaskStatus.QUEUED_DOWNLOAD),
                        'stage': row.get('stage'),
                        'progress': row.get('progress'),
                        'video_id': row.get('video_id'),
                        'original_filename': row.get('original_filename'),
                        'downloaded_path': row.get('downloaded_path'),
                        'processed_path': row.get('processed_path'),
                        'clips_dir': row.get('clips_dir'),
                        'transcript_path': row.get('transcript_path'),
                        'clips_json_path': row.get('clips_json_path'),
                        'error': row.get('error'),
                        'start_time': row.get('start_time'),
                        'end_time': row.get('end_time'),
                        'created_at': datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow(),
                        'updated_at': datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else datetime.utcnow(),
                    }
                    
                    # Remove None values to use model defaults
                    task_data = {k: v for k, v in task_data.items() if v is not None}
                    
                    # Check if task already exists (by URL)
                    existing = session.exec(select(Task).where(Task.url == task_data['url'])).first()
                    if existing:
                        print(f"⏭️  Task already exists: {task_data['url'][:50]}...")
                        continue
                    
                    task = Task(**task_data)
                    session.add(task)
                    migrated += 1
                    
                except Exception as e:
                    print(f"❌ Failed to migrate task {row.get('id', 'unknown')}: {e}")
                    continue
            
            session.commit()
        
        print(f"✅ Migrated {migrated} tasks")
        return migrated
    
    def migrate_upscale_tasks(self) -> int:
        """Migrate UpscaleTask table data"""
        print("\n🚀 Migrating Upscale Tasks...")
        
        columns = self.get_table_info('upscaletask')
        if not columns:
            print("⚠️  UpscaleTask table not found in SQLite, skipping...")
            return 0
        
        data = self.get_table_data('upscaletask')
        if not data:
            print("ℹ️  No upscale tasks to migrate")
            return 0
        
        migrated = 0
        with Session(self.postgres_engine) as session:
            for row in data:
                try:
                    upscale_data = {
                        'file_path': row.get('file_path'),
                        'status': row.get('status', UpscaleStatus.QUEUED),
                        'stage': row.get('stage'),
                        'progress': row.get('progress', 0),
                        'vast_instance_id': row.get('vast_instance_id'),
                        'vast_job_id': row.get('vast_job_id'),
                        'result_path': row.get('result_path'),
                        'error': row.get('error'),
                        'created_at': datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow(),
                        'updated_at': datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else datetime.utcnow(),
                    }
                    
                    # Remove None values
                    upscale_data = {k: v for k, v in upscale_data.items() if v is not None}
                    
                    # Check if task already exists (by file_path)
                    existing = session.exec(select(UpscaleTask).where(UpscaleTask.file_path == upscale_data['file_path'])).first()
                    if existing:
                        print(f"⏭️  Upscale task already exists: {upscale_data['file_path']}")
                        continue
                    
                    upscale_task = UpscaleTask(**upscale_data)
                    session.add(upscale_task)
                    migrated += 1
                    
                except Exception as e:
                    print(f"❌ Failed to migrate upscale task {row.get('id', 'unknown')}: {e}")
                    continue
            
            session.commit()
        
        print(f"✅ Migrated {migrated} upscale tasks")
        return migrated
    
    def migrate_downloaded_videos(self) -> int:
        """Migrate DownloadedVideo table data"""
        print("\n🎥 Migrating Downloaded Videos...")
        
        columns = self.get_table_info('downloadedvideo')
        if not columns:
            print("⚠️  DownloadedVideo table not found in SQLite, skipping...")
            return 0
        
        data = self.get_table_data('downloadedvideo')
        if not data:
            print("ℹ️  No downloaded videos to migrate")
            return 0
        
        migrated = 0
        with Session(self.postgres_engine) as session:
            for row in data:
                try:
                    video_data = {
                        'url': row.get('url'),
                        'title': row.get('title'),
                        'created_at': datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow(),
                    }
                    
                    # Remove None values
                    video_data = {k: v for k, v in video_data.items() if v is not None}
                    
                    # Check if video already exists (by URL)
                    existing = session.exec(select(DownloadedVideo).where(DownloadedVideo.url == video_data['url'])).first()
                    if existing:
                        print(f"⏭️  Downloaded video already exists: {video_data['url'][:50]}...")
                        continue
                    
                    video = DownloadedVideo(**video_data)
                    session.add(video)
                    migrated += 1
                    
                except Exception as e:
                    print(f"❌ Failed to migrate downloaded video {row.get('id', 'unknown')}: {e}")
                    continue
            
            session.commit()
        
        print(f"✅ Migrated {migrated} downloaded videos")
        return migrated
    
    def create_backup(self):
        """Create backup of SQLite database"""
        if not os.path.exists(self.sqlite_path):
            print("⚠️  No SQLite database to backup")
            return
        
        backup_path = f"{self.sqlite_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        import shutil
        shutil.copy2(self.sqlite_path, backup_path)
        print(f"💾 Created backup: {backup_path}")
    
    def get_statistics(self):
        """Get migration statistics"""
        print("\n📊 Migration Statistics:")
        
        # SQLite stats
        if self.sqlite_conn:
            print("\n📁 SQLite Database:")
            for table in ['task', 'upscaletask', 'downloadedvideo']:
                try:
                    cursor = self.sqlite_conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table}: {count} records")
                except sqlite3.OperationalError:
                    print(f"  {table}: table not found")
        
        # PostgreSQL stats
        if self.postgres_engine:
            print("\n🐘 PostgreSQL Database:")
            with Session(self.postgres_engine) as session:
                task_count = len(session.exec(select(Task)).all())
                upscale_count = len(session.exec(select(UpscaleTask)).all())
                video_count = len(session.exec(select(DownloadedVideo)).all())
                
                print(f"  task: {task_count} records")
                print(f"  upscaletask: {upscale_count} records") 
                print(f"  downloadedvideo: {video_count} records")
    
    def migrate_all(self):
        """Perform complete migration"""
        print("🚀 Starting database migration from SQLite to PostgreSQL")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        # Create backup first
        self.create_backup()
        
        # Show initial statistics
        self.get_statistics()
        
        # Perform migrations
        total_migrated = 0
        total_migrated += self.migrate_downloaded_videos()
        total_migrated += self.migrate_tasks()
        total_migrated += self.migrate_upscale_tasks()
        
        # Show final statistics
        print("\n" + "=" * 60)
        print(f"🎉 Migration completed! Total records migrated: {total_migrated}")
        self.get_statistics()
        
        return True
    
    def __del__(self):
        """Close connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()


def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate database from SQLite to PostgreSQL")
    parser.add_argument("--sqlite", default="app.db", help="Path to SQLite database")
    parser.add_argument("--postgres", help="PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without actually doing it")
    
    args = parser.parse_args()
    
    # Get PostgreSQL URL from environment or argument
    postgres_url = args.postgres or os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("❌ PostgreSQL URL not provided. Use --postgres argument or set POSTGRES_URL environment variable")
        return 1
    
    sqlite_path = args.sqlite
    
    print(f"📋 Migration Plan:")
    print(f"  From: {sqlite_path}")
    print(f"  To: {postgres_url[:50]}...")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print()
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No actual migration will be performed")
        # TODO: Implement dry run logic
        return 0
    
    migrator = DatabaseMigrator(sqlite_path, postgres_url)
    success = migrator.migrate_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())