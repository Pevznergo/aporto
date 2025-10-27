# Emergency Fix for Running Instance

## Current Issues Detected

Based on the error output, your instance has these problems:

1. ✅ **basicsr patch** - Already applied successfully
2. ❌ **blinker distutils error** - Still occurring during pip install
3. ❌ **start_server.sh** - Using wrong paths and python command
4. ❌ **Missing realesrgan** - Not installed yet

## Quick Fix Commands

SSH into your instance and run these commands:

```bash
# 1. Navigate to workspace
cd /workspace/aporto

# 2. Pull latest fixes
git pull

# 3. Make scripts executable
chmod +x upscale/vastai_deployment/*.sh

# 4. Run the complete fix script
./upscale/vastai_deployment/apply_fix.sh
```

This will:
- Apply the basicsr fix (already done, but safe to re-run)
- Update environment variables
- Verify imports
- Restart the service

## If pip install is currently failing

If you're in the middle of a failed installation:

```bash
cd /workspace/aporto

# Activate venv
source .venv/bin/activate

# Install with --ignore-installed to bypass distutils error
pip install --ignore-installed -r upscale/vastai_deployment/requirements.txt

# Apply fixes
./upscale/vastai_deployment/auto_fix_basicsr.sh

# Restart service
systemctl restart vast-upscale.service
```

## If you need a complete fresh install

```bash
# Stop the service
systemctl stop vast-upscale.service

# Navigate to workspace
cd /workspace/aporto

# Pull latest code
git pull

# Remove old venv (if needed)
rm -rf .venv

# Run fresh installation
chmod +x upscale/vastai_deployment/install.sh
./upscale/vastai_deployment/install.sh
```

## Verification Steps

After applying fixes, verify everything works:

```bash
# 1. Check service status
systemctl status vast-upscale.service

# 2. Check if imports work
source /workspace/aporto/.venv/bin/activate
python3 -c "from realesrgan.utils import RealESRGANer; print('✅ Import successful')"

# 3. Test health endpoint
curl http://localhost:5000/health

# 4. Check logs
tail -f /workspace/server.log
```

## What Was Fixed in Latest Code

The latest code includes:

1. **auto_fix_basicsr.sh** - Automatic basicsr patching
2. **fix_distutils_packages.sh** - Handles blinker/PyYAML distutils errors
3. **Updated start_server.sh** - Correct paths and python3 command
4. **Updated install.sh** - Applies both fixes automatically
5. **Updated setup_vastai.sh** - Applies both fixes automatically

## Common Errors and Solutions

### Error: "No module named 'realesrgan'"
**Solution:** Install requirements
```bash
source /workspace/aporto/.venv/bin/activate
pip install --ignore-installed -r upscale/vastai_deployment/requirements.txt
```

### Error: "Cannot uninstall blinker 1.4"
**Solution:** Use --ignore-installed flag (now automatic in scripts)
```bash
pip install --ignore-installed -r upscale/vastai_deployment/requirements.txt
```

### Error: "python: command not found"
**Solution:** Latest scripts now use python3 instead of python

### Error: "cd: /app: No such file"
**Solution:** Latest start_server.sh uses correct path (/workspace/aporto)

## Contact

If issues persist after applying these fixes, check:
- Service logs: `journalctl -u vast-upscale.service -n 100`
- Application logs: `tail -f /workspace/server.log`
- GPU status: `nvidia-smi`
