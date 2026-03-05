"""
Ultra-fast video downloader module with tweet caption extraction

This module handles:
- Validating Twitter/X URLs
- Extracting direct video URLs (lightning fast, no download)
- Extracting tweet text/caption
- Streaming videos directly to Telegram (no local storage)
- Optimized for serverless (Vercel-readyy)
"""

import re
import io
import requests
import yt_dlp
from concurrent.futures import ThreadPoolExecutor


def is_valid_twitter_url(url):
    """
    Validates if the provided URL is a valid Twitter/X video link.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if valid Twitter/X URL, False otherwise
    """
    # Pattern to match Twitter/X URLs with status
    twitter_patterns = [
        r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
        r'https?://(?:www\.)?x\.com/\w+/status/\d+'
    ]
    
    for pattern in twitter_patterns:
        if re.match(pattern, url):
            return True
    return False


def get_video_info(url):
    """
    Extracts video information, direct URL, and tweet caption (ULTRA-FAST - no download).
    
    Args:
        url (str): The Twitter/X URL to extract from
        
    Returns:
        dict: Video info including direct URL, title, caption, thumbnail, duration
        
    Raises:
        Exception: If extraction fails or no video found
    """
    # Configure yt-dlp for ultra-fast info extraction
    ydl_opts = {
        'format': 'best',  # Get best quality URL
        'quiet': True,  # Suppress output
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,  # Don't download, just get info
        'socket_timeout': 10,  # Faster timeout
        'no_check_certificate': True,  # Skip cert validation for speed
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video information (fast, no download)
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise Exception("Could not extract video information")
            
            # Get direct video URL
            video_url = info.get('url')
            if not video_url:
                raise Exception("No video URL found in the tweet")
            
            # Extract tweet caption/text (the tweet's actual text content)
            caption = info.get('description', '') or info.get('title', '')
            
            # Clean up caption - remove URL at the end if present
            if caption:
                caption = caption.split('https://t.co/')[0].strip()
                caption = caption.split('pic.twitter.com/')[0].strip()
            
            # Get uploader/author info
            uploader = info.get('uploader', '') or info.get('channel', '')
            
            return {
                'url': video_url,
                'title': info.get('title', 'twitter_video'),
                'caption': caption,  # The actual tweet text
                'uploader': uploader,
                'ext': info.get('ext', 'mp4'),
                'filesize': info.get('filesize', 0),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail'),
            }
                
    except yt_dlp.utils.DownloadError as e:
        raise Exception(f"Extraction error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


def stream_video(video_url, chunk_size=8192):
    """
    Streams video from direct URL into memory (no disk storage needed).
    
    Args:
        video_url (str): Direct URL to the video file
        chunk_size (int): Size of chunks to stream (default 8KB)
        
    Returns:
        io.BytesIO: Video data in memory buffer
        
    Raises:
        Exception: If streaming fails
    """
    try:
        # Stream video with progress
        response = requests.get(video_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Create in-memory buffer
        video_buffer = io.BytesIO()
        
        # Stream video in chunks (memory efficient)
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                video_buffer.write(chunk)
        
        # Reset buffer position to beginning
        video_buffer.seek(0)
        
        return video_buffer
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Streaming error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected streaming error: {str(e)}")
