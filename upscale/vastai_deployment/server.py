#!/usr/bin/env python
"""
Simple HTTP Server for Video Upscaling
Provides a REST API for upscaling videos using Real-ESRGAN.
"""

import os
import sys
import time
import json
import threading
import subprocess
from flask import Flask, request, jsonify, send_file
from upscale_app import upscale_video_with_realesrgan

app = Flask(__name__)

# In-memory job tracking
jobs = {}
job_counter = 0

def _ffprobe_video_ok(path: str) -> tuple[bool, str]:
    try:
        if not os.path.exists(path):
            return False, "Input file not found"
        try:
            sz = os.path.getsize(path)
        except Exception:
            sz = 0
        if sz <= 0:
            return False, "Input file is empty"
        cmd = [
            'ffprobe', '-v', 'error', '-hide_banner',
            '-select_streams', 'v:0', '-show_entries', 'stream=codec_name',
            '-of', 'csv=p=0', path
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return True, ''
        return False, (r.stderr or r.stdout or 'ffprobe failed')
    except Exception as e:
        return False, str(e)

@app.route('/upscale', methods=['POST'])
def upscale_video():
    """
    Upscale a video file.
    
    Expected JSON payload:
    {
        "input_path": "/path/to/input/video.mp4",
        "output_path": "/path/to/output/video.mp4"
    }
    
    Returns:
    {
        "job_id": 123,
        "status": "processing"
    }
    """
    global job_counter
    
    try:
        data = request.get_json()
        input_path = data.get('input_path')
        output_path = data.get('output_path')
        
        if not input_path or not output_path:
            return jsonify({"error": "Missing input_path or output_path"}), 400
        
        if not os.path.exists(input_path):
            return jsonify({"error": "Input file not found"}), 404
        
        ok, err = _ffprobe_video_ok(input_path)
        if not ok:
            return jsonify({"error": f"Invalid input video: {err}"}), 400
        
        # Create a new job
        job_counter += 1
        job_id = job_counter
        
        jobs[job_id] = {
            "status": "processing",
            "input_path": input_path,
            "output_path": output_path,
            "start_time": time.time()
        }
        
        # Process in background
        thread = threading.Thread(target=process_upscale_job, args=(job_id, input_path, output_path))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "status": "processing"
        }), 202
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_upscale_job(job_id, input_path, output_path):
    """Process the upscaling job in background."""
    try:
        success = upscale_video_with_realesrgan(input_path, output_path)
        
        jobs[job_id]["status"] = "completed" if success else "failed"
        jobs[job_id]["end_time"] = time.time()
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["end_time"] = time.time()

@app.route('/job/<int:job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of an upscaling job."""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"]
    }
    
    if "error" in job:
        response["error"] = job["error"]
    
    if "start_time" in job:
        response["start_time"] = job["start_time"]
    
    if "end_time" in job:
        response["end_time"] = job["end_time"]
        response["duration"] = job["end_time"] - job["start_time"]
    
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "video-upscale-api"})

if __name__ == '__main__':
    print("Starting Video Upscaling Server...")
    print("Endpoints:")
    print("  POST /upscale - Submit upscaling job")
    print("  GET /job/<id> - Check job status")
    print("  GET /health - Health check")
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=False)