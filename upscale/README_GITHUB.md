# Video Upscaling Application for Vast.ai

This application provides video upscaling using the realesr-general-x4v3 model with fixed settings:
- Denoise Strength: 0.5
- Resolution upscale: 4x
- Face Enhancement (GFPGAN): Enabled

## Features

- Optimized for Vast.ai L4 server deployment
- SSH-based file transfer for input/output videos
- REST API for remote job submission
- Easy deployment to Vast.ai GPU instances

## Prerequisites

To run this application, you need:
- A Vast.ai account
- An L4 GPU instance on Vast.ai

## Deployment to Vast.ai

### Option 1: Direct Deployment from GitHub

1. Rent an L4 GPU instance on Vast.ai with the following settings:
   - Docker image: `nvidia/cuda:12.2.2-devel-ubuntu22.04`
   - On Start command: `/bin/bash`
   - Disk space: 50GB+

2. Connect to your instance via SSH:
   ```bash
   ssh -p [SSH_PORT] root@[INSTANCE_IP]
   ```

3. Clone this repository on the instance:
   ```bash
   cd /workspace
   git clone https://github.com/YOUR_USERNAME/video-upscale-vastai.git
   cd video-upscale-vastai
   ```

4. Run the setup script:
   ```bash
   chmod +x setup_vastai.sh
   ./setup_vastai.sh
   ```

5. Start the API server:
   ```bash
   nohup ./start_server.sh > server.log 2>&1 &
   ```

6. Test the API:
   ```bash
   curl http://localhost:5000/health
   ```

### Option 2: Manual Deployment

1. Download the latest release from GitHub
2. Upload to your Vast.ai instance
3. Extract and run the setup script
4. Start the server

## API Usage

Once deployed, you can use the REST API to submit upscaling jobs:

```bash
# Submit an upscaling job
curl -X POST http://[INSTANCE_IP]:5000/upscale \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "/workspace/input.mp4",
    "output_path": "/workspace/output.mp4"
  }'

# Check job status
curl http://[INSTANCE_IP]:5000/job/1
```

## SSH-based Workflow

The application supports SSH-based video processing:

1. Send a video to the Vast.ai instance:
   ```bash
   scp -P [SSH_PORT] your_video.mp4 root@[INSTANCE_IP]:/workspace/input.mp4
   ```

2. Submit an upscaling job via the API

3. Retrieve the upscaled video:
   ```bash
   scp -P [SSH_PORT] root@[INSTANCE_IP]:/workspace/output.mp4 upscaled_video.mp4
   ```

## Configuration

The application uses the following fixed settings:
- Model: realesr-general-x4v3
- Denoise Strength: 0.5
- Upscale Factor: 4x
- Face Enhancement: Enabled (GFPGAN)

These settings can be modified in the [config.json](file:///Users/igortkachenko/Downloads/aporto/upscale/config.json) file.

## Cost Management

Remember to stop or destroy your Vast.ai instance when not in use to avoid unnecessary charges.