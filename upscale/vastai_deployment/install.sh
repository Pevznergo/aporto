#!/bin/bash
# VASTAI GPU Server Installation Script (macOS version)
# Run this on a macOS system to set up the environment

set -e

echo "🚀 Starting VASTAI GPU Server Installation (macOS version)..."

# 1. Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo " Homebrew is not installed. Please install Homebrew first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# 2. Install system packages
echo "📦 Installing system packages..."
brew install python3 ffmpeg git wget

# 3. Create project directory and navigate
mkdir -p /workspace/aporto
cd /workspace/aporto

# 4. Create and activate virtual environment
echo "🐍 Setting up Python virtual environment..."

# Create venv
if [ -d .venv ]; then
    echo "  Removing old venv..."
    rm -rf .venv
fi

python3 -m venv .venv

# Verify venv was created
if [ ! -f .venv/bin/python3 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
else
    source .venv/bin/activate
    echo "  ✅ Virtual environment created"
fi

# 5. Upgrade pip and install requirements
echo "📚 Installing Python dependencies..."
python -m pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r upscale/vastai_deployment/requirements.txt

# 6. Create necessary directories
echo "📁 Creating directories..."
mkdir -p /workspace/aporto/upscale/models
mkdir -p /workspace/cut/to_cut /workspace/cut/cuted /workspace/cut/to_upscale /workspace/cut/upscaled

# 7. Download model weights
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
    # Use the correct URL for the model and retry if needed
    wget -O realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth || {
        echo "  First attempt failed, trying alternative URL..."
        rm -f realesr-general-x4v3.pth
        wget -O realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.3.0/realesr-general-x4v3.pth
    }
fi

# Validate downloaded model files
echo "🔍 Validating model files..."
for model in GFPGANv1.4.pth realesr-general-x4v3.pth; do
    if [ -f "$model" ]; then
        if [ ! -s "$model" ]; then
            echo "  ❌ $model is empty, removing..."
            rm "$model"
        else
            echo "  ✅ $model downloaded successfully"
        fi
    else
        echo "  ❌ $model not found"
    fi
done

echo "📏 Model file sizes:"
ls -lh /workspace/aporto/upscale/models/*.pth

# 8. Validate models with Python script
echo "🧪 Validating model files with Python..."
cd /workspace/aporto
source .venv/bin/activate

# Copy validation script to workspace (using absolute path)
cp /workspace/aporto/upscale/vastai_deployment/validate_models.py .

python validate_models.py || {
    echo "❌ Model validation failed!"
    echo "Trying to re-download models..."
    
    cd /workspace/aporto/upscale/models
    
    # Re-download GFPGAN
    if [ -f "GFPGANv1.4.pth" ]; then
        rm GFPGANv1.4.pth
    fi
    echo "  Re-downloading GFPGAN model..."
    wget -O GFPGANv1.4.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
    
    # Re-download Real-ESRGAN with retry logic
    if [ -f "realesr-general-x4v3.pth" ]; then
        rm realesr-general-x4v3.pth
    fi
    echo "  Re-downloading Real-ESRGAN model..."
    wget -O realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth || {
        echo "  First attempt failed, trying alternative URL..."
        rm -f realesr-general-x4v3.pth
        wget -O realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.3.0/realesr-general-x4v3.pth
    }
    
    # Validate again
    cd /workspace/aporto
    python validate_models.py || {
        echo "❌ Model validation failed even after re-download!"
        exit 1
    }
}

# 9. Create environment file
echo "⚙️ Creating environment configuration..."
cat > /workspace/aporto/.env << 'EOF'
# Python interpreter (for subprocess calls)
VENV_PYTHON=/workspace/aporto/.venv/bin/python

# Model paths
GFPGAN_MODEL_PATH=/workspace/aporto/upscale/models/GFPGANv1.4.pth
REALESRGAN_MODEL_PATH=/workspace/aporto/upscale/models/realesr-general-x4v3.pth
XDG_CACHE_HOME=/workspace/aporto/upscale/models

# Cut configuration
CUT_BASE_DIR=/workspace/cut
CUT_REQUIRE_CUDA=0
CUT_FORCE_DEVICE=cpu
CUT_ENABLE_UPSCALE=1
WHISPER_MODEL=small

# OpenAI API (set this manually)
# OPENAI_API_KEY=your_key_here
EOF

# 10. Test installation
echo "🧪 Testing installation..."
cd /workspace/aporto
source .venv/bin/activate
source .env

echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Set your OPENAI_API_KEY in /workspace/aporto/.env (if needed)"
echo "2. Run the server: nohup python3 upscale/vastai_deployment/server.py >/workspace/server.log 2>&1 &"
echo "3. View logs: tail -f /workspace/server.log"
echo "4. Test health endpoint: curl http://localhost:5000/health"