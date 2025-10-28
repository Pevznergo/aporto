#!/usr/bin/env python3
"""
Script to check available video qualities for a YouTube URL
"""

import sys
from yt_dlp import YoutubeDL
from typing import Any, List, Dict

def check_video_qualities(url: str) -> bool:
    """Check available video qualities for a YouTube URL"""
    # Options for getting format information
    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "simulate": True,  # Don't download, just fetch info
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info: Any = ydl.extract_info(url, download=False)
            
            # Get available formats
            formats: List[Dict[str, Any]] = info.get('formats', []) or []
            
            print(f"Video Title: {info.get('title', 'Unknown')}")
            print(f"Video ID: {info.get('id', 'Unknown')}")
            print("\nAvailable Formats:")
            print("-" * 80)
            
            # Sort formats by height (quality) in descending order
            formats_sorted = sorted(formats, key=lambda x: x.get('height', 0) or 0, reverse=True)
            
            # Track unique heights
            seen_heights = set()
            available_formats = []
            
            for f in formats_sorted:
                height = f.get('height')
                width = f.get('width')
                ext = f.get('ext', 'unknown')
                format_id = f.get('format_id', 'unknown')
                fps = f.get('fps', 'unknown')
                
                # Skip if height is None or already seen
                if height is None:
                    continue
                    
                if height not in seen_heights:
                    seen_heights.add(height)
                    available_formats.append({
                        'height': height,
                        'width': width,
                        'ext': ext,
                        'format_id': format_id,
                        'fps': fps
                    })
            
            # Print unique heights with details
            for fmt in available_formats:
                print(f"{fmt['height']:4d}p | {fmt['width'] or 0:4d}x{fmt['height']:4d} | {fmt['ext']:3s} | {fmt['fps'] or 0:2}fps | Format ID: {fmt['format_id']}")
            
            # Print just the heights as a list
            heights = sorted(list(seen_heights), reverse=True)
            print(f"\nAvailable heights: {heights}")
            
            # Check for our target qualities
            target_qualities = [1080, 720, 480, 360]
            print("\nTarget Qualities Check:")
            for quality in target_qualities:
                status = "✓ Available" if quality in seen_heights else "✗ Not available"
                print(f"  {quality:4d}p: {status}")
                
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_video_quality.py <youtube_url>")
        print("Example: python check_video_quality.py https://www.youtube.com/watch?v=kYqPMh-0bIw")
        sys.exit(1)
    
    url = sys.argv[1]
    check_video_qualities(url)