# Manual Deployment to Vast.ai

This guide explains how to manually deploy your video upscaling application to a Vast.ai instance without needing Docker or local dependencies.

## Prerequisites

1. A Vast.ai account
2. An SSH client (built into macOS Terminal)
3. The deployment package: `vastai_minimal.zip` (already created)

## Step-by-Step Manual Deployment

### Step 1: Rent a Vast.ai Instance

1. Go to [Vast.ai](https://vast.ai/)
2. Click "Rent" and search for L4 GPU instances
3. Select an instance with:
   - At least 16GB RAM
   - At least 50GB storage
   - CUDA support
4. Configure the instance:
   - Use this Docker image: `nvidia/cuda:12.2.2-devel-ubuntu22.04`
   - Set the "On Start" command to: `/bin/bash`
   - Allocate at least 50GB disk space
5. Click "Rent" to create the instance

### Step 2: Get Instance Connection Details

Once your instance is running:
1. Note the IP address and SSH port from the Vast.ai dashboard
2. You'll use these to connect to your instance

### Step 3: Upload the Deployment Package

In your local terminal, navigate to the project directory and upload the package:

```bash
# Upload the deployment package to your Vast.ai instance
scp -P [SSH_PORT] vastai_minimal.zip root@[INSTANCE_IP]:/workspace/
```

Replace `[SSH_PORT]` with the SSH port and `[INSTANCE_IP]` with the instance IP address from your Vast.ai dashboard.

### Step 4: Set Up the Application on the Instance

Connect to your Vast.ai instance:

```bash
ssh -p [SSH_PORT] root@[INSTANCE_IP]
```

Once connected, run these commands on the instance:

```bash
# Navigate to workspace
cd /workspace

# Extract the deployment package
unzip vastai_minimal.zip

# Enter the deployment directory
cd vastai_minimal

# Make scripts executable
chmod +x *.sh

# Run the setup script
./setup_vastai.sh
```

### Step 5: Start the API Server

After setup completes, start the API server:

```bash
# Start the server in the background
nohup ./start_server.sh > server.log 2>&1 &
```

### Step 6: Test the Deployment

Check if the server is running:

```bash
# Check if the server is listening on port 5000
netstat -tlnp | grep :5000
```

Test the API:

```bash
# Health check
curl http://localhost:5000/health
```

If you want to access the API from outside the instance, you may need to use the instance's public IP:

```bash
# Health check using public IP
curl http://[INSTANCE_IP]:5000/health
```

### Step 7: Using the API

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

## Managing the Server

### Checking Server Logs

```bash
# View server logs
tail -f /workspace/vastai_minimal/server.log
```

### Stopping the Server

```bash
# Stop the server
pkill -f server.py
```

### Restarting the Server

```bash
# Restart the server
pkill -f server.py 2>/dev/null
cd /workspace/vastai_minimal
nohup ./start_server.sh > server.log 2>&1 &
```

## SSH-based Video Processing Workflow

Your application supports SSH-based video processing. You can:

1. Send a video to the Vast.ai instance:
   ```bash
   scp -P [SSH_PORT] your_video.mp4 root@[INSTANCE_IP]:/workspace/input.mp4
   ```

2. Submit an upscaling job via the API:
   ```bash
   curl -X POST http://[INSTANCE_IP]:5000/upscale \
     -H "Content-Type: application/json" \
     -d '{
       "input_path": "/workspace/input.mp4",
       "output_path": "/workspace/output.mp4"
     }'
   ```

3. Retrieve the upscaled video:
   ```bash
   scp -P [SSH_PORT] root@[INSTANCE_IP]:/workspace/output.mp4 upscaled_video.mp4
   ```

## Cost Management

Remember to stop or destroy your instance when not in use:
1. Go to your Vast.ai dashboard
2. Find your instance
3. Click "Stop" to pause billing (storage only) or "Destroy" to completely remove

## Troubleshooting

### Common Issues

1. **Connection refused**: Make sure the server is running and listening on port 5000

2. **Permission denied**: Check that file permissions are set correctly:
   ```bash
   chmod +x *.sh
   ```

3. **Setup fails**: Check the server logs for error messages:
   ```bash
   cat server.log
   ```

4. **GPU not detected**: Ensure you selected a GPU-enabled instance

### Checking Dependencies on Instance

To verify all dependencies are installed on the instance:
```bash
cd /workspace/vastai_minimal
python -c "import torch, cv2, basicsr, flask; print('All dependencies OK')"
```