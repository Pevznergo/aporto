#!/usr/bin/env python3
"""
Test script for deployed Vast.ai API
"""

import os
import sys
import time
import requests
import argparse

def test_api_health(api_url):
    """Test if the API is healthy."""
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def submit_upscale_job(api_url, input_path, output_path):
    """Submit an upscaling job."""
    try:
        data = {
            "input_path": input_path,
            "output_path": output_path
        }
        response = requests.post(f"{api_url}/upscale", json=data, timeout=30)
        
        if response.status_code == 202:
            result = response.json()
            job_id = result.get("job_id")
            print(f"✅ Job submitted successfully. Job ID: {job_id}")
            return job_id
        else:
            print(f"❌ Failed to submit job: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Failed to submit job: {e}")
        return None

def check_job_status(api_url, job_id):
    """Check the status of an upscaling job."""
    try:
        response = requests.get(f"{api_url}/job/{job_id}", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status")
            print(f"Job {job_id} status: {status}")
            return status, result
        else:
            print(f"❌ Failed to check job status: {response.status_code} - {response.text}")
            return None, {}
    except Exception as e:
        print(f"❌ Failed to check job status: {e}")
        return None, {}

def wait_for_job_completion(api_url, job_id, timeout=300):
    """Wait for job to complete."""
    print(f"Waiting for job {job_id} to complete...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status, details = check_job_status(api_url, job_id)
        
        if status is None:
            return False
            
        if status == "completed":
            print("✅ Job completed successfully!")
            if details and "duration" in details:
                print(f"Processing time: {details['duration']:.2f} seconds")
            return True
            
        elif status == "failed":
            print("❌ Job failed!")
            if details and "error" in details:
                print(f"Error: {details['error']}")
            return False
            
        elif status == "processing":
            print("Job is still processing...")
            
        time.sleep(10)
    
    print("⏰ Timeout waiting for job completion")
    return False

def main():
    parser = argparse.ArgumentParser(description="Test deployed Vast.ai API")
    parser.add_argument("--api-url", required=True, help="API URL (e.g., http://ip:5000)")
    parser.add_argument("--input-path", help="Input video path on the server")
    parser.add_argument("--output-path", help="Output video path on the server")
    parser.add_argument("--job-id", help="Existing job ID to check status")
    parser.add_argument("--wait", action="store_true", help="Wait for job completion")
    
    args = parser.parse_args()
    
    # Test API health
    if not test_api_health(args.api_url):
        return 1
    
    # Submit new job if paths provided
    if args.input_path and args.output_path:
        job_id = submit_upscale_job(args.api_url, args.input_path, args.output_path)
        if job_id:
            print(f"Submitted job ID: {job_id}")
            if args.wait:
                return 0 if wait_for_job_completion(args.api_url, job_id) else 1
        else:
            return 1
    
    # Check existing job status
    elif args.job_id:
        if args.wait:
            return 0 if wait_for_job_completion(args.api_url, args.job_id) else 1
        else:
            status, _ = check_job_status(args.api_url, args.job_id)
            return 0 if status else 1
    
    else:
        print("Provide either --input-path and --output-path to submit a job, or --job-id to check status")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())