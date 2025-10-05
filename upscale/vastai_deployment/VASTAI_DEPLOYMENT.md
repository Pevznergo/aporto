# Deployment Guide for Vast.ai L4 Server

This guide explains how to deploy the Video Upscaling Application on a Vast.ai rented L4 server.

## Prerequisites

1. Rent an L4 server on [Vast.ai](https://vast.ai/)
2. Ensure the server has:
   - CUDA-compatible GPU
   - At least 16GB RAM
   - At least 50GB storage
   - SSH access enabled

## Deployment Steps

### 1. Connect to Your Vast.ai Instance

```bash
ssh -p <port> root@<ip_address>
```

Replace `<port>` and `<ip_address>` with your instance details from Vast.ai.

### 2. Clone the Repository

```bash
git clone <repository_url>
cd upscale
```

### 3. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Install system dependencies
- Install Python packages
- Download Real-ESRGAN models

### 4. Configure SSH Access

To enable SSH file transfer, you'll need to set up SSH keys or configure password access.

#### Option A: SSH Keys (Recommended)

1. Generate SSH keys on your Vast.ai instance:
   ```bash
   ssh-keygen -t rsa -b 4096
   ```

2. Copy the public key to your remote server:
   ```bash
   ssh-copy-id user@remote_server
   ```

#### Option B: Password Authentication

Edit SSH config to enable password authentication:
```bash
echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
systemctl restart ssh
```

### 5. Run the Application

#### SSH-based Processing

```bash
python upscale_app.py <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>
```

Or use the provided script:
```bash
./run_upscale.sh <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>
```

#### API Server Mode

```bash
python server.py
```

The API will be available at `http://<your_instance_ip>:5000`

### 6. Docker Deployment (Alternative)

If you prefer Docker:

1. Build the image:
   ```bash
   docker build -t video-upscale .
   ```

2. Run with SSH processing:
   ```bash
   docker run --gpus all -it video-upscale \
     python upscale_app.py <ssh_user> <ssh_host> <remote_input_path> <remote_output_path>
   ```

3. Run API server:
   ```bash
   docker run --gpus all -p 5000:5000 video-upscale python server.py
   ```

## Monitoring and Maintenance

### Check Resource Usage

```bash
# GPU usage
nvidia-smi

# System resources
htop

# Disk usage
df -h
```

### Logs and Debugging

Check application logs for any errors:
```bash
# If running in background, check log files
tail -f upscale.log

# Or run with verbose output
python upscale_app.py <args> 2>&1 | tee upscale.log
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**: Reduce batch size or use smaller videos
2. **SSH Connection Failed**: Check SSH keys or firewall settings
3. **Model Download Failed**: Check internet connection and try again
4. **Permission Denied**: Ensure proper file permissions

### Support

For issues with the application, please check:
- [README.md](README.md)
- [README_UPSCALE.md](README_UPSCALE.md)
- [README_API.md](README_API.md)

For Vast.ai specific issues, please contact Vast.ai support.