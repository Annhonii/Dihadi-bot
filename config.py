import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Telegram Bot Token (from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Optional: List of authorized user IDs (comma-separated, e.g. "123456,7891011")
# If empty, the bot is public and responds to anyone.
_allowed = os.getenv("ALLOWED_USERS", "").strip()
ALLOWED_USERS = set(int(uid.strip()) for uid in _allowed.split(",") if uid.strip().isdigit())

# Telegram Bot API standard upload limit (50 MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Temporary download directory
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
