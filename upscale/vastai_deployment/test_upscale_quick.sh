#!/bin/bash
# Quick test: create 1-sec video and upscale it

set -e

cd /workspace/aporto

echo "🧪 Quick Upscale Test"
echo ""

# 1. Create test video
echo "1. Creating 1-second test video..."
TEST_INPUT="/tmp/test_1sec.mp4"
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=30 \
       -f lavfi -i sine=frequency=1000:duration=1 \
       -c:v libx264 -preset ultrafast -crf 23 \
       -c:a aac -b:a 128k \
       -y "$TEST_INPUT" 2>&1 | tail -5

if [ ! -f "$TEST_INPUT" ]; then
    echo "❌ Failed to create test video"
    exit 1
fi

SIZE_IN=$(du -h "$TEST_INPUT" | cut -f1)
echo "✅ Created: $TEST_INPUT ($SIZE_IN)"
echo ""

# 2. Test upscale
echo "2. Testing upscale..."
TEST_OUTPUT="/tmp/test_1sec_upscaled.mp4"

# Load environment
source /workspace/aporto/.env

# Run upscale using the venv python
time /workspace/aporto/.venv/bin/python - <<'PYCODE'
import sys
sys.path.insert(0, '/workspace/aporto/upscale/vastai_deployment')
from upscale_app import upscale_video_with_realesrgan

success = upscale_video_with_realesrgan('/tmp/test_1sec.mp4', '/tmp/test_1sec_upscaled.mp4')
if success:
    print('\n✅ Upscale completed successfully!')
    sys.exit(0)
else:
    print('\n❌ Upscale failed')
    sys.exit(1)
PYCODE

if [ $? -eq 0 ] && [ -f "$TEST_OUTPUT" ]; then
    SIZE_OUT=$(du -h "$TEST_OUTPUT" | cut -f1)
    echo ""
    echo "📊 Results:"
    echo "  Input:  $TEST_INPUT ($SIZE_IN)"
    echo "  Output: $TEST_OUTPUT ($SIZE_OUT)"
    
    # Get video info
    echo ""
    echo "Input resolution:"
    ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$TEST_INPUT"
    echo "Output resolution:"
    ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$TEST_OUTPUT"
    
    echo ""
    echo "🎉 Test PASSED!"
else
    echo "❌ Test FAILED"
    exit 1
fi
