"""One-shot runner for GitHub Actions.

Reads URL / CHAT_ID / REPLY_TO / STATUS_ID from environment, downloads the media
with downloader.py and sends it to Telegram, then exits.
"""
import asyncio
import os
import sys
import time
from pathlib import Path

from telegram import Bot, InputMediaPhoto, InputMediaVideo

import config
from downloader import download_media, cleanup_request_dir

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov"}


def _int(name: str):
    val = os.getenv(name, "").strip()
    return int(val) if val.lstrip("-").isdigit() else None


async def run() -> int:
    url = os.getenv("URL", "").strip()
    chat_id = _int("CHAT_ID")
    reply_to = _int("REPLY_TO")
    status_id = _int("STATUS_ID")

    if not config.BOT_TOKEN or not url or chat_id is None:
        print("BOT_TOKEN / URL / CHAT_ID missing")
        return 1

    bot = Bot(config.BOT_TOKEN)
    request_id = f"{chat_id}_{int(time.time() * 1000)}"

    async def set_status(text: str):
        if status_id is None:
            return
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=status_id, text=text)
        except Exception as e:  # message may be unchanged / deleted
            print(f"status edit failed: {e}")

    try:
        await set_status("📥 Download ho raha hai...")
        result = await download_media(url, request_id)

        if result.error or not result.file_paths:
            await set_status(f"❌ {result.error or 'Media download nahi ho paya.'}")
            return 0

        await set_status("📤 Telegram par upload ho raha hai...")
        caption = f"🎬 {result.title}\n\nDownloaded via Dihadi Bot" if result.title else "Downloaded via Dihadi Bot"
        if len(caption) > 1000:
            caption = caption[:960] + "...\n\nDownloaded via Dihadi Bot"

        common = {"chat_id": chat_id, "reply_to_message_id": reply_to, "read_timeout": 300, "write_timeout": 300}

        if result.media_type == "video":
            thumb = None
            if result.thumbnail_path and Path(result.thumbnail_path).exists():
                thumb = open(result.thumbnail_path, "rb")
            try:
                with open(result.file_paths[0], "rb") as vf:
                    await bot.send_video(
                        video=vf, caption=caption, duration=result.duration,
                        width=result.width, height=result.height,
                        thumbnail=thumb, supports_streaming=True, **common,
                    )
            finally:
                if thumb:
                    thumb.close()

        elif result.media_type == "photo":
            with open(result.file_paths[0], "rb") as pf:
                await bot.send_photo(photo=pf, caption=caption, **common)

        elif result.media_type == "album":
            opened, group = [], []
            try:
                for idx, path in enumerate(result.file_paths[:10]):
                    fp = open(path, "rb")
                    opened.append(fp)
                    cap = caption if idx == 0 else None
                    if Path(path).suffix.lower() in VIDEO_EXT:
                        group.append(InputMediaVideo(media=fp, caption=cap))
                    else:
                        group.append(InputMediaPhoto(media=fp, caption=cap))
                await bot.send_media_group(media=group, **common)
            finally:
                for fp in opened:
                    fp.close()

        elif result.media_type == "audio":
            with open(result.file_paths[0], "rb") as af:
                await bot.send_audio(audio=af, caption=caption, **common)

        if status_id is not None:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=status_id)
            except Exception:
                pass
        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        await set_status(f"❌ Upload me error aaya: {str(e)[:150]}")
        return 0  # user already notified; don't mark the run as failed
    finally:
        cleanup_request_dir(request_id)


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
