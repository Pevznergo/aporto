from yt_dlp import YoutubeDL
from typing import Tuple
import os


def download_video(url: str, output_dir: str) -> Tuple[str, str, str]:
    """
    Downloads the video and returns (video_id, original_title, file_path)
    file_path is absolute.
    """
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        # Add headers to avoid 403 errors
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        # Additional options to bypass restrictions
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "nocheckcertificate": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    video_id = info.get("id")
    file_path = os.path.abspath(filename)
    original_title = info.get("title")
    return video_id, original_title, file_path


def download_video_simple(url: str, output_dir: str) -> Tuple[str, str, str]:
    """
    Downloads the video in 1080p (Full HD) only and saves filename as the video title.
    If 1080p is unavailable, raises a clear error.
    Returns (video_id, original_title, file_path).
    """
    os.makedirs(output_dir, exist_ok=True)
    # Enforce 1080p: try bestvideo[height=1080]+bestaudio or single best[height=1080]
    # If no match, yt-dlp will raise an error which we convert to a friendly message.
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        # Prefer MP4 container for compatibility when merging
        "merge_output_format": "mp4",
        # Strictly select 1080p
        "format": "bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/best[height=1080]",
        # Add headers to avoid 403 errors
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        # Additional options to bypass restrictions
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "nocheckcertificate": True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as e:
        # Map any format-not-found cases to a clear 1080p error
        msg = str(e)
        if "requested format not available" in msg.lower() or "no such format" in msg.lower():
            raise RuntimeError("Недоступно качество 1080p для этого видео")
        raise
    video_id = info.get("id")
    file_path = os.path.abspath(filename)
    original_title = info.get("title")
    return video_id, original_title, file_path
