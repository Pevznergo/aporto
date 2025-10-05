# Consolidated

See README.md in this folder for Vast.ai API usage.

This guide explains how to use the Vast.ai API to deploy, manage, and control your video upscaling application.

## Prerequisites

1. A Vast.ai account with API key
2. Docker image pushed to a container registry
3. curl or another HTTP client for API requests

## Step-by-Step API Usage

### 1. Set Your API Key

```bash
export VAST_API_KEY=your_actual_api_key_here
```

### 2. Search for Available GPU Instances

Find L4 GPU instances suitable for your application:

```bash
curl -X GET "https://console.vast.ai/api/v0/bundles/?q=gpu_name:L4" \
  -H "Authorization: Bearer $VAST_API_KEY" | jq '.'
```

### 3. Create an Instance Template

Create a JSON file [vastai_instance_config.json](file:///Users/igortkachenko/Downloads/aporto/upscale/vastai_instance_config.json) with your instance configuration:

```json
{
  "client_id": "me",
  "image": "your-dockerhub-username/video-upscale-app:latest",
  "env": {
    "PORT": "5000"
  },
  "disk": 32.0,
  "onstart": "/start_server.sh",
  "runtype": "ssh_direc",
  "cuda_v": 11.8
}
```

### 4. Create and Start an Instance

```bash
# Create and start an instance
curl -X POST "https://console.vast.ai/api/v0/asks/" \
  -H "Authorization: Bearer $VAST_API_KEY" \
  -H "Content-Type: application/json" \
  -d @vastai_instance_config.json | jq '.'
```

This will return an instance ID that you'll use for future operations.

### 5. List Your Instances

```bash
# List all your instances
curl -X GET "https://console.vast.ai/api/v0/instances/" \
  -H "Authorization: Bearer $VAST_API_KEY" | jq '.'
```

### 6. Get Instance Details

```bash
# Get details for a specific instance
curl -X GET "https://console.vast.ai/api/v0/instances/{instance_id}/" \
  -H "Authorization: Bearer $VAST_API_KEY" | jq '.'
```

### 7. Stop an Instance

```bash
# Stop an instance (will be billed for storage only)
curl -X PUT "https://console.vast.ai/api/v0/instances/{instance_id}/" \
  -H "Authorization: Bearer $VAST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state": "stopped"}' | jq '.'
```

### 8. Start a Stopped Instance

```bash
# Start a stopped instance
curl -X PUT "https://console.vast.ai/api/v0/instances/{instance_id}/" \
  -H "Authorization: Bearer $VAST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state": "running"}' | jq '.'
```

### 9. Destroy an Instance

```bash
# Completely destroy an instance (no further billing)
curl -X DELETE "https://console.vast.ai/api/v0/instances/{instance_id}/" \
  -H "Authorization: Bearer $VAST_API_KEY" | jq '.'
```

## Using Your Deployed Application

Once your instance is running, you can access the API:

1. Get the instance IP and port from the instance details
2. Use the REST API endpoints:

### Submit an Upscaling Job

```bash
curl -X POST "http://INSTANCE_IP:5000/upscale" \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "/path/to/input.mp4",
    "output_path": "/path/to/output.mp4"
  }'
```

### Check Job Status

```bash
curl "http://INSTANCE_IP:5000/job/JOB_ID"
```

## Automation Script

Here's a bash script to automate the deployment process:

```bash
#!/bin/bash
# deploy_to_vastai.sh

# Set variables
VAST_API_KEY="your_api_key_here"
DOCKER_IMAGE="your-dockerhub-username/video-upscale-app:latest"

# Create instance configuration
cat > instance_config.json << EOF
{
  "client_id": "me",
  "image": "$DOCKER_IMAGE",
  "env": {
    "PORT": "5000"
  },
  "disk": 32.0,
  "onstart": "/start_server.sh",
  "runtype": "ssh_direc",
  "cuda_v": 11.8
}
EOF

# Create instance
echo "Creating instance..."
RESPONSE=$(curl -s -X POST "https://console.vast.ai/api/v0/asks/" \
  -H "Authorization: Bearer $VAST_API_KEY" \
  -H "Content-Type: application/json" \
  -d @instance_config.json)

echo "Response: $RESPONSE"

# Extract instance ID
INSTANCE_ID=$(echo $RESPONSE | jq -r '.id')
echo "Instance ID: $INSTANCE_ID"

# Wait for instance to be ready
echo "Waiting for instance to start..."
sleep 30

# Get instance details
curl -X GET "https://console.vast.ai/api/v0/instances/$INSTANCE_ID/" \
  -H "Authorization: Bearer $VAST_API_KEY" | jq '.'
```

## Cost Management

Monitor your instance costs:

```bash
# Get billing information
curl -X GET "https://console.vast.ai/api/v0/users/me/" \
  -H "Authorization: Bearer $VAST_API_KEY" | jq '.'
```

## Troubleshooting

### Common Issues

1. **Image not found**: Ensure your Docker image is public or you've provided credentials
2. **Instance fails to start**: Check the startup script and logs
3. **API authentication errors**: Verify your API key is correct
4. **Port not accessible**: Ensure your application binds to 0.0.0.0, not localhost

### Checking Logs

```bash
# Get instance logs
curl -X GET "https://console.vast.ai/api/v0/instances/{instance_id}/logs/" \
  -H "Authorization: Bearer $VAST_API_KEY" | jq '.'
```

## Security Considerations

1. Store your API key securely (use environment variables, not hardcoded)
2. Use HTTPS for all API communications
3. Implement authentication for your application API if needed
4. Regularly rotate your API keys