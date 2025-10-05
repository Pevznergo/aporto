# Quick Start: Deploy to Vast.ai

This is a quick start guide to deploy your video upscaling application to Vast.ai.

## 1. Rent an Instance

1. Go to [Vast.ai](https://vast.ai/)
2. Rent an L4 GPU instance with:
   - Docker image: `nvidia/cuda:12.2.2-devel-ubuntu22.04`
   - On Start command: `/bin/bash`
   - Disk space: 50GB+

## 2. Upload Application

```bash
# Upload deployment package
scp -P [SSH_PORT] vastai_minimal.zip root@[INSTANCE_IP]:/workspace/
```

## 3. Setup on Instance

Connect to your instance and run:

```bash
ssh -p [SSH_PORT] root@[INSTANCE_IP]
```

Then on the instance:

```bash
cd /workspace
unzip vastai_minimal.zip
cd vastai_minimal
chmod +x *.sh
./setup_vastai.sh
```

## 4. Start Server

```bash
nohup ./start_server.sh > server.log 2>&1 &
```

## 5. Test API

```bash
curl http://localhost:5000/health
```

## 6. Use for Video Upscaling

```bash
# Submit upscaling job
curl -X POST http://localhost:5000/upscale \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "/workspace/input.mp4",
    "output_path": "/workspace/output.mp4"
  }'
```

That's it! Your video upscaling application is now running on Vast.ai.