#!/usr/bin/env python3
"""
Test script to check current queue settings
"""
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print('=== QUEUE SETTINGS TEST ===')

try:
    from app.worker import get_upload_concurrency, get_result_download_concurrency
    print(f'✅ Upload concurrency: {get_upload_concurrency()}')
    print(f'✅ Download concurrency: {get_result_download_concurrency()}')
except Exception as e:
    print(f'❌ Error importing worker functions: {e}')

try:
    from app.upscale_config import get_upscale_concurrency, get_upscale_settings
    print(f'✅ GPU processing concurrency: {get_upscale_concurrency()}')
    settings = get_upscale_settings()
    print(f'✅ Upscale settings: {settings}')
except Exception as e:
    print(f'❌ Error importing upscale config: {e}')

print('\n=== ENVIRONMENT VARIABLES ===')
env_vars = [
    'UPSCALE_UPLOAD_CONCURRENCY', 
    'UPSCALE_CONCURRENCY', 
    'UPSCALE_RESULT_DOWNLOAD_CONCURRENCY'
]
for key in env_vars:
    value = os.getenv(key, 'NOT SET')
    print(f'{key}: {value}')

print('\n=== EXPECTED BEHAVIOR ===')
print('Upload queue: 1 concurrent (controlled by _upload_sem)')
print('GPU processing: 2 concurrent (controlled by _active_upscale counter)')  
print('Download queue: 1 concurrent (controlled by _result_dl_sem)')
print()
print('If you see more than 2 GPU jobs processing simultaneously,')
print('check if UPSCALE_CONCURRENCY=2 is set correctly.')