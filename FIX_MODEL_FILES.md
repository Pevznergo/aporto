# Fix for Real-ESRGAN Model File Error

## Problem
When running the upscale process, you may encounter this error:
```
EOFError: Ran out of input
```

This error occurs when the Real-ESRGAN model file (`realesr-general-x4v3.pth`) or the GFPGAN model file (`GFPGANv1.4.pth`) is corrupted or empty.

## Solution
Run the provided script to automatically download fresh copies of the model files:

```bash
./fix_model_files.sh
```

## What the script does
1. Checks if the model files exist and are valid
2. Removes any corrupted or empty model files
3. Downloads fresh copies of the model files from the official repositories
4. Validates that the downloaded files are working correctly

## After running the script
Once the script completes successfully, restart your upscaling service:
```bash
# If running the server directly
python upscale/vastai_deployment/server.py

# Or if using Docker, restart the container
docker-compose down
docker-compose up
```

## Manual fix (if script doesn't work)
If the script doesn't work, you can manually download the model files:

1. Create the models directory:
   ```bash
   mkdir -p models
   ```

2. Download Real-ESRGAN model:
   ```bash
   wget -O models/realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
   ```

3. Download GFPGAN model:
   ```bash
   wget -O models/GFPGANv1.4.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
   ```