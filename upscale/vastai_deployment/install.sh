#!/bin/bash
# VASTAI GPU Server Installation Script
# Run this on a fresh VASTAI instance to set up the environment

set -e

echo "🚀 Starting VASTAI GPU Server Installation..."

# 1. Install system packages
echo "📦 Installing system packages..."
apt-get update -y
apt-get install -y python3-venv python3-pip ffmpeg git wget curl

# 2. Create project directory and navigate
mkdir -p /workspace/aporto
cd /workspace/aporto

# 3. Create and activate virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# 4. Upgrade pip and install requirements
echo "📚 Installing Python dependencies..."
python -m pip install --upgrade pip setuptools wheel

# Install requirements (assuming this script is in vastai_deployment/)
pip install -r upscale/vastai_deployment/requirements.txt

# Patch basicsr import for torchvision 0.19+ (functional_tensor removed)
echo "🩹 Patching basicsr for torchvision compatibility..."
PY_FILE=$(python - <<'PY'
import sys, inspect
try:
    import basicsr.data.degradations as d
    print(inspect.getfile(d))
except Exception:
    sys.exit(0)
PY
)
if [ -n "$PY_FILE" ] && grep -q "from torchvision.transforms.functional_tensor import rgb_to_grayscale" "$PY_FILE"; then
  cp "$PY_FILE" "$PY_FILE.bak"
  sed -i "s/from torchvision.transforms.functional_tensor import rgb_to_grayscale/from torchvision.transforms.functional import rgb_to_grayscale/" "$PY_FILE"
  echo "  Patched: $PY_FILE"
else
  echo "  No patch needed."
fi

# 5. Create necessary directories
echo "📁 Creating directories..."
mkdir -p /workspace/aporto/upscale/models
mkdir -p /workspace/cut/to_cut /workspace/cut/cuted /workspace/cut/to_upscale /workspace/cut/upscaled

# 6. Download model weights
echo "🎯 Downloading model weights..."
cd /workspace/aporto/upscale/models

# GFPGAN weights
if [ ! -f "GFPGANv1.4.pth" ]; then
    echo "  Downloading GFPGAN model..."
    wget -O GFPGANv1.4.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
fi

# Real-ESRGAN weights  
if [ ! -f "realesr-general-x4v3.pth" ]; then
    echo "  Downloading Real-ESRGAN model..."
    wget -O realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.3.0/realesr-general-x4v3.pth
fi

echo "📏 Model file sizes:"
ls -lh /workspace/aporto/upscale/models/*.pth

# 7. Create environment file
echo "⚙️ Creating environment configuration..."
cat > /workspace/aporto/.env << 'EOF'
# Model paths
GFPGAN_MODEL_PATH=/workspace/aporto/upscale/models/GFPGANv1.4.pth
REALESRGAN_MODEL_PATH=/workspace/aporto/upscale/models/realesr-general-x4v3.pth
XDG_CACHE_HOME=/workspace/aporto/upscale/models

# Cut configuration
CUT_BASE_DIR=/workspace/cut
CUT_REQUIRE_CUDA=1
CUT_FORCE_DEVICE=cuda
CUT_ENABLE_UPSCALE=1
WHISPER_MODEL=small

# OpenAI API (set this manually)
# OPENAI_API_KEY=your_key_here
EOF

# 8. Test installation
echo "🧪 Testing installation..."
cd /workspace/aporto
source .venv/bin/activate
source .env

python -c "
import numpy as np
import torch
import torchvision
from realesrgan.utils import RealESRGANer
from gfpgan import GFPGANer
print('✅ All imports successful!')
print(f'NumPy: {np.__version__}')
print(f'PyTorch: {torch.__version__}')
print(f'TorchVision: {torchvision.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"

# 9. Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/vast-upscale.service << 'EOF'
[Unit]
Description=VAST GPU Upscale Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/aporto
Environment=PATH=/workspace/aporto/.venv/bin
EnvironmentFile=/workspace/aporto/.env
ExecStart=/workspace/aporto/.venv/bin/python upscale/vastai_deployment/server.py
Restart=always
RestartSec=10
StandardOutput=append:/workspace/server.log
StandardError=append:/workspace/server.log

[Install]
WantedBy=multi-user.target
EOF

# 10. Start and enable service
systemctl daemon-reload
systemctl enable vast-upscale.service
systemctl start vast-upscale.service

echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Set your OPENAI_API_KEY in /workspace/aporto/.env"
echo "2. Check service status: systemctl status vast-upscale.service"
echo "3. View logs: tail -f /workspace/server.log"
echo "4. Test health endpoint: curl http://localhost:5000/health"
echo ""
echo "Service will automatically start on boot."