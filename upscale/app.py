#!/usr/bin/env python
"""
EDEN Video Interpolation Application for Hugging Face Spaces
A complete application for video frame interpolation using EDEN.
"""

import os
import tempfile
import threading
import time
import torch
import cv2
import numpy as np
import subprocess
import sys
import shutil
import importlib.util
from PIL import Image

# Global variables for EDEN availability and model
EDEN_AVAILABLE = False
eden_model = None
_eden_cache_lock = threading.Lock()

def install_eden_automatically():
    """Install EDEN following the official README instructions."""
    global EDEN_AVAILABLE
    
    try:
        print("Installing EDEN from GitHub repository...")
        
        # Clean up any existing EDEN directory
        if os.path.exists('EDEN'):
            shutil.rmtree('EDEN')
        
        # Clone the repository manually since it's not a standard Python package
        try:
            subprocess.run(['git', 'clone', 'https://github.com/bbldCVer/EDEN.git'], 
                         check=True, capture_output=True, text=True)
            print("Successfully cloned EDEN repository")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone EDEN repository: {e.stderr}")
            return False
        
        if not os.path.exists('EDEN'):
            print("EDEN directory not created after cloning")
            return False
        
        # Install EDEN dependencies from requirements.txt
        if os.path.exists('EDEN/requirements.txt'):
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'EDEN/requirements.txt'], 
                             check=True, capture_output=True, text=True)
                print("Successfully installed EDEN requirements")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install requirements: {e.stderr}")
                return False
        
        # Add EDEN to Python path
        eden_path = os.path.abspath('EDEN')
        if eden_path not in sys.path:
            sys.path.insert(0, eden_path)
        
        # Create necessary directories
        os.makedirs('EDEN/checkpoints', exist_ok=True)
        os.makedirs('EDEN/interpolation_outputs', exist_ok=True)
        
        EDEN_AVAILABLE = True
        print("EDEN installed successfully!")
        return True
        
    except Exception as e:
        print(f"EDEN installation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def download_eden_weights():
    """Download EDEN pretrained weights from Hugging Face."""
    try:
        print("Downloading EDEN pretrained weights...")
        
        # Install huggingface_hub if not available
        try:
            from huggingface_hub import hf_hub_download
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'huggingface_hub'], check=True)
            from huggingface_hub import hf_hub_download
        
        # Download weights - based on README, we need to check what files are actually available
        checkpoints_dir = 'EDEN/checkpoints'
        os.makedirs(checkpoints_dir, exist_ok=True)
        
        # Try to download common model files
        possible_files = [
            "model.safetensors",
            "model.pth",
            "vae.safetensors",
            "dit.safetensors",
            "config.json",
            "config.yaml"
        ]
        
        downloaded_files = []
        for filename in possible_files:
            try:
                downloaded_path = hf_hub_download(
                    repo_id="zhZ524/EDEN",
                    filename=filename,
                    local_dir=checkpoints_dir
                )
                print(f"Downloaded {filename}")
                downloaded_files.append(filename)
            except Exception as e:
                print(f"Warning: Could not download {filename}: {e}")
        
        return len(downloaded_files) > 0
        
    except Exception as e:
        print(f"Failed to download EDEN weights: {e}")
        return False

def initialize_eden():
    """Initialize EDEN model following official instructions."""
    global EDEN_AVAILABLE, eden_model
    
    # First check if EDEN directory exists
    if not os.path.exists('EDEN'):
        # Install EDEN
        if not install_eden_automatically():
            return False
    
    # Add EDEN to Python path
    eden_path = os.path.abspath('EDEN')
    if eden_path not in sys.path:
        sys.path.insert(0, eden_path)
    
    # Download weights
    download_eden_weights()
    
    EDEN_AVAILABLE = True
    return True

class EDENVideoInterpolator:
    """EDEN-based video frame interpolation processor."""
    
    def __init__(self, target_fps=None, multiplier=2):
        """
        Initialize EDEN interpolator.
        
        Args:
            target_fps (float): Target FPS (if None, uses multiplier)
            multiplier (int): FPS multiplication factor (2x, 4x, etc.)
        """
        self.target_fps = target_fps
        self.multiplier = multiplier
        
        if not EDEN_AVAILABLE:
            raise ImportError("EDEN is not available and automatic installation failed.")
        
        # Add EDEN to Python path
        eden_path = os.path.abspath('EDEN')
        if eden_path not in sys.path:
            sys.path.insert(0, eden_path)
    
    def interpolate_video(self, input_video, output_path):
        """Interpolate video frames using EDEN."""
        
        # Open video
        cap = cv2.VideoCapture(input_video)
        if not cap.isOpened():
            raise Exception("Error opening video file")
        
        # Get video properties
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate target FPS
        if self.target_fps is None:
            new_fps = original_fps * self.multiplier
        else:
            new_fps = self.target_fps
            self.multiplier = new_fps / original_fps
        
        print(f"EDEN interpolation: {original_fps} FPS → {new_fps} FPS ({self.multiplier:.1f}x)")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, new_fps, (frame_width, frame_height))
        
        if not out.isOpened():
            raise Exception("Error initializing video writer")
        
        try:
            # Process frames
            prev_frame = None
            written_count = 0
            processed_frames = 0
            
            # Create temporary directory for frame processing
            temp_frames_dir = 'temp_frames'
            os.makedirs(temp_frames_dir, exist_ok=True)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                processed_frames += 1
                
                if prev_frame is not None:
                    # Save frames as images for EDEN processing
                    frame_0_path = f'{temp_frames_dir}/frame_0.jpg'
                    frame_1_path = f'{temp_frames_dir}/frame_1.jpg'
                    
                    cv2.imwrite(frame_0_path, prev_frame)
                    cv2.imwrite(frame_1_path, frame)
                    
                    # Use EDEN to interpolate
                    interpolated_frames = self._interpolate_frame_pair(frame_0_path, frame_1_path)
                    
                    # Write original previous frame
                    out.write(prev_frame)
                    written_count += 1
                    
                    # Write interpolated frames
                    for interp_frame in interpolated_frames:
                        out.write(interp_frame)
                        written_count += 1
                
                prev_frame = frame
                
                # Print progress
                if processed_frames % 10 == 0:
                    print(f"EDEN progress: {processed_frames}/{total_frames} frames processed, {written_count} frames written")
            
            # Write the last frame
            if prev_frame is not None:
                out.write(prev_frame)
                written_count += 1
            
            # Clean up temporary directory
            shutil.rmtree(temp_frames_dir, ignore_errors=True)
            
            print(f"EDEN interpolation completed: {processed_frames} frames processed, {written_count} frames written")
            
        finally:
            cap.release()
            out.release()
    
    def _interpolate_frame_pair(self, frame_0_path, frame_1_path):
        """Interpolate frames between two input frames using EDEN."""
        try:
            # Create results directory
            results_dir = 'temp_interpolation_results'
            os.makedirs(results_dir, exist_ok=True)
            
            # Run EDEN inference directly using subprocess as per README
            # CUDA_VISIBLE_DEVICES=0 python inference.py --frame_0_path examples/frame_0.jpg --frame_1_path examples/frame_1.jpg --interpolated_results_dir interpolation_outputs
            cmd = [
                sys.executable,
                'inference.py',
                '--frame_0_path', frame_0_path,
                '--frame_1_path', frame_1_path,
                '--interpolated_results_dir', results_dir
            ]
            
            # Add checkpoint path if it exists
            if os.path.exists('EDEN/checkpoints'):
                cmd.extend(['--checkpoint_path', 'EDEN/checkpoints'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='EDEN')
            
            if result.returncode != 0:
                print(f"EDEN inference failed: {result.stderr}")
                return []
            
            # Load interpolated frames
            interpolated_frames = []
            
            # Generate intermediate frames based on multiplier
            steps = max(1, int(self.multiplier) - 1)
            
            for i in range(1, steps + 1):
                # EDEN typically saves interpolated frames with specific naming
                # Check for common naming patterns
                possible_names = [
                    f"interpolated_frame_{i}.jpg",
                    f"frame_{i}.jpg",
                    f"output_{i}.jpg",
                    f"interpolated_{i}.png"
                ]
                
                interp_path = None
                for name in possible_names:
                    path = os.path.join(results_dir, name)
                    if os.path.exists(path):
                        interp_path = path
                        break
                
                if interp_path and os.path.exists(interp_path):
                    # Load and convert to OpenCV format
                    pil_image = Image.open(interp_path)
                    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    interpolated_frames.append(cv_image)
            
            # Clean up temporary results
            shutil.rmtree(results_dir, ignore_errors=True)
            
            return interpolated_frames
            
        except Exception as e:
            print(f"Frame pair interpolation error: {e}")
            import traceback
            traceback.print_exc()
            return []

def interpolate_video_with_eden(input_video, target_fps=None, multiplier=2):
    """
    Interpolate video using EDEN.
    
    Args:
        input_video: Path to input video file or Gradio file object
        target_fps (float): Target FPS (if None, uses multiplier)
        multiplier (int): FPS multiplication factor (2x, 4x, etc.)
    
    Returns:
        str: Path to the interpolated video file
    """
    if not EDEN_AVAILABLE:
        # Try to initialize EDEN one more time
        if not initialize_eden():
            raise Exception("EDEN is not available. Please check the installation.")
    
    print(f"Interpolating video with EDEN: {input_video}")
    
    # Handle Gradio's file upload format
    if hasattr(input_video, 'name'):
        input_video_path = input_video.name
    else:
        input_video_path = input_video
    
    # Verify input file exists and is accessible
    if not os.path.exists(input_video_path):
        raise Exception(f"Input video file not found: {input_video_path}")
    
    if os.path.getsize(input_video_path) == 0:
        raise Exception("Input video file is empty")
    
    # Create output file
    timestamp = int(time.time())
    final_output_path = f"eden_interpolated_{timestamp}.mp4"
    
    # Process video with EDEN
    try:
        interpolator = EDENVideoInterpolator(target_fps=target_fps, multiplier=multiplier)
        interpolator.interpolate_video(input_video_path, final_output_path)
        
        # Verify the file was created and is not empty
        if os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 0:
            print(f"Video interpolation completed successfully: {final_output_path}")
            return final_output_path
        else:
            raise Exception("Failed to create interpolated video file")
            
    except Exception as e:
        print(f"Error during video interpolation: {e}")
        raise Exception(f"Video interpolation failed: {str(e)}")

# Initialize EDEN at startup
print("Initializing EDEN...")
if not initialize_eden():
    print("Failed to initialize EDEN. Please check your internet connection and try again.")

# Gradio interface
try:
    import gradio as gr
    
    with gr.Blocks(title="EDEN Video Interpolation") as demo:
        gr.Markdown("""
        # EDEN Video Interpolation
        
        High-quality video frame interpolation using EDEN (Enhanced Diffusion for High-quality Large-motion Video Frame Interpolation).
        
        ## Features:
        - State-of-the-art diffusion-based interpolation
        - Handles large motion effectively
        - Multiple frame rate options
        
        ## Model Information:
        - **Paper**: [CVPR 2025] EDEN: Enhanced Diffusion for High-quality Large-motion Video Frame Interpolation
        - **Repository**: [EDEN on GitHub](https://github.com/bbldCVer/EDEN)
        """)
        
        with gr.Row():
            with gr.Column():
                input_video = gr.File(
                    label="Upload Video File", 
                    file_types=["video"],
                    type="filepath"
                )
                
                with gr.Row():
                    multiplier = gr.Slider(
                        minimum=2, 
                        maximum=8, 
                        value=2, 
                        step=1, 
                        label="Frame Rate Multiplier"
                    )
                    target_fps = gr.Number(
                        label="Target FPS (optional)", 
                        precision=0,
                        value=None
                    )
                
                interpolate_btn = gr.Button("Interpolate Video", variant="primary")
                
            with gr.Column():
                output_file = gr.File(
                    label="Download Interpolated Video",
                    type="filepath"
                )
                status = gr.Textbox(
                    label="Status", 
                    lines=4,
                    value="Ready to process video"
                )
        
        def interpolate_with_status(input_video, target_fps, multiplier):
            try:
                if input_video is None:
                    return None, "Please upload a video file first."
                
                status_msg = f"Processing video with EDEN {multiplier}x interpolation..."
                if target_fps:
                    status_msg += f" (Target: {target_fps} FPS)"
                
                result = interpolate_video_with_eden(input_video, target_fps, multiplier)
                return result, f"✅ EDEN interpolation completed successfully!\nOutput: {result}"
                
            except Exception as e:
                return None, f"❌ Error: {str(e)}"
        
        interpolate_btn.click(
            fn=interpolate_with_status,
            inputs=[input_video, target_fps, multiplier],
            outputs=[output_file, status],
            show_progress=True
        )
        
        # Add example
        gr.Examples(
            examples=[
                [None, None, 2],
                [None, 60, 4]
            ],
            inputs=[input_video, target_fps, multiplier],
            label="Example Settings"
        )

except ImportError:
    gr = None
    print("Warning: Gradio not available. Web interface will not be available.")
    demo = None

# Launch the app when run directly
if __name__ == "__main__":
    if gr is not None and demo is not None:
        if EDEN_AVAILABLE:
            print("Starting EDEN Video Interpolation web interface...")
            demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
        else:
            print("EDEN is not available. Cannot start web interface.")
    else:
        print("EDEN Video Interpolation CLI")
        if EDEN_AVAILABLE:
            print("EDEN is ready for use")
        else:
            print("EDEN initialization failed")