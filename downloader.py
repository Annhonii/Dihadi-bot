import os
import shutil
import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import yt_dlp

from config import DOWNLOAD_DIR, MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)

SUPPORTED_DOMAINS = [
    "instagram.com",
    "instagr.am",
    "youtube.com",
    "youtu.be",
    "reddit.com",
    "redd.it",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "facebook.com",
    "fb.watch",
    "pinterest.com",
    "pin.it",
]


@dataclass
class DownloadResult:
    media_type: str  # 'video', 'photo', 'album', 'audio'
    file_paths: List[str] = field(default_factory=list)
    title: str = ""
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail_path: Optional[str] = None
    error: Optional[str] = None


def is_supported_url(url: str) -> bool:
    """Checks if the URL matches known supported media platforms."""
    lower_url = url.lower()
    return any(domain in lower_url for domain in SUPPORTED_DOMAINS)


def _sync_download(url: str, request_dir: Path) -> DownloadResult:
    """Synchronous media extraction and download worker executed in thread pool."""
    ydl_opts = {
        "outtmpl": str(request_dir / "%(id)s.%(ext)s"),
        "format": (
            f"bestvideo[filesize<{MAX_FILE_SIZE_BYTES - 5 * 1024 * 1024}]+bestaudio/"
            f"best[filesize<{MAX_FILE_SIZE_BYTES}]/best"
        ),
        "merge_output_format": "mp4",
        "writethumbnail": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "socket_timeout": 30,
        "ignoreerrors": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return DownloadResult(media_type="error", error="Media information fetch nahi ho payi.")

            title = info.get("title", "") or "Downloaded Media"
            duration = info.get("duration")
            width = info.get("width")
            height = info.get("height")

            # Check for multiple entries (playlist / carousel / album)
            entries = info.get("entries")
            downloaded_files: List[str] = []
            thumb_path: Optional[str] = None

            # Collect all downloaded media files in request_dir
            for f in sorted(request_dir.iterdir()):
                if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"] and not thumb_path:
                    thumb_path = str(f)
                elif f.suffix.lower() in [".mp4", ".mkv", ".webm", ".mov", ".avi"]:
                    downloaded_files.append(str(f))
                elif f.suffix.lower() in [".mp3", ".m4a", ".aac", ".ogg", ".opus"]:
                    downloaded_files.append(str(f))

            # If no videos found, check if only images were downloaded
            if not downloaded_files and thumb_path:
                downloaded_files.append(thumb_path)
                thumb_path = None

            if not downloaded_files:
                return DownloadResult(media_type="error", error="Media file download nahi ho payi.")

            # Check file size limits for Telegram
            for f_path in downloaded_files:
                file_size = os.path.getsize(f_path)
                if file_size > MAX_FILE_SIZE_BYTES:
                    size_mb = round(file_size / (1024 * 1024), 2)
                    return DownloadResult(
                        media_type="error",
                        error=f"File size ({size_mb} MB) Telegram bot limit (50 MB) se zyada hai.",
                    )

            # Determine media type
            first_ext = Path(downloaded_files[0]).suffix.lower()
            if len(downloaded_files) > 1:
                media_type = "album"
            elif first_ext in [".mp4", ".mkv", ".webm", ".mov"]:
                media_type = "video"
            elif first_ext in [".jpg", ".jpeg", ".png", ".webp"]:
                media_type = "photo"
            else:
                media_type = "audio"

            return DownloadResult(
                media_type=media_type,
                file_paths=downloaded_files,
                title=title,
                duration=int(duration) if duration else None,
                width=width,
                height=height,
                thumbnail_path=thumb_path,
            )

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"yt-dlp download error: {error_msg}")
        if "Private video" in error_msg or "login" in error_msg.lower():
            return DownloadResult(media_type="error", error="Ye post/video private ya login-protected hai.")
        elif "HTTP Error 404" in error_msg:
            return DownloadResult(media_type="error", error="Link expire ya delete ho chuka hai (404).")
        return DownloadResult(media_type="error", error=f"Download error: {error_msg[:120]}")
    except Exception as e:
        logger.exception("Unexpected error in _sync_download")
        return DownloadResult(media_type="error", error=f"Error: {str(e)[:120]}")


async def download_media(url: str, request_id: str) -> DownloadResult:
    """Asynchronous wrapper around _sync_download to prevent blocking event loop."""
    request_dir = DOWNLOAD_DIR / request_id
    request_dir.mkdir(parents=True, exist_ok=True)

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _sync_download, url, request_dir)
        return result
    except Exception as e:
        return DownloadResult(media_type="error", error=f"Execution error: {str(e)}")


def cleanup_request_dir(request_id: str) -> None:
    """Removes temporary files created for this request."""
    request_dir = DOWNLOAD_DIR / request_id
    if request_dir.exists():
        try:
            shutil.rmtree(request_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup {request_dir}: {e}")
