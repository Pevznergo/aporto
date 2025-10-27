# Deployment Checklist for Vast.ai Instance

## ✅ Pre-Deployment

- [ ] Clone repository to `/workspace/aporto`
- [ ] Ensure all scripts have execute permissions
- [ ] Review `.env` configuration requirements

## 🚀 Fresh Installation

Use this for a brand new instance:

```bash
cd /workspace/aporto
chmod +x upscale/vastai_deployment/install.sh
./upscale/vastai_deployment/install.sh
```

**What it does:**
- Installs system packages
- Creates Python venv
- Installs all requirements
- **Automatically applies basicsr fix**
- Downloads model weights
- Creates systemd service
- Starts the upscale service

## 🔄 Existing Instance Update

If you're updating an existing instance:

```bash
cd /workspace/aporto
git pull
chmod +x upscale/vastai_deployment/apply_fix.sh
./upscale/vastai_deployment/apply_fix.sh
```

**What it does:**
- **Applies basicsr compatibility fix**
- Updates environment configuration
- Verifies imports
- Restarts service

## 🔧 Manual Compatibility Fix

If you only need to apply the basicsr fix:

```bash
cd /workspace/aporto
chmod +x upscale/vastai_deployment/auto_fix_basicsr.sh
./upscale/vastai_deployment/auto_fix_basicsr.sh
systemctl restart vast-upscale.service
```

## 📋 Post-Deployment Verification

1. **Check service status:**
   ```bash
   systemctl status vast-upscale.service
   ```

2. **Verify imports:**
   ```bash
   source /workspace/aporto/.venv/bin/activate
   python3 -c "from realesrgan.utils import RealESRGANer; print('✅ OK')"
   ```

3. **Test health endpoint:**
   ```bash
   curl http://localhost:5000/health
   ```

4. **Check logs:**
   ```bash
   tail -f /workspace/server.log
   ```

## 🔁 Instance Restart

The fix is automatically applied on every restart via `start.sh`:

```bash
cd /workspace/aporto/upscale/vastai_deployment
./start.sh
```

## ⚠️ Common Issues

### Issue: "No module named 'torchvision.transforms.functional_tensor'"

**Solution:**
```bash
/workspace/aporto/upscale/vastai_deployment/auto_fix_basicsr.sh
systemctl restart vast-upscale.service
```

### Issue: Service fails to start

**Check logs:**
```bash
journalctl -u vast-upscale.service -n 50 --no-pager
tail -f /workspace/server.log
```

**Verify fix was applied:**
```bash
grep "from torchvision.transforms.functional import rgb_to_grayscale" \
  $(find /workspace/aporto/.venv -name "degradations.py" -path "*/basicsr/data/degradations.py")
```

### Issue: Permission denied

**Fix permissions:**
```bash
cd /workspace/aporto/upscale/vastai_deployment
chmod +x *.sh
```

## 🎯 Environment Variables

Ensure these are set in `/workspace/aporto/.env`:

```bash
# Required
VENV_PYTHON=/workspace/aporto/.venv/bin/python
GFPGAN_MODEL_PATH=/workspace/aporto/upscale/models/GFPGANv1.4.pth
REALESRGAN_MODEL_PATH=/workspace/aporto/upscale/models/realesr-general-x4v3.pth

# Optional (set manually)
OPENAI_API_KEY=your_key_here
```

## 📊 System Requirements

Verify your instance meets these requirements:

- [ ] CUDA-compatible GPU (L4 recommended)
- [ ] At least 16GB RAM
- [ ] At least 50GB storage
- [ ] Ubuntu 20.04+ or compatible
- [ ] Internet connectivity for model downloads

## 🔐 Security Notes

- Change default SSH port if exposed to internet
- Set strong passwords/keys
- Configure firewall rules
- Don't commit API keys to repository
- Use environment variables for secrets

## 📞 Support

If issues persist:

1. Check [BASICSR_FIX.md](BASICSR_FIX.md) for detailed fix information
2. Review [QUICK_FIX.md](QUICK_FIX.md) for troubleshooting
3. Check service logs: `journalctl -u vast-upscale.service -f`
4. Verify GPU availability: `nvidia-smi`

## 🎉 Success Indicators

Your deployment is successful when:

- ✅ Service is running: `systemctl is-active vast-upscale.service` returns "active"
- ✅ Health check passes: `curl http://localhost:5000/health` returns 200
- ✅ Imports work: Python can import RealESRGANer without errors
- ✅ GPU detected: `nvidia-smi` shows your GPU
- ✅ Models loaded: Model files exist in `/workspace/aporto/upscale/models/`
