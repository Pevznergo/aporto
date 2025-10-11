#!/usr/bin/env python3
"""
Debug script to check queue status and worker threads
"""

import sys
import os
import requests
import json
import threading

def check_api_queues():
    try:
        response = requests.get('http://localhost:8000/api/queue/stats')
        if response.status_code == 200:
            stats = response.json()
            print("=== API Queue Stats ===")
            for category, queues in stats.items():
                print(f"\n{category.upper()}:")
                for queue_name, queue_info in queues.items():
                    size = queue_info.get('size', 'Unknown')
                    max_workers = queue_info.get('max_workers', 'Unknown') 
                    active = queue_info.get('active_workers', 'N/A')
                    desc = queue_info.get('description', '')
                    print(f"  {queue_name}: size={size}, active={active}, max={max_workers} ({desc})")
        else:
            print(f"❌ API Error: {response.status_code}")
    except Exception as e:
        print(f"❌ API Request failed: {e}")

def check_upscale_tasks():
    try:
        response = requests.get('http://localhost:8000/api/upscale/tasks')
        if response.status_code == 200:
            tasks = response.json()
            print(f"\n=== Upscale Tasks ({len(tasks)}) ===")
            for task in tasks:
                status = task.get('status', 'unknown')
                stage = task.get('stage', 'unknown')
                progress = task.get('progress', 0)
                task_id = task.get('id')
                file_name = os.path.basename(task.get('file_path', ''))
                print(f"  ID {task_id}: {status}/{stage} ({progress}%) - {file_name}")
                
            # Check for stuck tasks
            stuck_tasks = [t for t in tasks if t.get('status') == 'queued' and t.get('stage') != 'queued']
            if stuck_tasks:
                print(f"\n⚠️  {len(stuck_tasks)} STUCK TASKS:")
                for task in stuck_tasks:
                    print(f"    ID {task['id']}: status={task['status']}, stage={task['stage']}")
        else:
            print(f"❌ Tasks API Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Tasks request failed: {e}")

def check_threads():
    """Check if all expected threads are running"""
    print(f"\n=== Python Threads ===")
    for thread in threading.enumerate():
        print(f"  {thread.name}: {'alive' if thread.is_alive() else 'dead'}")

def suggest_fixes():
    print(f"\n=== SUGGESTED FIXES ===")
    print("1. If upload queue size > 0 but no processing:")
    print("   systemctl restart aporto-orchestrator.service")
    print()
    print("2. If tasks stuck in 'queued/uploading' state:")
    print("   curl -X POST http://localhost:8000/api/upscale/tasks/ID/retry")
    print()
    print("3. If semaphore deadlock suspected:")
    print("   Check logs for 'acquire' without 'release'")
    print()
    print("4. Force clear stuck tasks:")
    print("   curl -X DELETE http://localhost:8000/api/upscale/tasks")

if __name__ == "__main__":
    print("🔍 UPSCALE QUEUE DIAGNOSTICS")
    print("=" * 50)
    
    check_api_queues()
    check_upscale_tasks() 
    check_threads()
    suggest_fixes()
    
    print(f"\n" + "=" * 50)
    print("Run this script periodically to monitor queue health")