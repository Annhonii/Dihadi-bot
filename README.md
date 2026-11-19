# 🤖 Dihadi Bot (Social Media Media Downloader for Telegram)

**Dihadi Bot** ek powerful aur fast asynchronous Telegram Bot hai jo Instagram, YouTube, Reddit, X (Twitter), TikTok jaise platforms ke video aur photo links ko detect karke unhe download karta hai aur directly Telegram chat mein bhejta hai.

---

## ✨ Features

- 📥 **Multi-Platform Support**:
  - **Instagram**: Reels, Posts, Carousels (multiple photos/videos), IGTV.
  - **YouTube**: Shorts & full videos (audio + video merge).
  - **Reddit**: Videos with audio (v.redd.it), images, and gallery posts.
  - **X / Twitter**: Media tweets and videos.
  - **TikTok, Pinterest, Facebook** etc.
- ⚡ **Asynchronous & Non-Blocking**: High-concurrency support using `python-telegram-bot` and `asyncio`.
- 🗜️ **Telegram 50MB Cap Handling**: Telegram Bot API ke standard 50MB upload limit ko respect karta hai aur format auto-adjust karta hai.
- 🧹 **Automatic Cleanup**: Download hone aur send hone ke baad temporary files immediately delete ho jaati hain, jisse disk space waste nahi hoti.
- 🔒 **Access Control (Optional)**: `ALLOWED_USERS` set karke aap bot ko private rakh sakte hain ya sabke liye public chhod sakte hain.

---

## 🛠️ Requirements

- **Python**: 3.10 ya usse naya
- **FFmpeg**: Video aur audio ko merge karne ke liye zaruri hai.
  ```bash
  # Debian / Ubuntu / PRoot
  apt-get update && apt-get install -y ffmpeg

  # Termux native
  pkg install ffmpeg
  ```

---

## 🚀 Setup & Installation Steps

### 1. Repository Clone karein (agar pehle se nahi kiya hai):
```bash
git clone https://github.com/Annhonii/Dihadi-bot.git
cd Dihadi-bot
```

### 2. Python Dependencies Install karein:
```bash
pip install -r requirements.txt
```

### 3. Telegram Bot Token Setup karein:
1. Telegram open karein aur [@BotFather](https://t.me/BotFather) ke paas jayein.
2. `/newbot` command dekar apna bot banayein aur API Token copy karein.
3. `.env.example` ko copy karke `.env` banayein:
   ```bash
   cp .env.example .env
   ```
4. `.env` file ko edit karein aur apna token dalein:
   ```env
   BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
   # Optional: Apni Telegram User ID daal sakte hain (e.g. 12345678)
   ALLOWED_USERS=
   MAX_FILE_SIZE_MB=50
   ```

### 4. Bot Start karein:
```bash
python3 bot.py
```

---

## 🔄 24/7 Background Run (Screen / Tmux / Systemd)

Bot ko background mein continuous chalane ke liye:

### Option A: Using Screen / Tmux (Sabse aasan)
```bash
# Screen install karein
apt-get install -y screen

# New session start karein
screen -S dihadi-bot

# Bot run karein
python3 bot.py

# Detach karne ke liye press: Ctrl + A then D
# Re-attach karne ke liye:
screen -r dihadi-bot
```

### Option B: Using Systemd Service (Linux Server / VPS)
Ek service file banayein `/etc/systemd/system/dihadibot.service`:
```ini
[Unit]
Description=Dihadi Telegram Downloader Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Dihadi-bot
ExecStart=/usr/bin/python3 /root/Dihadi-bot/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Enable aur start karein:
```bash
systemctl daemon-reload
systemctl enable dihadibot
systemctl start dihadibot
```

---

## 💬 Bot Commands

| Command | Description |
|---|---|
| `/start` | Bot welcome message aur supported platforms list |
| `/help` | Bot use karne ke steps aur limitations |
| `/ping` | Bot status aur response latency check |

Bas kisi bhi supported link ko chat mein paste karein, bot turant video download karke bhej dega! 🎉
