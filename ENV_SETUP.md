# Environment Variables Setup Guide

This document describes how to configure environment variables for the Video Cutter Task Manager.

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Load variables into your shell:**
   ```bash
   source load_env.sh
   ```

3. **Check current configuration:**
   ```bash
   ./check_env.sh
   ```

## Environment Files

### `.env.example`
Template file with all available environment variables and their default values. Safe to commit to version control.

### `.env`
Your actual configuration file with real values. **Never commit this file to version control** as it contains sensitive information like API keys.

## Scripts

### `load_env.sh`
Loads all environment variables from `.env` file into your current shell session.

**Usage:**
```bash
source load_env.sh
```

**Features:**
- Counts and displays loaded variables
- Masks sensitive values (API keys, passwords, URLs)
- Shows detailed status for each variable
- Provides helpful tips

### `check_env.sh`
Checks which environment variables are currently set in your shell.

**Usage:**
```bash
./check_env.sh
```

**Features:**
- Categorizes variables by purpose
- Shows count of set/missing variables per category
- Provides overall configuration status
- Masks sensitive information

## Variable Categories

### 🔑 Core Variables
- `OPENAI_API_KEY` - Required for GPT processing
- `POSTGRES_URL` - Database connection string  
- `HUGGINGFACE_TOKEN` - For AI model downloads

### 🤖 AI Models
- `OPENAI_MODEL` - GPT model to use (default: gpt-4o-mini)
- `WHISPER_MODEL` - Speech recognition model (default: small)

### 🌐 Server Configuration
- `CORS_ORIGINS` - Allowed frontend origins

### 🖥️ VAST.AI Configuration
- `VAST_API_KEY` - VAST.AI API access key
- `VAST_INSTANCE_ID` - Specific GPU instance ID
- `VAST_SSH_*` - SSH connection details for GPU server

### 🎬 GPU Processing
- `CUT_ON_GPU` - Enable GPU-based video processing
- `VAST_UPSCALE_URL` - Direct URL to GPU upscaling service
- `GPU_SSH_*` - Alternative SSH configuration

### 📈 Upscale Configuration
- `UPSCALE_CONCURRENCY` - Parallel upscale jobs
- `UPSCALE_MODEL_NAME` - AI upscaling model to use
- Various upscale quality settings

### 📂 Model Paths
- Paths to AI model files on the system
- Cache directories for models

### ⚙️ Cut Configuration
- CUDA requirements and device settings
- Base directories for processing

## Security Notes

1. **Never commit `.env` files** - Add `.env` to your `.gitignore`
2. **Rotate API keys regularly** - Especially if they might be compromised
3. **Use environment-specific configurations** - Different settings for dev/prod
4. **Limit access** - Only share API keys with authorized team members

## Troubleshooting

### Variables not loading
```bash
# Check if .env file exists and is readable
ls -la .env

# Verify file format (no spaces around =)
cat .env | head -5

# Load with verbose output
bash -x load_env.sh
```

### Missing variables
```bash
# See what's missing
./check_env.sh

# Compare with example
diff .env.example .env
```

### Permission issues
```bash
# Make scripts executable
chmod +x load_env.sh check_env.sh

# Fix file permissions
chmod 600 .env  # Restrict access to owner only
```

## Examples

### Basic setup for local development
```bash
# Copy and edit configuration
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY and POSTGRES_URL

# Load and verify
source load_env.sh
./check_env.sh
```

### Production server setup
```bash
# Use production values
cp .env.production .env  # Your production config

# Load environment
source load_env.sh

# Verify critical variables are set
./check_env.sh | grep -E "(CORE|SERVER)"
```

## Integration with Other Tools

### With Docker
```bash
# Load env vars before running docker
source load_env.sh
docker-compose up
```

### With Python scripts
```bash
# Environment loaded automatically by python-dotenv
source load_env.sh  # Optional for shell access
python app/main.py
```

### With shell scripts
```bash
#!/bin/bash
source load_env.sh
# Your script can now use $OPENAI_API_KEY etc.
```