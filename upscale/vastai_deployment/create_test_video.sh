#!/bin/bash
# Create a 1-second test video for quick upscaling tests

OUTPUT=${1:-/tmp/test_1sec.mp4}

echo "Creating 1-second test video: $OUTPUT"

# Create a 1-second video with a simple pattern
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=30 \
       -f lavfi -i sine=frequency=1000:duration=1 \
       -c:v libx264 -preset fast -crf 23 \
       -c:a aac -b:a 128k \
       -y "$OUTPUT"

if [ -f "$OUTPUT" ]; then
    SIZE=$(du -h "$OUTPUT" | cut -f1)
    echo "✅ Created: $OUTPUT (size: $SIZE)"
    
    # Show video info
    ffprobe -v error -show_entries format=duration,size \
            -show_entries stream=width,height,codec_name \
            -of default=noprint_wrappers=1 "$OUTPUT" 2>/dev/null
else
    echo "❌ Failed to create video"
    exit 1
fi
