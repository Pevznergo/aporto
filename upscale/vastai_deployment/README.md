# Video Upscaling Application for Vast.ai L4 Server

This application provides video upscaling using the realesr-general-x4v3 model with fixed settings:
- Denoise Strength: 0.5
- Resolution upscale: 4x
- Face Enhancement (GFPGAN): Enabled

## Features

- Optimized for Vast.ai L4 server deployment
- SSH-based file transfer for input/output videos
- REST API for remote job submission
- Docker support for easy deployment
- **Automatic compatibility fixes** - torchvision compatibility is handled automatically on every deployment

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run upscaling via SSH:
   ```bash
   python upscale_app.py <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>
   ```

3. Or use the provided script:
   ```bash
   ./run_upscale.sh <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>
   ```

4. For API usage, start the server:
   ```bash
   python server.py
   ```

## Vast.ai Deployment

This application is designed for deployment on Vast.ai GPU instances:

1. Build and push the Docker image:
   ```bash
   docker build -t your-dockerhub-username/video-upscale-app:latest .
   docker push your-dockerhub-username/video-upscale-app:latest
   ```

2. Use the Vast.ai API to create an instance:
   ```bash
   python deploy_vastai.py --api-key YOUR_API_KEY --action create --config vastai_instance_config.json
   ```

3. Wait for the instance to start:
   ```bash
   python deploy_vastai.py --api-key YOUR_API_KEY --action wait --instance-id INSTANCE_ID
   ```

4. Use the REST API for upscaling jobs:
   ```bash
   curl -X POST "http://INSTANCE_IP:5000/upscale" \
     -H "Content-Type: application/json" \
     -d '{"input_path": "/input.mp4", "output_path": "/output.mp4"}'
   ```

## Documentation

- [Full Upscaling Documentation](README_UPSCALE.md)
- [API Documentation](README_API.md)
- [Vast.ai Deployment Guide](VASTAI_DEPLOYMENT.md)
- [Vast.ai API Usage](VASTAI_API_GUIDE.md)
- [Deployment Examples](DEPLOYMENT_EXAMPLE.md)
- [BasicSR Compatibility Fix](BASICSR_FIX.md) - Detailed explanation of automatic fixes
- [Quick Fix Reference](QUICK_FIX.md) - Quick troubleshooting guide

## Requirements

- Python 3.7+
- CUDA-compatible GPU (for best performance)
- SSH access to remote server for file transfer