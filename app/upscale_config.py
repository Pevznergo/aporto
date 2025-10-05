import os
import json
from typing import Dict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SETTINGS_PATH = os.path.join(BASE_DIR, "upscale_settings.json")

DEFAULTS = {
    "UPSCALE_IMAGE": os.getenv("UPSCALE_IMAGE", "your-dockerhub-username/video-upscale-app:latest"),
    "UPSCALE_CONCURRENCY": int(os.getenv("UPSCALE_CONCURRENCY", "2")),
    # Optional: if you already have a Vast instance, set its ID here to reuse
    "VAST_INSTANCE_ID": os.getenv("VAST_INSTANCE_ID", ""),
}

def get_upscale_settings() -> Dict:
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULTS, **data}
    except Exception:
        pass
    return DEFAULTS.copy()


def save_upscale_settings(new_settings: Dict) -> Dict:
    current = get_upscale_settings()
    current.update({
        "UPSCALE_IMAGE": new_settings.get("UPSCALE_IMAGE", current["UPSCALE_IMAGE"]),
        "UPSCALE_CONCURRENCY": int(new_settings.get("UPSCALE_CONCURRENCY", current["UPSCALE_CONCURRENCY"])),
        "VAST_INSTANCE_ID": new_settings.get("VAST_INSTANCE_ID", current.get("VAST_INSTANCE_ID", ""))
    })
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return current


def get_upscale_concurrency() -> int:
    s = get_upscale_settings()
    try:
        return max(1, int(s.get("UPSCALE_CONCURRENCY", 2)))
    except Exception:
        return 2
