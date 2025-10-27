# BasicSR Torchvision Compatibility Fix

## Problem

The `basicsr` library (a dependency of Real-ESRGAN) has a compatibility issue with torchvision >= 0.19.0. The library attempts to import from `torchvision.transforms.functional_tensor`, which was removed in newer versions of torchvision.

### Error Message
```
Failed to import RealESRGANer from realesrgan.utils: No module named 'torchvision.transforms.functional_tensor'
```

### Root Cause
In `basicsr/data/degradations.py`, line 8:
```python
from torchvision.transforms.functional_tensor import rgb_to_grayscale
```

This import path is deprecated in torchvision 0.19+. The function now exists in:
```python
from torchvision.transforms.functional import rgb_to_grayscale
```

## Solution

We've implemented an automatic fix that patches the `basicsr` library during deployment. The fix is applied through the `auto_fix_basicsr.sh` script, which:

1. Locates the `degradations.py` file in the installed basicsr package
2. Creates a timestamped backup of the original file
3. Replaces the deprecated import with the correct one
4. Verifies the fix by attempting to import RealESRGANer

### How It Works

The fix is automatically applied in multiple scenarios:

1. **Initial Installation** (`install.sh`)
   - During fresh instance setup
   - Runs after pip installs all requirements

2. **Instance Startup** (`start.sh`)
   - Every time the instance starts
   - Ensures the fix persists even if packages are reinstalled

3. **Manual Setup** (`setup_vastai.sh`)
   - When running setup script manually
   - Part of the standard deployment process

4. **Manual Fix Application** (`apply_fix.sh`)
   - Can be run standalone after package updates
   - Useful for troubleshooting

### Auto-Fix Script Features

The `auto_fix_basicsr.sh` script is:
- **Idempotent**: Can be run multiple times safely
- **Smart Detection**: Tries multiple strategies to locate the file
  - Searches in venv if present
  - Searches in system-wide packages
  - Uses Python import to find the module
  - Checks all common installation locations
- **Safe**: Creates timestamped backups before patching
- **Verified**: Tests the import after patching

## Usage

### Automatic (Recommended)

The fix is applied automatically when using any of these scripts:
```bash
# Fresh installation
./install.sh

# Regular startup
./start.sh

# Setup on existing instance
./setup_vastai.sh
```

### Manual Application

If you need to apply the fix manually:
```bash
cd /workspace/aporto/upscale/vastai_deployment
chmod +x auto_fix_basicsr.sh
./auto_fix_basicsr.sh
```

### Verification

To verify the fix was applied successfully:
```bash
# Activate venv if using one
source /workspace/aporto/.venv/bin/activate

# Test import
python3 -c "from realesrgan.utils import RealESRGANer; print('✅ Fix successful')"
```

## Files Modified

- **Created**: `auto_fix_basicsr.sh` - Centralized fix script
- **Updated**: `install.sh` - Calls auto-fix during installation
- **Updated**: `setup_vastai.sh` - Calls auto-fix during setup
- **Updated**: `start.sh` - Calls auto-fix on every startup
- **Updated**: `apply_fix.sh` - Uses auto-fix for consistency

## Backup Files

The script creates backups with timestamps:
```
degradations.py.bak.20251027_064914
```

These can be used to restore the original file if needed.

## Troubleshooting

### Fix Not Applied

If the error persists:

1. Check if basicsr is installed:
   ```bash
   pip3 show basicsr
   ```

2. Manually locate the file:
   ```bash
   find /workspace/aporto/.venv -name "degradations.py" -path "*/basicsr/data/degradations.py"
   ```

3. Verify the import line:
   ```bash
   grep "rgb_to_grayscale" <path_to_degradations.py>
   ```

4. Run the fix script with verbose output:
   ```bash
   bash -x auto_fix_basicsr.sh
   ```

### Permissions Issues

If you get permission denied errors:
```bash
chmod +x auto_fix_basicsr.sh
# Or run with sudo if needed
sudo ./auto_fix_basicsr.sh
```

### Package Reinstallation

If you reinstall packages (e.g., `pip install --force-reinstall basicsr`), the fix will need to be reapplied. Simply run:
```bash
./auto_fix_basicsr.sh
```

Or restart the service (which automatically applies the fix):
```bash
systemctl restart vast-upscale.service
```

## Technical Details

### Import Change
- **Old** (torchvision < 0.19): `from torchvision.transforms.functional_tensor import rgb_to_grayscale`
- **New** (torchvision >= 0.19): `from torchvision.transforms.functional import rgb_to_grayscale`

### Affected Package
- **Package**: basicsr
- **File**: `basicsr/data/degradations.py`
- **Line**: ~8
- **Upstream Issue**: The basicsr maintainers should update their package to support newer torchvision versions

### Why Not Downgrade Torchvision?

We could downgrade torchvision to < 0.19, but:
- Newer versions have bug fixes and performance improvements
- Other dependencies may require newer torchvision
- The patch is simple and reliable
- It's better to fix the actual issue than work around it

## Future Considerations

This fix may not be needed if:
- The basicsr package is updated to support torchvision >= 0.19
- We switch to a different upscaling library
- The upstream issue is resolved

Until then, this automatic fix ensures smooth deployments without manual intervention.
