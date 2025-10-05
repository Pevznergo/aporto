# Consolidated

Usage examples were merged into README.md.

## 1. SSH-based Processing

### Command Line Usage

```bash
# Process a video from a remote server
python upscale_app.py user 192.168.1.100 /path/to/input.mp4 /path/to/output.mp4

# Using the provided script
./run_upscale.sh user 192.168.1.100 /path/to/input.mp4 /path/to/output.mp4
```

### Python API Usage

```python
from upscale_app import process_video_from_ssh

# Process video via SSH
success = process_video_from_ssh(
    ssh_user="user",
    ssh_host="192.168.1.100",
    remote_input_path="/path/to/input.mp4",
    remote_output_path="/path/to/output.mp4"
)

if success:
    print("Video processed successfully!")
```

## 2. Direct File Processing

### Python API Usage

```python
from upscale_app import upscale_video_with_realesrgan

# Upscale a local video file
success = upscale_video_with_realesrgan(
    input_video_path="/local/path/to/input.mp4",
    output_video_path="/local/path/to/output.mp4"
)

if success:
    print("Video upscaled successfully!")
```

## 3. REST API Usage

### Start the Server

```bash
python server.py
```

### Submit a Job

```bash
# Submit upscaling job
curl -X POST http://localhost:5000/upscale \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "/videos/input.mp4",
    "output_path": "/videos/output.mp4"
  }'

# Response:
# {
#   "job_id": 1,
#   "status": "processing"
# }
```

### Check Job Status

```bash
# Check job status
curl http://localhost:5000/job/1

# Response when processing:
# {
#   "job_id": 1,
#   "status": "processing",
#   "start_time": 1640995200.0
# }

# Response when completed:
# {
#   "job_id": 1,
#   "status": "completed",
#   "start_time": 1640995200.0,
#   "end_time": 1640995500.0,
#   "duration": 300.0
# }
```

## 4. Docker Usage

### Build Docker Image

```bash
docker build -t video-upscale .
```

### Run with SSH Processing

```bash
docker run --gpus all -it video-upscale \
  python upscale_app.py user 192.168.1.100 /path/to/input.mp4 /path/to/output.mp4
```

### Run API Server

```bash
docker run --gpus all -p 5000:5000 video-upscale python server.py
```

## Configuration

The application uses the following fixed settings:
- Model: realesr-general-x4v3
- Denoise Strength: 0.5
- Upscale Factor: 4x
- Face Enhancement: Enabled (GFPGAN)

These settings can be modified in the [config.json](config.json) file.