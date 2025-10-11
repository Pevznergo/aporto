import os
from typing import Dict

# Simple environment-only configuration
# No more JSON file dependencies - everything comes from .env

def get_upscale_settings() -> Dict:
    """Get upscale settings directly from environment variables"""
    return {
        "UPSCALE_IMAGE": os.getenv("UPSCALE_IMAGE", "your-dockerhub-username/video-upscale-app:latest"),
        "UPSCALE_CONCURRENCY": int(os.getenv("UPSCALE_CONCURRENCY", "2")),
        "VAST_INSTANCE_ID": os.getenv("VAST_INSTANCE_ID", ""),
    }


def save_upscale_settings(new_settings: Dict) -> Dict:
    """Save upscale settings - now just returns current env values
    
    Note: This function is kept for API compatibility but doesn't actually save.
    To change settings, modify the .env file and restart the application.
    """
    current = get_upscale_settings()
    # Return current settings from environment - no persistence to JSON
    return current


def get_upscale_concurrency() -> int:
    """Get upscale concurrency from environment variable"""
    try:
        return max(1, int(os.getenv("UPSCALE_CONCURRENCY", "2")))
    except (ValueError, TypeError):
        return 2
