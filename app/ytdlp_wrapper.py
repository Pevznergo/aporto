from yt_dlp import YoutubeDL
from typing import Tuple, List, Any
import os
import subprocess


def _convert_to_mp4(input_path: str, output_path: str) -> None:
    """Convert video to MP4 format using ffmpeg"""
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file
        '-i', input_path,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-strict', 'experimental',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to convert video to MP4: {result.stderr}")


def download_video(url: str, output_dir: str) -> Tuple[str, str, str]:
    """
    Downloads the video and returns (video_id, original_title, file_path)
    file_path is absolute.
    """
    os.makedirs(output_dir, exist_ok=True)
    # Use more flexible format selection
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
        # Flexible format selection - prioritize high quality
        "format": "bestvideo[height>=720]+bestaudio/best[height>=720]/best",
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info: Any = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check video quality
            height = info.get('height', 0)
            if height < 720:
                raise RuntimeError(f"Video quality is too low: {height}p. Minimum required is 720p.")
            
            # Convert to MP4 if needed
            ext = os.path.splitext(filename)[1].lower()
            if ext != '.mp4':
                mp4_filename = os.path.splitext(filename)[0] + '.mp4'
                _convert_to_mp4(filename, mp4_filename)
                # Remove original file
                os.remove(filename)
                filename = mp4_filename
                
    except Exception as e:
        # Provide detailed error with available formats
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
            
    video_id = info.get("id", "") or ""
    file_path = os.path.abspath(filename)
    original_title = info.get("title", "") or ""
    return video_id, original_title, file_path


def download_video_simple(url: str, output_dir: str) -> Tuple[str, str, str]:
    """
    Downloads the video in high quality (720p or higher) and saves filename as the video title.
    Prioritizes 1080p but will accept 720p if 1080p is unavailable.
    Returns (video_id, original_title, file_path).
    """
    os.makedirs(output_dir, exist_ok=True)
    # Use more flexible format selection
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
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
        # Flexible format selection - prioritize high quality
        "format": "bestvideo[height>=720]+bestaudio/best[height>=720]/best",
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info: Any = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Check video quality
            height = info.get('height', 0)
            if height < 720:
                raise RuntimeError(f"Video quality is too low: {height}p. Minimum required is 720p.")
            
            # Convert to MP4 if needed
            ext = os.path.splitext(filename)[1].lower()
            if ext != '.mp4':
                mp4_filename = os.path.splitext(filename)[0] + '.mp4'
                _convert_to_mp4(filename, mp4_filename)
                # Remove original file
                os.remove(filename)
                filename = mp4_filename
                
    except Exception as e:
        # Provide detailed error with available formats
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
            
    video_id = info.get("id", "") or ""
    file_path = os.path.abspath(filename)
    original_title = info.get("title", "") or ""
    return video_id, original_title, file_path