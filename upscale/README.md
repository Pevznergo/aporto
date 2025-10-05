# Video Upscale Service (Vast.ai L4)

Production-ready video upscaler built around Real-ESRGAN (realesr-general-x4v3) with a simple REST API. Designed to run on a Vast.ai L4 instance via Docker. No local installation required.

Highlights
- 4× upscale, denoise 0.5, GFPGAN face enhancement
- REST API (Flask): POST /upscale, GET /job/<id>, GET /health
- Dockerized: start_server.sh starts server.py and downloads the model on first run
- File exchange via /app/inbox (input) and /app/outbox (output) inside the container

Key files
- Dockerfile — CUDA 11.8 base, installs requirements, exposes port 5000
- requirements.txt — Python libs (Real-ESRGAN stack, Flask, etc.)
- start_server.sh — installs deps on container boot, downloads Real-ESRGAN model if missing, runs server.py
- server.py — Flask API server with job queue
- upscale_app.py — core upscaling logic (frames → upscale → reassemble)

Deploy on Vast.ai from GitHub
Option A — With container registry (recommended)
1) Build and push this folder as an image (locally or in CI):
   docker build -t <registry>/<user>/aporto-upscale:latest .
   docker push <registry>/<user>/aporto-upscale:latest
2) Create an L4 instance in Vast.ai using that image. Ensure port 5000 is reachable.
3) The container runs start_server.sh → API at http://<instance_ip>:5000

Option B — Build image directly on the instance
1) SSH to the instance, then:
   git clone <this repo>
   cd upscale
   docker build -t aporto-upscale:latest .
   docker run --gpus all -p 5000:5000 aporto-upscale:latest

API
- Health
  GET /health → { "status": "healthy", "service": "video-upscale-api" }

- Submit job
  POST /upscale
  Body:
  {
    "input_path": "/app/inbox/input.mp4",
    "output_path": "/app/outbox/output.mp4"
  }
  Returns 202 with { job_id, status }

- Job status
  GET /job/<job_id>
  Returns { job_id, status: processing|completed|failed, start_time, end_time, duration }

File exchange
- Upload inputs to /app/inbox in the container (e.g., scp)
- Outputs are written to /app/outbox

Model download
- start_server.sh downloads realesr-general-x4v3.pth into models/ on first run

Smoke test (on instance)
- curl http://127.0.0.1:5000/health
- curl -X POST http://127.0.0.1:5000/upscale -H 'Content-Type: application/json' -d '{"input_path":"/app/inbox/in.mp4","output_path":"/app/outbox/out.mp4"}'
- curl http://127.0.0.1:5000/job/1

Requirements
- NVIDIA GPU (CUDA 11.8), port 5000 open
- Sufficient disk for temporary frames and outputs
