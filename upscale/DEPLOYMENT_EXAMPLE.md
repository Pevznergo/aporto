# Deployment Example

This document shows a complete example of deploying the video upscaling application to Vast.ai.

## Prerequisites

1. Docker image built and pushed to a registry
2. Vast.ai API key
3. Instance configuration file

## Step-by-Step Deployment

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t your-dockerhub-username/video-upscale-app:latest .

# Push to Docker Hub
docker push your-dockerhub-username/video-upscale-app:latest
```

### 2. Prepare Instance Configuration

Create [vastai_instance_config.json](file:///Users/igortkachenko/Downloads/aporto/upscale/vastai_instance_config.json):

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

### 3. Deploy Using Python Script

```bash
# Create a new instance
python deploy_vastai.py --api-key YOUR_API_KEY --action create --config vastai_instance_config.json

# Output will include the instance ID
# {
#   "success": true,
#   "id": "123456"
# }
```

### 4. Wait for Instance to Start

```bash
# Wait for the instance to be running
python deploy_vastai.py --api-key YOUR_API_KEY --action wait --instance-id 123456
```

### 5. Get Instance Details

```bash
# Get instance details including IP address
python deploy_vastai.py --api-key YOUR_API_KEY --action details --instance-id 123456

# Look for the "ssh_host" field in the response for the IP address
```

### 6. Use the Deployed Application

Once the instance is running, you can use the REST API:

```bash
# Submit an upscaling job
curl -X POST "http://INSTANCE_IP:5000/upscale" \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "/videos/input.mp4",
    "output_path": "/videos/output.mp4"
  }'

# Check job status
curl "http://INSTANCE_IP:5000/job/1"
```

### 7. Manage the Instance

```bash
# Stop the instance (storage-only billing)
python deploy_vastai.py --api-key YOUR_API_KEY --action stop --instance-id 123456

# Start the instance again
python deploy_vastai.py --api-key YOUR_API_KEY --action start --instance-id 123456

# Destroy the instance (no further billing)
python deploy_vastai.py --api-key YOUR_API_KEY --action destroy --instance-id 123456
```

## Bash Script Automation

You can also create a bash script to automate the entire process:

```bash
#!/bin/bash
# automated_deploy.sh

# Configuration
API_KEY="your_api_key_here"
CONFIG_FILE="vastai_instance_config.json"

# Create instance
echo "Creating instance..."
CREATE_RESULT=$(python deploy_vastai.py --api-key $API_KEY --action create --config $CONFIG_FILE)
INSTANCE_ID=$(echo $CREATE_RESULT | jq -r '.id')

if [ "$INSTANCE_ID" == "null" ]; then
    echo "Failed to create instance"
    echo $CREATE_RESULT
    exit 1
fi

echo "Created instance: $INSTANCE_ID"

# Wait for instance to start
echo "Waiting for instance to start..."
python deploy_vastai.py --api-key $API_KEY --action wait --instance-id $INSTANCE_ID

# Get instance details
echo "Getting instance details..."
DETAILS=$(python deploy_vastai.py --api-key $API_KEY --action details --instance-id $INSTANCE_ID)
IP_ADDRESS=$(echo $DETAILS | jq -r '.ssh_host')

echo "Instance is ready!"
echo "IP Address: $IP_ADDRESS"
echo "API Endpoint: http://$IP_ADDRESS:5000"

echo "You can now use the API:"
echo "curl -X POST http://$IP_ADDRESS:5000/health"
```

## Cost Monitoring

Monitor your instance costs:

```bash
# Check your account balance
curl -X GET "https://console.vast.ai/api/v0/users/me/" \
  -H "Authorization: Bearer YOUR_API_KEY" | jq '.'
```

## Cleanup

When you're done with your instance:

```bash
# Destroy the instance to stop all billing
python deploy_vastai.py --api-key YOUR_API_KEY --action destroy --instance-id 123456
```