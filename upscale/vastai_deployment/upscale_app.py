#!/usr/bin/env python
"""
Video Upscaling Application for Vast.ai L4 Server
A simplified application for video upscaling using realesr-general-x4v3 model.
"""

import os
import sys
import time
import subprocess
import cv2
import tempfile
import shutil
import json
from pathlib import Path

# Configuration
DENOISE_STRENGTH = 0.5
UPSCALE_FACTOR = 4
FACE_ENHANCEMENT = True

def install_upscale_dependencies():
    """Install dependencies for video upscaling."""
    try:
        print("Installing upscaling dependencies...")
        
        # Install basicsr for Real-ESRGAN
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'basicsr', 'facexlib', 'gfpgan', 'realesrgan'], 
                      check=True, capture_output=True, text=True)
        print("Successfully installed upscaling dependencies")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return False

def download_realesrgan_model():
    """Download Real-ESRGAN model files."""
    try:
        print("Downloading Real-ESRGAN model files...")
        
        # Create models directory
        models_dir = 'models'
        os.makedirs(models_dir, exist_ok=True)
        
        # Download realesr-general-x4v3 model
        model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth"
        model_path = os.path.join(models_dir, "realesr-general-x4v3.pth")
        
        if not os.path.exists(model_path):
            subprocess.run(['wget', '-O', model_path, model_url], check=True)
            print("Successfully downloaded Real-ESRGAN model")
        else:
            print("Real-ESRGAN model already exists")
            
        return True
        
    except Exception as e:
        print(f"Failed to download Real-ESRGAN model: {e}")
        return False

def upscale_video_with_realesrgan(input_video_path, output_video_path):
    """
    Upscale video using Real-ESRGAN with specified settings.
    
    Args:
        input_video_path (str): Path to input video file
        output_video_path (str): Path to output upscaled video file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Upscaling video: {input_video_path}")
        print(f"Settings: Denoise={DENOISE_STRENGTH}, Upscale={UPSCALE_FACTOR}x, FaceEnhance={FACE_ENHANCEMENT}")
        
        # Create temporary directory for frame processing
        temp_dir = tempfile.mkdtemp()
        frames_dir = os.path.join(temp_dir, "frames")
        output_frames_dir = os.path.join(temp_dir, "output_frames")
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(output_frames_dir, exist_ok=True)
        
        # Extract frames from video
        print("Extracting video frames...")
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise Exception("Error opening video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Video FPS: {fps}, Total frames: {frame_count}")
        
        # Save frames as images
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_path = os.path.join(frames_dir, f"frame_{frame_idx:06d}.png")
            cv2.imwrite(frame_path, frame)
            frame_idx += 1
        
        cap.release()
        print(f"Extracted {frame_idx} frames")
        
        # Prepare Real-ESRGAN command
        cmd = [
            sys.executable, '-m', 'realesrgan.archs.srvgg_arch',
            '-i', frames_dir,
            '-o', output_frames_dir,
            '-n', 'realesr-general-x4v3',
            '-s', str(UPSCALE_FACTOR),
            '--outscale', str(UPSCALE_FACTOR)
        ]

        # Add denoise strength
        if DENOISE_STRENGTH != 0.5:  # 0.5 is default
            cmd.extend(['--denoise_strength', str(DENOISE_STRENGTH)])

        # Add face enhancement
        if FACE_ENHANCEMENT:
            cmd.append('--face_enhance')

        # Add model path if exists
        model_path = os.path.join('models', 'realesr-general-x4v3.pth')
        if os.path.exists(model_path):
            cmd.extend(['--model_path', model_path])

        # Ensure our sitecustomize.py is imported in the subprocess
        def _find_patch_root() -> str:
            here = Path(__file__).resolve()
            for p in [here.parent, *here.parents]:
                if (p / 'sitecustomize.py').exists():
                    return str(p)
            return str(here.parent)

        env = os.environ.copy()
        patch_root = _find_patch_root()
        existing_pp = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = (patch_root if not existing_pp else patch_root + os.pathsep + existing_pp)

        print("Running Real-ESRGAN upscaling...")
        print(f"Command: {' '.join(cmd)}")

        # Run Real-ESRGAN with patched PYTHONPATH so sitecustomize is auto-imported
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            print(f"Real-ESRGAN failed: {result.stderr}")
            return False

        print("Upscaling completed")
        
        # Reconstruct video from upscaled frames
        print("Reconstructing upscaled video...")
        
        # Get dimensions of first upscaled frame
        output_frame_files = sorted(os.listdir(output_frames_dir))
        if not output_frame_files:
            raise Exception("No upscaled frames found")
            
        first_frame_path = os.path.join(output_frames_dir, output_frame_files[0])
        first_frame = cv2.imread(first_frame_path)
        height, width = first_frame.shape[:2]
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            raise Exception("Error initializing video writer")
        
        # Write frames to video
        for frame_file in sorted(os.listdir(output_frames_dir)):
            frame_path = os.path.join(output_frames_dir, frame_file)
            frame = cv2.imread(frame_path)
            out.write(frame)
        
        out.release()
        print(f"Upscaled video saved to: {output_video_path}")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return True
        
    except Exception as e:
        print(f"Error during video upscaling: {e}")
        return False

def receive_video_via_ssh(ssh_user, ssh_host, remote_video_path, local_video_path):
    """
    Receive video file via SSH from remote server.
    
    Args:
        ssh_user (str): SSH username
        ssh_host (str): SSH host
        remote_video_path (str): Path to video on remote server
        local_video_path (str): Local path to save video
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Receiving video via SSH from {ssh_user}@{ssh_host}:{remote_video_path}")
        
        # Use scp to copy file
        cmd = ['scp', f"{ssh_user}@{ssh_host}:{remote_video_path}", local_video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"SSH file transfer failed: {result.stderr}")
            return False
            
        print(f"Video received successfully: {local_video_path}")
        return True
        
    except Exception as e:
        print(f"Error receiving video via SSH: {e}")
        return False

def send_video_via_ssh(local_video_path, ssh_user, ssh_host, remote_video_path):
    """
    Send video file via SSH to remote server.
    
    Args:
        local_video_path (str): Local path to video file
        ssh_user (str): SSH username
        ssh_host (str): SSH host
        remote_video_path (str): Path to save video on remote server
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Sending video via SSH to {ssh_user}@{ssh_host}:{remote_video_path}")
        
        # Use scp to copy file
        cmd = ['scp', local_video_path, f"{ssh_user}@{ssh_host}:{remote_video_path}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"SSH file transfer failed: {result.stderr}")
            return False
            
        print(f"Video sent successfully to: {remote_video_path}")
        return True
        
    except Exception as e:
        print(f"Error sending video via SSH: {e}")
        return False

def process_video_from_ssh(ssh_user, ssh_host, remote_input_path, remote_output_path):
    """
    Complete workflow: receive video, upscale it, and send it back.
    
    Args:
        ssh_user (str): SSH username
        ssh_host (str): SSH host
        remote_input_path (str): Path to input video on remote server
        remote_output_path (str): Path to save output video on remote server
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Generate local paths
        local_input_path = f"input_{int(time.time())}.mp4"
        local_output_path = f"output_{int(time.time())}.mp4"
        
        # Step 1: Receive video from remote server
        if not receive_video_via_ssh(ssh_user, ssh_host, remote_input_path, local_input_path):
            return False
            
        # Step 2: Upscale video
        if not upscale_video_with_realesrgan(local_input_path, local_output_path):
            return False
            
        # Step 3: Send upscaled video back to remote server
        if not send_video_via_ssh(local_output_path, ssh_user, ssh_host, remote_output_path):
            return False
            
        # Clean up local files
        if os.path.exists(local_input_path):
            os.remove(local_input_path)
        if os.path.exists(local_output_path):
            os.remove(local_output_path)
            
        print("Video processing workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in video processing workflow: {e}")
        return False

def main():
    """Main function to run the upscaling application."""
    print("Video Upscaling Application for Vast.ai L4 Server")
    print("=" * 50)
    
    # Install dependencies
    if not install_upscale_dependencies():
        print("Failed to install dependencies. Exiting.")
        return 1
    
    # Download models
    if not download_realesrgan_model():
        print("Failed to download models. Exiting.")
        return 1
    
    # Check if we have command line arguments for SSH processing
    if len(sys.argv) == 5:
        # Process video via SSH: ssh_user ssh_host remote_input_path remote_output_path
        ssh_user = sys.argv[1]
        ssh_host = sys.argv[2]
        remote_input_path = sys.argv[3]
        remote_output_path = sys.argv[4]
        
        success = process_video_from_ssh(ssh_user, ssh_host, remote_input_path, remote_output_path)
        return 0 if success else 1
    else:
        print("Usage for SSH processing:")
        print(f"  {sys.argv[0]} <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>")
        print("\nFor manual processing, modify the code to call upscale_video_with_realesrgan() directly.")
        return 0

if __name__ == "__main__":
    sys.exit(main())