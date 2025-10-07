# Consolidated

See README.md in this folder for current documentation.

This is a simplified application for video upscaling using the realesr-general-x4v3 model, designed to run on a rented L4 server on Vast.ai.

## Features

- Video upscaling with Real-ESRGAN (realesr-general-x4v3 model)
- Fixed settings:
  - Denoise Strength: 0.5
  - Resolution upscale: 4x
  - Face Enhancement (GFPGAN): Enabled
- SSH-based file transfer for input/output videos
- Automatic dependency installation

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### SSH-based Processing (Recommended)

To process a video from a remote server and send it back:

```bash
python upscale_app.py <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>
```

Example:
```bash
python upscale_app.py user 192.168.1.100 /path/to/input.mp4 /path/to/output.mp4
```

This will:
1. Receive the video file via SSH from the remote server
2. Upscale the video using Real-ESRGAN with the specified settings
3. Send the upscaled video back to the remote server

### Manual Processing

You can also modify the code to call `upscale_video_with_realesrgan()` directly for manual processing.

## Configuration

The upscaling settings are fixed in the code:
- DENOISE_STRENGTH = 0.5
- UPSCALE_FACTOR = 4
- FACE_ENHANCEMENT = True

To change these settings, modify the constants at the top of `upscale_app.py`.

## Requirements

- Python 3.7+
- CUDA-compatible GPU (for best performance)
- SSH access to remote server for file transfer

## Dependencies

All dependencies are listed in `requirements.txt` and will be automatically installed when running the application.

## Required models

- Real-ESRGAN weights will be downloaded automatically to `models/realesr-general-x4v3.pth` on first run (if missing).
- GFPGAN face enhancement is mandatory. Place `GFPGANv1.4.pth` at `models/GFPGANv1.4.pth` before starting the server. The server will refuse to start if this file is not present.
