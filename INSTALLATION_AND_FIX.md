# Installation and Fix Guide for Video Upscaling Service

## Problem
When running the upscale process, you may encounter this error:
```
EOFError: Ran out of input
```

This error occurs when the Real-ESRGAN model file (`realesr-general-x4v3.pth`) or the GFPGAN model file (`GFPGANv1.4.pth`) is corrupted or empty.

## Root Cause
The issue is typically caused by:
1. Incomplete or interrupted model downloads during installation
2. Corrupted model files due to network issues
3. Incorrect model file URLs in the installation script

## Solution

### 1. Run the Installation Script
The updated installation script now includes better error handling and model validation:

```bash
chmod +x /workspace/aporto/upscale/vastai_deployment/install.sh
/workspace/aporto/upscale/vastai_deployment/install.sh
```

### 2. What the Installation Script Does
- Installs all required system packages and Python dependencies
- Creates a Python virtual environment
- Downloads the model files with proper validation
- Validates the downloaded model files using a Python script
- Automatically re-downloads corrupted files if needed
- Sets up the systemd service for automatic startup

### 3. Manual Fix (if installation script doesn't work)
If you're still experiencing issues, you can manually fix the model files:

1. Navigate to the models directory:
   ```bash
   cd /workspace/aporto/upscale/models
   ```

2. Remove corrupted model files:
   ```bash
   rm -f GFPGANv1.4.pth realesr-general-x4v3.pth
   ```

3. Download fresh copies:
   ```bash
   wget -O GFPGANv1.4.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
   wget -O realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
   ```

4. Validate the files:
   ```bash
   cd /workspace/aporto
   python validate_models.py
   ```

### 4. Check Service Status
After installation or manual fix, check that the service is running correctly:

```bash
systemctl status vast-upscale.service
```

### 5. Check Health Endpoint
Verify that the service is healthy:
```bash
curl http://localhost:5000/health
```

A healthy response should look like:
```json
{
  "status": "healthy",
  "service": "video-upscale-api",
  "models": {
    "gfpgan": {
      "status": "ok",
      "path": "/workspace/aporto/upscale/models/GFPGANv1.4.pth",
      "error": null
    },
    "realesrgan": {
      "status": "ok",
      "path": "/workspace/aporto/upscale/models/realesr-general-x4v3.pth",
      "error": null
    }
  }
}
```

## Troubleshooting

### If the service fails to start:
1. Check the logs:
   ```bash
   tail -f /workspace/server.log
   ```

2. Try restarting the service:
   ```bash
   systemctl restart vast-upscale.service
   ```

### If model validation fails:
1. Check file permissions:
   ```bash
   ls -la /workspace/aporto/upscale/models/
   ```

2. Ensure the files are not empty:
   ```bash
   ls -lh /workspace/aporto/upscale/models/
   ```

3. Manually validate with Python:
   ```bash
   cd /workspace/aporto
   source .venv/bin/activate
   python -c "
import torch
torch.load('/workspace/aporto/upscale/models/realesr-general-x4v3.pth', map_location=torch.device('cpu'))
print('Real-ESRGAN model is valid')
torch.load('/workspace/aporto/upscale/models/GFPGANv1.4.pth', map_location=torch.device('cpu'))
print('GFPGAN model is valid')
"
   ```

## Prevention
To prevent this issue in the future:
1. Always use the updated installation script
2. Ensure stable network connectivity during installation
3. Regularly check the health endpoint to verify model files are valid
4. Monitor disk space to ensure there's enough room for model files