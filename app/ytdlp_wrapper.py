from yt_dlp import YoutubeDL
from typing import Tuple, List, Any
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
    
    try:
        # First, get info about available formats without downloading
        info_opts = ydl_opts.copy()
        info_opts["simulate"] = True
        with YoutubeDL(info_opts) as ydl:
            info: Any = ydl.extract_info(url, download=False)
            
            # Check available formats
            formats: List[Any] = info.get('formats', [])
            available_heights = []
            for f in formats:
                height = f.get('height')
                if height:
                    available_heights.append(height)
            
            # Remove duplicates and sort
            available_heights = sorted(list(set(available_heights)), reverse=True)
            
            # Check if 1080p is available
            if 1080 not in available_heights:
                raise RuntimeError(f"1080p quality is not available for this video. Available heights: {available_heights}")
        
        # Now download with exactly 1080p format
        ydl_opts["format"] = "bestvideo[height=1080]+bestaudio/best[height=1080]"
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check if the downloaded video is exactly 1080p
            height = info.get('height', 0)
            if height != 1080:
                raise RuntimeError(f"Video quality is not 1080p: {height}p. Only 1080p videos are allowed.")
    except Exception as e:
        # Map any format-not-found cases to a clear error
        msg = str(e)
        if "requested format not available" in msg.lower() or "no such format" in msg.lower():
            # Try to get info about available formats
            try:
                info_opts = ydl_opts.copy()
                info_opts["simulate"] = True
                with YoutubeDL(info_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = info.get('formats', [])
                    available_heights = []
                    for f in formats:
                        height = f.get('height')
                        if height:
                            available_heights.append(height)
                    available_heights = sorted(list(set(available_heights)), reverse=True)
                raise RuntimeError(f"1080p quality is not available for this video. Available heights: {available_heights}")
            except Exception:
                raise RuntimeError("1080p quality is not available for this video")
        raise
    video_id = info.get("id", "") or ""
    file_path = os.path.abspath(filename)
    original_title = info.get("title", "") or ""
    return video_id, original_title, file_path


def download_video_simple(url: str, output_dir: str) -> Tuple[str, str, str]:
    """
    Downloads the video in exactly 1080p quality and saves filename as the video title.
    Returns (video_id, original_title, file_path).
    """
    os.makedirs(output_dir, exist_ok=True)
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
    }
    
    try:
        # First, get info about available formats without downloading
        info_opts = ydl_opts.copy()
        info_opts["simulate"] = True
        with YoutubeDL(info_opts) as ydl:
            info: Any = ydl.extract_info(url, download=False)
            
            # Check available formats
            formats: List[Any] = info.get('formats', [])
            available_heights = []
            for f in formats:
                height = f.get('height')
                if height:
                    available_heights.append(height)
            
            # Remove duplicates and sort
            available_heights = sorted(list(set(available_heights)), reverse=True)
            
            # Check if 1080p is available
            if 1080 not in available_heights:
                raise RuntimeError(f"1080p quality is not available for this video. Available heights: {available_heights}")
        
        # Now download with exactly 1080p format
        ydl_opts["format"] = "bestvideo[height=1080]+bestaudio/best[height=1080]"
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check if the downloaded video is exactly 1080p
            height = info.get('height', 0)
            if height != 1080:
                raise RuntimeError(f"Video quality is not 1080p: {height}p. Only 1080p videos are allowed.")
    except Exception as e:
        # Map any format-not-found cases to a clear error
        msg = str(e)
        if "requested format not available" in msg.lower() or "no such format" in msg.lower():
            # Try to get info about available formats
            try:
                info_opts = ydl_opts.copy()
                info_opts["simulate"] = True
                with YoutubeDL(info_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = info.get('formats', [])
                    available_heights = []
                    for f in formats:
                        height = f.get('height')
                        if height:
                            available_heights.append(height)
                    available_heights = sorted(list(set(available_heights)), reverse=True)
                raise RuntimeError(f"1080p quality is not available for this video. Available heights: {available_heights}")
            except Exception:
                raise RuntimeError("1080p quality is not available for this video")
        raise
    video_id = info.get("id", "") or ""
    file_path = os.path.abspath(filename)
    original_title = info.get("title", "") or ""
    return video_id, original_title, file_path