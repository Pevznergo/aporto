#!/usr/bin/env python
"""
Test script for Video Upscaling Application
"""

import os
import sys
import tempfile
import cv2
import numpy as np

def create_test_video(filename, duration=5, fps=30):
    """Create a simple test video for upscaling."""
    print(f"Creating test video: {filename}")
    
    # Video dimensions
    width, height = 640, 360
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    if not out.isOpened():
        raise Exception("Could not create video writer")
    
    # Create frames with moving pattern
    for i in range(duration * fps):
        # Create a black image
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add a moving rectangle
        x = int((i / (duration * fps)) * width)
        cv2.rectangle(frame, (x, 100), (x + 50, 200), (0, 255, 0), -1)
        
        # Add some text
        cv2.putText(frame, f"Frame {i}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print(f"Test video created: {filename} ({duration} seconds, {fps} FPS)")

def test_upscale_app():
    """Test the upscaling application."""
    print("Testing Video Upscaling Application...")
    
    # Create test video
    test_video = "test_input.mp4"
    create_test_video(test_video)
    
    # Test upscaling
    output_video = "test_output.mp4"
    
    # Import the upscaling function
    try:
        from upscale_app import upscale_video_with_realesrgan
        success = upscale_video_with_realesrgan(test_video, output_video)
        
        if success:
            print("✅ Upscaling test passed!")
            print(f"Output video: {output_video}")
        else:
            print("❌ Upscaling test failed!")
            
    except Exception as e:
        print(f"❌ Error during upscaling test: {e}")
        return False
    
    # Cleanup
    if os.path.exists(test_video):
        os.remove(test_video)
    
    return True

if __name__ == "__main__":
    test_upscale_app()