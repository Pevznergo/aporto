from yt_dlp import YoutubeDL
from typing import Tuple, List, Any
import os


def download_video(url: str, output_dir: str) -> Tuple[str, str, str]:
    """
    Downloads the video and returns (video_id, original_title, file_path)
    file_path is absolute.
    """
    os.makedirs(output_dir, exist_ok=True)
    # Try to get exactly 1080p quality first, then fall back to 720p
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
        # Try to get exactly 1080p quality first
        "format": "bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=1080]+bestaudio/best[height=1080]",
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info: Any = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check if the downloaded video is exactly 1080p
            height = info.get('height', 0)
            if height != 1080:
                # If not 1080p, try 720p
                if height >= 720:
                    # Accept 720p or higher
                    pass
                else:
                    raise RuntimeError(f"Video quality is too low: {height}p. Minimum required is 720p.")
    except Exception as e:
        # If 1080p fails, try 720p
        if "requested format not available" in str(e).lower() or "no such format" in str(e).lower():
            try:
                ydl_opts["format"] = "bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=720]+bestaudio/best[height=720]"
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    # Check if the downloaded video is at least 720p
                    height = info.get('height', 0)
                    if height < 720:
                        raise RuntimeError(f"Video quality is too low: {height}p. Minimum required is 720p.")
            except Exception as e2:
                # If both fail, provide detailed error with available formats
                try:
                    # Get available formats for error message
                    info_opts = ydl_opts.copy()
                    info_opts["simulate"] = True
                    info_opts["format"] = "best"
                    with YoutubeDL(info_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        formats = info.get('formats', [])
                        available_heights = []
                        for f in formats:
                            h = f.get('height')
                            if h:
                                available_heights.append(h)
                        available_heights = sorted(list(set(available_heights)), reverse=True)
                    raise RuntimeError(f"Could not download acceptable quality. Available heights: {available_heights}")
                except Exception:
                    raise RuntimeError("Could not download acceptable quality (minimum 720p required)")
        else:
            raise
    video_id = info.get("id", "") or ""
    file_path = os.path.abspath(filename)
    original_title = info.get("title", "") or ""
    return video_id, original_title, file_path


def download_video_simple(url: str, output_dir: str) -> Tuple[str, str, str]:
    """
    Downloads the video in high quality (720p-1080p) and saves filename as the video title.
    Prioritizes 1080p but will accept 720p if 1080p is unavailable.
    Returns (video_id, original_title, file_path).
    """
    os.makedirs(output_dir, exist_ok=True)
    # Try to get exactly 1080p quality first, then fall back to 720p
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        # Prefer MP4 container for compatibility when merging
        "merge_output_format": "mp4",
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
        # Try to get exactly 1080p quality first
        "format": "bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=1080]+bestaudio/best[height=1080]",
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info: Any = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check if the downloaded video is exactly 1080p
            height = info.get('height', 0)
            if height != 1080:
                # If not 1080p, try 720p
                if height >= 720:
                    # Accept 720p or higher
                    pass
                else:
                    raise RuntimeError(f"Video quality is too low: {height}p. Minimum required is 720p.")
    except Exception as e:
        # If 1080p fails, try 720p
        if "requested format not available" in str(e).lower() or "no such format" in str(e).lower():
            try:
                ydl_opts["format"] = "bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=720]+bestaudio/best[height=720]"
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    # Check if the downloaded video is at least 720p
                    height = info.get('height', 0)
                    if height < 720:
                        raise RuntimeError(f"Video quality is too low: {height}p. Minimum required is 720p.")
            except Exception as e2:
                # If both fail, provide detailed error with available formats
                try:
                    # Get available formats for error message
                    info_opts = ydl_opts.copy()
                    info_opts["simulate"] = True
                    info_opts["format"] = "best"
                    with YoutubeDL(info_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        formats = info.get('formats', [])
                        available_heights = []
                        for f in formats:
                            h = f.get('height')
                            if h:
                                available_heights.append(h)
                        available_heights = sorted(list(set(available_heights)), reverse=True)
                    raise RuntimeError(f"Could not download acceptable quality. Available heights: {available_heights}")
                except Exception:
                    raise RuntimeError("Could not download acceptable quality (minimum 720p required)")
        else:
            raise
    video_id = info.get("id", "") or ""
    file_path = os.path.abspath(filename)
    original_title = info.get("title", "") or ""
    return video_id, original_title, file_path