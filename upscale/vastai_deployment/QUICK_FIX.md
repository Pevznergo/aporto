# Quick Fix Reference

## 🔧 Automatic Fix (Recommended)

The basicsr compatibility fix is now **automatically applied** on every instance startup. You don't need to do anything!

## ⚡ Manual Fix (If Needed)

If you encounter this error:
```
Failed to import RealESRGANer: No module named 'torchvision.transforms.functional_tensor'
```

Run this single command:
```bash
/workspace/aporto/upscale/vastai_deployment/auto_fix_basicsr.sh
```

Then restart the service:
```bash
systemctl restart vast-upscale.service
```

## ✅ Verify Fix

```bash
python3 -c "from realesrgan.utils import RealESRGANer; print('✅ Working!')"
```

## 📋 What Gets Fixed

The script automatically patches `basicsr/data/degradations.py` to use the correct import for torchvision >= 0.19:

**Before:**
```python
from torchvision.transforms.functional_tensor import rgb_to_grayscale
```

**After:**
```python
from torchvision.transforms.functional import rgb_to_grayscale
```

## 🚀 When Is The Fix Applied?

- ✅ During initial installation (`install.sh`)
- ✅ On every instance startup (`start.sh`)
- ✅ During manual setup (`setup_vastai.sh`)
- ✅ When running apply_fix.sh
- ✅ Anytime you run `auto_fix_basicsr.sh`

## 🛠️ Scripts Updated

All deployment scripts now include automatic fixing:
- `install.sh` - Fresh installation
- `start.sh` - Instance startup
- `setup_vastai.sh` - Manual setup
- `apply_fix.sh` - Complete fix application
- `auto_fix_basicsr.sh` - Standalone fix script

## 📖 Full Documentation

See [BASICSR_FIX.md](BASICSR_FIX.md) for detailed information.
