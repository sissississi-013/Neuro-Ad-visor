"""
Content ingestion and preprocessing.

Handles downloading social media content from URLs, converting images to
short videos (for TRIBE v2 compatibility), and saving uploaded files.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_VIDEO_EXT = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
SUPPORTED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SUPPORTED_AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg"}


def save_upload(data: bytes, filename: str) -> Path:
    """Persist an uploaded file and return its path."""
    uid = uuid.uuid4().hex[:8]
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower()
    dest = UPLOAD_DIR / f"{stem}_{uid}{ext}"
    dest.write_bytes(data)
    log.info("Saved upload: %s (%d bytes)", dest, len(data))
    return dest


def download_from_url(url: str) -> Path:
    """Download a social media post/video from a URL using yt-dlp."""
    uid = uuid.uuid4().hex[:8]
    output_path = UPLOAD_DIR / f"download_{uid}.mp4"

    try:
        subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "--format", "best[ext=mp4]/best",
                "--output", str(output_path),
                url,
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        log.info("Downloaded from URL: %s -> %s", url, output_path)
        return output_path
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        log.warning("yt-dlp failed (%s), trying httpx fallback", exc)
        return _http_download(url)


def _http_download(url: str) -> Path:
    """Simple HTTP download fallback for direct image/video URLs."""
    import httpx

    uid = uuid.uuid4().hex[:8]
    resp = httpx.get(url, follow_redirects=True, timeout=60)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "video" in content_type:
        ext = ".mp4"
    elif "png" in content_type:
        ext = ".png"
    elif "gif" in content_type:
        ext = ".gif"
    elif "webp" in content_type:
        ext = ".webp"
    else:
        ext = ".jpg"

    dest = UPLOAD_DIR / f"download_{uid}{ext}"
    dest.write_bytes(resp.content)
    log.info("HTTP downloaded: %s -> %s", url, dest)
    return dest


def classify_content(path: Path) -> str:
    """Return 'video', 'image', 'audio', or 'unknown'."""
    ext = path.suffix.lower()
    if ext in SUPPORTED_VIDEO_EXT:
        return "video"
    if ext in SUPPORTED_IMAGE_EXT:
        return "image"
    if ext in SUPPORTED_AUDIO_EXT:
        return "audio"
    return "unknown"


def image_to_video(image_path: Path, duration: float = 3.0) -> Path:
    """Convert a static image to a short video for TRIBE v2 processing.

    Creates a simple static-frame video. TRIBE v2 expects video input;
    for images we present them as a brief stimulus.
    """
    # Convert webp/gif to png first (ffmpeg handles png more reliably)
    input_path = image_path
    if image_path.suffix.lower() in {".webp", ".gif"}:
        try:
            from PIL import Image as PILImage
            png_path = image_path.with_suffix(".png")
            PILImage.open(image_path).convert("RGB").save(png_path)
            input_path = png_path
            log.info("Converted %s to PNG for ffmpeg", image_path.suffix)
        except Exception:
            pass

    output = image_path.with_suffix(".mp4")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(input_path),
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                str(output),
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
        log.info("Converted image to video: %s -> %s", image_path, output)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        log.warning("ffmpeg conversion failed (%s) -- returning image path as-is", type(e).__name__)
        return image_path
    return output


def prepare_for_tribe(path: Path) -> Path:
    """Ensure content is in a format TRIBE v2 can process (video or audio)."""
    content_type = classify_content(path)
    if content_type == "video":
        return path
    if content_type == "image":
        return image_to_video(path)
    if content_type == "audio":
        return path
    log.warning("Unknown content type for %s, returning as-is", path)
    return path
