#!/usr/bin/env python3
"""
Environment Variables Checker
Проверяет и диагностирует состояние переменных окружения для aporto приложения
"""

import os
import json
from pathlib import Path

# Попытка загрузить dotenv
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

def load_env_file():
    """Загружает переменные из .env файла если доступен dotenv"""
    if DOTENV_AVAILABLE:
        load_dotenv()
        return True
    return False

def check_env_variables():
    """Проверяет все ключевые переменные окружения"""
    
    print("=== Environment Variables Checker ===\n")
    
    # Загружаем .env если возможно
    if load_env_file():
        print("✓ python-dotenv loaded successfully")
    else:
        print("⚠ python-dotenv not available, checking system env only")
    
    print()
    
    # Основные переменные для проверки
    variables = {
        "OpenAI Configuration": {
            "OPENAI_API_KEY": {"required": True, "mask": True},
            "OPENAI_MODEL": {"required": False, "default": "gpt-4o-mini"},
        },
        "Whisper Configuration": {
            "WHISPER_MODEL": {"required": False, "default": "small"},
        },
        "CORS Configuration": {
            "CORS_ORIGINS": {"required": False, "default": "http://localhost:3000,http://127.0.0.1:3000"},
        },
        "VAST.ai Configuration": {
            "VAST_API_KEY": {"required": True, "mask": True},
            "VAST_API_BASE": {"required": False, "default": "https://console.vast.ai/api/v0"},
            "VAST_INSTANCE_ID": {"required": True},
            "VAST_SSH_KEY": {"required": True},
            "VAST_SSH_HOST": {"required": True},
            "VAST_SSH_PORT": {"required": True},
            "VAST_SSH_USER": {"required": False, "default": "root"},
            "VAST_REMOTE_INBOX": {"required": True},
            "VAST_REMOTE_OUTBOX": {"required": True},
            "VAST_UPSCALE_URL": {"required": False},
            "VAST_DISABLE_ENSURE": {"required": False},
            "VAST_DISABLE_AUTO_STOP": {"required": False},
        },
        "Upscale Configuration": {
            "UPSCALE_UPLOAD_CONCURRENCY": {"required": False, "default": "1"},
            "UPSCALE_CONCURRENCY": {"required": False, "default": "2"},
            "UPSCALE_RESULT_DOWNLOAD_CONCURRENCY": {"required": False, "default": "1"},
            "UPSCALE_MODEL_NAME": {"required": False, "default": "realesr-general-x4v3"},
            "UPSCALE_DENOISE_STRENGTH": {"required": False, "default": "0.5"},
            "UPSCALE_FACE_ENHANCE": {"required": False, "default": "1"},
            "UPSCALE_OUTSCALE": {"required": False, "default": "4"},
        }
    }
    
    total_vars = 0
    missing_required = []
    
    for category, vars_dict in variables.items():
        print(f"--- {category} ---")
        
        for var_name, config in vars_dict.items():
            total_vars += 1
            value = os.getenv(var_name)
            is_required = config.get("required", False)
            default_val = config.get("default", None)
            mask = config.get("mask", False)
            
            if value:
                if mask:
                    display_value = f"{'*' * (len(value) - 8)}{value[-8:]}" if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"  ✓ {var_name} = {display_value}")
            elif default_val:
                print(f"  ○ {var_name} = {default_val} (default)")
            elif is_required:
                print(f"  ❌ {var_name} = NOT SET (REQUIRED)")
                missing_required.append(var_name)
            else:
                print(f"  - {var_name} = NOT SET (optional)")
        
        print()
    
    # Note: upscale_settings.json is no longer used - all config comes from .env
    upscale_settings_path = Path("upscale_settings.json")
    if upscale_settings_path.exists():
        print("--- ⚠ WARNING: Old Config File Found ---")
        print(f"  🗑️ upscale_settings.json exists but is no longer used")
        print(f"  💡 Run 'python cleanup_old_config.py' to remove it")
        print()
    
    # Резюме
    print("=== Summary ===")
    print(f"Total variables checked: {total_vars}")
    
    if missing_required:
        print(f"❌ Missing required variables: {len(missing_required)}")
        for var in missing_required:
            print(f"   - {var}")
    else:
        print("✓ All required variables are set")
    
    if DOTENV_AVAILABLE:
        print("✓ Environment loading works correctly")
    else:
        print("⚠ Install python-dotenv for automatic .env loading")
    
    return len(missing_required) == 0

if __name__ == "__main__":
    success = check_env_variables()
    exit(0 if success else 1)