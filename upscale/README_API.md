# Consolidated

See README.md in this folder for API documentation.

This document describes the REST API for the Video Upscaling application.

## Endpoints

### Health Check

**GET** `/health`

Check if the server is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "video-upscale-api"
}
```

### Submit Upscaling Job

**POST** `/upscale`

Submit a video upscaling job.

**Request Body:**
```json
{
  "input_path": "/path/to/input/video.mp4",
  "output_path": "/path/to/output/video.mp4"
}
```

**Response:**
```json
{
  "job_id": 123,
  "status": "processing"
}
```

**Status Codes:**
- 202: Job accepted for processing
- 400: Invalid request (missing parameters)
- 404: Input file not found
- 500: Server error

### Check Job Status

**GET** `/job/<job_id>`

Check the status of an upscaling job.

**Response:**
```json
{
  "job_id": 123,
  "status": "completed",
  "start_time": 1640995200.0,
  "end_time": 1640995500.0,
  "duration": 300.0
}
```

**Possible Status Values:**
- `processing`: Job is currently being processed
- `completed`: Job finished successfully
- `failed`: Job failed during processing

**Status Codes:**
- 200: Job status retrieved
- 404: Job not found

## Example Usage

### Submit a Job

```bash
curl -X POST http://localhost:5000/upscale \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "/videos/input.mp4",
    "output_path": "/videos/output.mp4"
  }'
```

### Check Job Status

```bash
curl http://localhost:5000/job/1
```