# Dockerfile for Video Upscaling Application
FROM nvidia/cuda:12.2.2-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    wget \
    ffmpeg \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3 as default
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x run_upscale.sh
RUN chmod +x start_server.sh

# Expose port for API server
EXPOSE 5000

# Default command - start API server
CMD ["./start_server.sh"]