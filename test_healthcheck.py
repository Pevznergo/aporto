#!/usr/bin/env python3
"""
Test script to verify healthcheck functionality
"""

import requests
import json
import time

def test_healthcheck_api():
    """Test the healthcheck functionality via API"""
    global SERVER_URL
    print("🔍 Testing Queue Healthcheck")
    print("=" * 50)
    
    try:
        # Get queue stats with healthcheck info
        # Replace with your actual VPS address
        if not SERVER_URL:
            SERVER_URL = input("Enter your VPS server URL (e.g., http://your-vps-ip:8000): ").strip()
            if not SERVER_URL:
                SERVER_URL = "http://localhost:8000"  # fallback for local testing
        
        response = requests.get(f'{SERVER_URL}/api/queue/stats')
        if response.status_code == 200:
            stats = response.json()
            
            print("📊 Current Queue Status:")
            for category, queues in stats.items():
                if category == "healthcheck":
                    continue
                    
                print(f"\n{category.upper()}:")
                for queue_name, queue_info in queues.items():
                    size = queue_info.get('size', 'Unknown')
                    max_workers = queue_info.get('max_workers', 'Unknown')
                    active = queue_info.get('active_workers', 'N/A')
                    print(f"  {queue_name}: size={size}, active={active}, max={max_workers}")
            
            # Display healthcheck status
            if "healthcheck" in stats:
                hc = stats["healthcheck"]
                print(f"\n🏥 HEALTHCHECK STATUS:")
                print(f"  Enabled: {hc.get('enabled', False)}")
                print(f"  Interval: {hc.get('check_interval', 'Unknown')}")
                
                if "stuck_tasks" in hc:
                    stuck = hc["stuck_tasks"]
                    total_stuck = stuck.get('total', 0)
                    print(f"  Total stuck tasks: {total_stuck}")
                    
                    if total_stuck > 0:
                        print("  ⚠️  STUCK TASKS DETECTED:")
                        print(f"    - Queued but not queued: {stuck.get('queued_but_not_queued', 0)}")
                        print(f"    - Uploading too long: {stuck.get('uploading_too_long', 0)}")
                        print(f"    - Processing too long: {stuck.get('processing_too_long', 0)}")
                        print("  📝 These will be auto-fixed by healthcheck worker")
                    else:
                        print("  ✅ No stuck tasks detected")
                
                if "error" in hc:
                    print(f"  ❌ Healthcheck error: {hc['error']}")
            else:
                print("\n❌ Healthcheck not available in API response")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def monitor_queues(duration=60):
    """Monitor queues for a period of time"""
    global SERVER_URL
    print(f"\n👀 Monitoring queues for {duration} seconds...")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        try:
            response = requests.get(f'{SERVER_URL}/api/queue/stats')
            if response.status_code == 200:
                stats = response.json()
                
                # Quick status line
                upscale_upload_size = stats.get("upscale_queues", {}).get("upload", {}).get("size", 0)
                upscale_process_size = stats.get("upscale_queues", {}).get("process", {}).get("size", 0)
                upscale_process_active = stats.get("upscale_queues", {}).get("process", {}).get("active_workers", 0)
                stuck_total = stats.get("healthcheck", {}).get("stuck_tasks", {}).get("total", 0)
                
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Upload: {upscale_upload_size} | Process: {upscale_process_size} (active: {upscale_process_active}) | Stuck: {stuck_total}")
                
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    test_healthcheck_api()
    
    print(f"\n" + "=" * 50)
    print("📋 HEALTHCHECK SUMMARY:")
    print("- Runs every 5 minutes automatically") 
    print("- Detects tasks stuck > 10/30/60 minutes")
    print("- Auto-resets stuck tasks to 'queued' state")
    print("- Check /api/queue/stats for real-time stuck task count")
    print("- Monitor logs for '[healthcheck]' messages")
    
    # Ask if user wants continuous monitoring
    try:
        choice = input("\n🔄 Start continuous monitoring? (y/N): ").strip().lower()
        if choice in ['y', 'yes']:
            monitor_queues()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except:
        pass