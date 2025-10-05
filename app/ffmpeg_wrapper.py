import subprocess
import os
from typing import Optional


def timemark(seconds: Optional[float]) -> Optional[str]:
    if seconds is None:
        return None
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def process_video(input_path: str, output_dir: str, start: Optional[float], end: Optional[float]) -> str:
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base}_cut.mp4")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", input_path]
    if start is not None:
        cmd.extend(["-ss", timemark(start)])
    if end is not None:
        cmd.extend(["-to", timemark(end)])

    if start is not None or end is not None:
        cmd.extend(["-c:v", "libx264", "-c:a", "aac"])
    else:
        cmd.extend(["-c", "copy"])

    cmd.append(output_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg failed")
    return os.path.abspath(output_path)
