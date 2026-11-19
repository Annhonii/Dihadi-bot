import re
import time
import logging
from pathlib import Path
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config
from downloader import download_media, cleanup_request_dir, is_supported_url

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)")


async def is_user_authorized(update: Update) -> bool:
    """Checks if the user is authorized when ALLOWED_USERS is set."""
    if not config.ALLOWED_USERS:
        return True
    user_id = update.effective_user.id if update.effective_user else None
    return user_id in config.ALLOWED_USERS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    if not await is_user_authorized(update):
        await update.message.reply_text("⛔ Aapko is bot ko use karne ki permission nahi hai.")
        return

    welcome_text = (
        "👋 **Namaste! Main Dihadi Bot hoon.**\n\n"
        "Mujhe kisi bhi platform ka link bhejo, main video ya photo download karke yahan bhej dunga! 🚀\n\n"
        "📌 **Supported Platforms:**\n"
        "• **Instagram** (Reels, Posts, Carousels)\n"
        "• **YouTube** (Shorts & Videos)\n"
        "• **Reddit** (Videos with audio, Photos)\n"
        "• **X / Twitter**\n"
        "• **TikTok / Facebook / Pinterest**\n\n"
        "💡 *Bas link copy karo aur seedha chat me send kar do!*"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /help command."""
    help_text = (
        "📖 **Help & Instructions:**\n\n"
        "1. Kisi bhi video/photo ka share link copy karein.\n"
        "2. Is bot chat me paste karke send karein.\n"
        "3. Bot automatic download karke yahan upload kar dega.\n\n"
        "⚠️ **Dhyan dein:**\n"
        "- Telegram Bot API maximum **50MB** tak ki files allow karta hai.\n"
        "- Private accounts ya login-protected content download nahi ho sakta."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks bot responsiveness."""
    start_time = time.time()
    msg = await update.message.reply_text("🏓 Pong...")
    latency = round((time.time() - start_time) * 1000)
    await msg.edit_text(f"🏓 **Pong!** Bot mast chal raha hai. (Latency: `{latency}ms`)", parse_mode=ParseMode.MARKDOWN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes incoming messages to find links and download media."""
    if not update.message or not update.message.text:
        return

    if not await is_user_authorized(update):
        await update.message.reply_text("⛔ Aapko is bot ko use karne ki permission nahi hai.")
        return

    text = update.message.text
    match = URL_REGEX.search(text)
    if not match:
        return

    url = match.group(0)
    chat_id = update.effective_chat.id
    request_id = f"{chat_id}_{int(time.time() * 1000)}"

    status_msg = await update.message.reply_text("⏳ **Link mil gaya! Media fetch kiya ja raha hai...**", parse_mode=ParseMode.MARKDOWN)

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VIDEO)
        result = await download_media(url, request_id)

        if result.error or not result.file_paths:
            error_text = result.error or "Media download nahi ho paya."
            await status_msg.edit_text(f"❌ {error_text}")
            return

        await status_msg.edit_text("📤 **Telegram par upload ho raha hai...**", parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

        caption = f"🎬 **{result.title}**\n\n_Downloaded via Dihadi Bot_" if result.title else "_Downloaded via Dihadi Bot_"
        # Truncate caption if too long for Telegram (1024 char limit)
        if len(caption) > 1000:
            caption = caption[:990] + "...\n\n_Downloaded via Dihadi Bot_"

        if result.media_type == "video":
            video_file = result.file_paths[0]
            thumb = open(result.thumbnail_path, "rb") if result.thumbnail_path and Path(result.thumbnail_path).exists() else None
            try:
                with open(video_file, "rb") as vf:
                    await context.bot.send_video(
                        chat_id=chat_id,
                        video=vf,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        duration=result.duration,
                        width=result.width,
                        height=result.height,
                        thumbnail=thumb,
                        supports_streaming=True,
                    )
            finally:
                if thumb:
                    thumb.close()

        elif result.media_type == "photo":
            photo_file = result.file_paths[0]
            with open(photo_file, "rb") as pf:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=pf,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                )

        elif result.media_type == "album":
            media_group = []
            opened_files = []
            try:
                for idx, f_path in enumerate(result.file_paths[:10]):  # Telegram allows max 10 in media group
                    fp = open(f_path, "rb")
                    opened_files.append(fp)
                    item_caption = caption if idx == 0 else ""
                    ext = Path(f_path).suffix.lower()
                    if ext in [".mp4", ".mkv", ".webm", ".mov"]:
                        media_group.append(InputMediaVideo(media=fp, caption=item_caption, parse_mode=ParseMode.MARKDOWN))
                    else:
                        media_group.append(InputMediaPhoto(media=fp, caption=item_caption, parse_mode=ParseMode.MARKDOWN))
                await context.bot.send_media_group(chat_id=chat_id, media=media_group)
            finally:
                for fp in opened_files:
                    fp.close()

        elif result.media_type == "audio":
            audio_file = result.file_paths[0]
            with open(audio_file, "rb") as af:
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=af,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                )

        # Remove the status message after sending media
        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.exception("Error handling download message")
        try:
            await status_msg.edit_text(f"❌ Upload me error aaya: {str(e)[:150]}")
        except Exception:
            pass
    finally:
        cleanup_request_dir(request_id)


def main() -> None:
    """Starts the Telegram bot polling."""
    if not config.BOT_TOKEN:
        print("❌ Error: BOT_TOKEN environment variable nahi mila!")
        print("Kripya .env file me BOT_TOKEN=your_token set karein.")
        return

    print("🚀 Dihadi Bot start ho raha hai...")
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Bot is online and listening for messages!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
