# Dihadi Bot (GitHub Actions version)

Telegram media downloader. Koi bhi link bhejo (Instagram, YouTube, Reddit, X, TikTok, Facebook, Pinterest) aur bot video/photo wapas bhej deta hai.

**Kaise chalta hai:** Telegram -> Cloudflare Worker (webhook) -> GitHub Actions job (`yt-dlp` se download + Telegram par upload). Koi server 24/7 chalane ki zaroorat nahi.

## Setup

### 1. Bot token
`@BotFather` -> `/newbot` -> token copy karo.

### 2. Repo
Ye project apne GitHub repo me push karo (fork bhi chalega).

### 3. GitHub secrets
Repo -> Settings -> Secrets and variables -> Actions -> New repository secret:
- `BOT_TOKEN` = BotFather ka token
- `COOKIES_TXT` = (optional) Netscape format cookies.txt ka poora text. Instagram/YouTube block kare to kaam aata hai.

### 4. GitHub token (Worker ke liye)
Settings -> Developer settings -> Fine-grained tokens -> Generate.
- Repository access: sirf ye repo
- Permission: **Actions -> Read and write**

### 5. Cloudflare Worker
Cloudflare dashboard -> Workers -> Create -> `worker/worker.js` ka code paste karke Deploy.
Worker -> Settings -> Variables and Secrets me daalo:

| Name | Value |
|------|-------|
| `BOT_TOKEN` | BotFather token |
| `GH_TOKEN` | step 4 wala token |
| `GH_REPO` | `username/repo-name` |
| `WEBHOOK_SECRET` | koi bhi random string |
| `ALLOWED_USERS` | (optional) apna Telegram user ID, comma se alag |
| `GH_BRANCH` | (optional) default `main` |

### 6. Webhook set karo
Browser me ye link kholo (values badal ke):

```
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=<WORKER_URL>&secret_token=<WEBHOOK_SECRET>
```
`"ok": true` aaye to ready. Bot ko `/start` bhejo, phir link paste karo.

## Dhyan rakhne wali baatein
- Reply me ~30-90 sec lagte hain (Action start hone ka time).
- Telegram Bot API limit: **50MB** tak ki files.
- GitHub Actions ke IPs par Instagram/YouTube kabhi-kabhi "login required" dete hain. Tab `COOKIES_TXT` secret add karo.
- Public repo me Actions free hai. Private repo me monthly minutes limit hoti hai.
- `bot.py` purana polling version hai, local/VPS par chalane ke liye. Actions version me iski zaroorat nahi.
