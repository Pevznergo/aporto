#!/usr/bin/env python3
"""
Cleanup Old Configuration Files
Удаляет устаревшие JSON файлы конфигурации, которые больше не используются
"""

import os
from pathlib import Path

def cleanup_old_config():
    """Удаляет старые файлы конфигурации"""
    
    print("=== Old Configuration Cleanup ===\n")
    
    # Файлы для удаления
    files_to_remove = [
        "upscale_settings.json",
        "upscale_instance.json"  # если есть кэш VAST instance
    ]
    
    removed_files = []
    missing_files = []
    
    for filename in files_to_remove:
        filepath = Path(filename)
        
        if filepath.exists():
            try:
                # Показываем содержимое перед удалением
                if filepath.suffix == '.json':
                    try:
                        import json
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        print(f"📄 Contents of {filename}:")
                        for key, value in data.items():
                            print(f"   {key}: {value}")
                        print()
                    except Exception:
                        print(f"📄 {filename} exists but couldn't read content")
                
                # Создаем backup перед удалением
                backup_name = f"{filename}.backup"
                filepath.rename(backup_name)
                print(f"✓ Moved {filename} → {backup_name}")
                removed_files.append(filename)
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
        else:
            missing_files.append(filename)
    
    if removed_files:
        print(f"\n✓ Cleaned up {len(removed_files)} old config files:")
        for filename in removed_files:
            print(f"  - {filename}")
        print("\nBackup files created with .backup extension.")
        print("You can safely delete them after verifying everything works.")
    
    if missing_files:
        print(f"\n○ {len(missing_files)} files were already missing (good):")
        for filename in missing_files:
            print(f"  - {filename}")
    
    print(f"\n=== Summary ===")
    print("✓ Configuration is now managed entirely via .env file")
    print("✓ No more JSON configuration files")
    print("✓ Settings are applied immediately when application starts")
    
    return len(removed_files) > 0

if __name__ == "__main__":
    cleanup_old_config()