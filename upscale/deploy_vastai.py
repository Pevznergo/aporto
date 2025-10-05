#!/usr/bin/env python3
"""
Vast.ai Deployment Script for Video Upscaling Application
"""

import os
import sys
import json
import time
import requests
import argparse

# Vast.ai API base URL
VAST_AI_API_URL = "https://console.vast.ai/api/v0"

def get_headers(api_key):
    """Get headers for Vast.ai API requests."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def list_instances(api_key):
    """List all instances."""
    url = f"{VAST_AI_API_URL}/instances/"
    response = requests.get(url, headers=get_headers(api_key))
    return response.json()

def create_instance(api_key, config_file):
    """Create a new instance."""
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    url = f"{VAST_AI_API_URL}/asks/"
    response = requests.post(url, headers=get_headers(api_key), json=config)
    return response.json()

def get_instance_details(api_key, instance_id):
    """Get details for a specific instance."""
    url = f"{VAST_AI_API_URL}/instances/{instance_id}/"
    response = requests.get(url, headers=get_headers(api_key))
    return response.json()

def stop_instance(api_key, instance_id):
    """Stop a running instance."""
    url = f"{VAST_AI_API_URL}/instances/{instance_id}/"
    data = {"state": "stopped"}
    response = requests.put(url, headers=get_headers(api_key), json=data)
    return response.json()

def start_instance(api_key, instance_id):
    """Start a stopped instance."""
    url = f"{VAST_AI_API_URL}/instances/{instance_id}/"
    data = {"state": "running"}
    response = requests.put(url, headers=get_headers(api_key), json=data)
    return response.json()

def destroy_instance(api_key, instance_id):
    """Destroy an instance."""
    url = f"{VAST_AI_API_URL}/instances/{instance_id}/"
    response = requests.delete(url, headers=get_headers(api_key))
    return response.json()

def wait_for_instance(api_key, instance_id, target_state="running", timeout=300):
    """Wait for instance to reach target state."""
    print(f"Waiting for instance {instance_id} to be {target_state}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            details = get_instance_details(api_key, instance_id)
            current_state = details.get('actual_status', 'unknown')
            print(f"Current state: {current_state}")
            
            if current_state == target_state:
                print(f"Instance {instance_id} is now {target_state}")
                return True
                
            time.sleep(10)
        except Exception as e:
            print(f"Error checking instance status: {e}")
            time.sleep(10)
    
    print(f"Timeout waiting for instance to be {target_state}")
    return False

def main():
    parser = argparse.ArgumentParser(description="Vast.ai Deployment Tool")
    parser.add_argument("--api-key", required=True, help="Vast.ai API key")
    parser.add_argument("--action", required=True, choices=[
        "list", "create", "details", "stop", "start", "destroy", "wait"
    ], help="Action to perform")
    parser.add_argument("--instance-id", help="Instance ID (required for details, stop, start, destroy, wait)")
    parser.add_argument("--config", help="Configuration file for instance creation")
    parser.add_argument("--target-state", default="running", help="Target state for wait command")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout for wait command")
    
    args = parser.parse_args()
    
    try:
        if args.action == "list":
            result = list_instances(args.api_key)
            print(json.dumps(result, indent=2))
            
        elif args.action == "create":
            if not args.config:
                print("Error: --config is required for create action")
                return 1
            result = create_instance(args.api_key, args.config)
            print(json.dumps(result, indent=2))
            
        elif args.action == "details":
            if not args.instance_id:
                print("Error: --instance-id is required for details action")
                return 1
            result = get_instance_details(args.api_key, args.instance_id)
            print(json.dumps(result, indent=2))
            
        elif args.action == "stop":
            if not args.instance_id:
                print("Error: --instance-id is required for stop action")
                return 1
            result = stop_instance(args.api_key, args.instance_id)
            print(json.dumps(result, indent=2))
            
        elif args.action == "start":
            if not args.instance_id:
                print("Error: --instance-id is required for start action")
                return 1
            result = start_instance(args.api_key, args.instance_id)
            print(json.dumps(result, indent=2))
            
        elif args.action == "destroy":
            if not args.instance_id:
                print("Error: --instance-id is required for destroy action")
                return 1
            result = destroy_instance(args.api_key, args.instance_id)
            print(json.dumps(result, indent=2))
            
        elif args.action == "wait":
            if not args.instance_id:
                print("Error: --instance-id is required for wait action")
                return 1
            success = wait_for_instance(
                args.api_key, 
                args.instance_id, 
                args.target_state, 
                args.timeout
            )
            return 0 if success else 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())