// Cloudflare Worker: Telegram webhook -> triggers GitHub Actions workflow.
//
// Secrets / vars (Worker settings):
//   BOT_TOKEN       Telegram bot token
//   GH_TOKEN        GitHub fine-grained PAT (Actions: read & write on this repo)
//   GH_REPO         "username/Dihadi-bot"
//   WEBHOOK_SECRET  any random string (also passed to Telegram setWebhook)
//   ALLOWED_USERS   optional, comma-separated Telegram user IDs (empty = public)
//   GH_BRANCH       optional, default "main"

const URL_REGEX = /https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_+.~#?&/=]*/;

async function tg(env, method, body) {
  const res = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

const START_TEXT =
  "👋 Namaste! Main Dihadi Bot hoon.\n\n" +
  "Mujhe kisi bhi platform ka link bhejo, main video ya photo download karke yahan bhej dunga! 🚀\n\n" +
  "📌 Supported: Instagram, YouTube, Reddit, X/Twitter, TikTok, Facebook, Pinterest\n\n" +
  "💡 Bas link copy karo aur seedha chat me send kar do!";

const HELP_TEXT =
  "📖 Help:\n\n1. Video/photo ka share link copy karein.\n2. Yahan paste karke send karein.\n" +
  "3. Bot download karke upload kar dega (thoda time lagta hai, ~30-90 sec).\n\n" +
  "⚠️ Max 50MB. Private/login-protected content download nahi hoga.";

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("Dihadi bot worker OK");

    if (env.WEBHOOK_SECRET &&
        request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) {
      return new Response("forbidden", { status: 403 });
    }

    let update;
    try { update = await request.json(); } catch { return new Response("ok"); }

    const msg = update.message;
    if (!msg || !msg.text) return new Response("ok");

    const chatId = msg.chat.id;
    const userId = msg.from && msg.from.id;
    const text = msg.text.trim();

    const allowed = (env.ALLOWED_USERS || "").split(",").map(s => s.trim()).filter(Boolean);
    if (allowed.length && !allowed.includes(String(userId))) {
      await tg(env, "sendMessage", { chat_id: chatId, text: "⛔ Aapko is bot ko use karne ki permission nahi hai." });
      return new Response("ok");
    }

    if (text.startsWith("/start")) {
      await tg(env, "sendMessage", { chat_id: chatId, text: START_TEXT });
      return new Response("ok");
    }
    if (text.startsWith("/help")) {
      await tg(env, "sendMessage", { chat_id: chatId, text: HELP_TEXT });
      return new Response("ok");
    }
    if (text.startsWith("/ping")) {
      await tg(env, "sendMessage", { chat_id: chatId, text: "🏓 Pong! Worker mast chal raha hai." });
      return new Response("ok");
    }

    const match = text.match(URL_REGEX);
    if (!match) return new Response("ok");

    const status = await tg(env, "sendMessage", {
      chat_id: chatId,
      reply_to_message_id: msg.message_id,
      text: "⏳ Link mil gaya! Job start ho raha hai...",
    });
    const statusId = status && status.result ? status.result.message_id : "";

    const ghRes = await fetch(
      `https://api.github.com/repos/${env.GH_REPO}/actions/workflows/download.yml/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GH_TOKEN}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "dihadi-bot-worker",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ref: env.GH_BRANCH || "main",
          inputs: {
            url: match[0],
            chat_id: String(chatId),
            reply_to: String(msg.message_id),
            status_id: String(statusId),
          },
        }),
      }
    );

    if (!ghRes.ok && statusId) {
      const err = (await ghRes.text()).slice(0, 120);
      await tg(env, "editMessageText", {
        chat_id: chatId,
        message_id: statusId,
        text: `❌ GitHub job start nahi hua (${ghRes.status}). ${err}`,
      });
    }

    return new Response("ok");
  },
};
