import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# --- Environment Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Free AI Models ---
FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "cognitivecomputations/dolphin3.0-mistral-24b:free"
]

# --- OpenRouter Function ---
def ask_openrouter(message: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("API key not set")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    last_error = None

    for model in FREE_MODELS:
        data = {"model": model, "messages": [{"role": "user", "content": message}]}
        try:
            print(f"Trying model: {model}")
            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code == 429:
                print(f"Rate-limited: {model}")
                last_error = "Rate-limited"
                continue
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}"
                continue

            resp_json = response.json()
            if "choices" in resp_json and resp_json["choices"]:
                choice = resp_json["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    print(f"Success with model: {model}")
                    return choice["message"]["content"]
                if "text" in choice:
                    print(f"Success with model: {model}")
                    return choice["text"]

            last_error = "Unexpected response format"
        except requests.exceptions.RequestException as e:
            print(f"Request error with {model}: {e}")
            last_error = str(e)
            continue

    raise Exception(last_error or "All models failed")

# --- Handlers ---
async def start_or_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text if update.message else ""

    if user_msg == "/start":
        await update.message.reply_text(
            f"Welcome! I can chat with you using AI.\nAvailable models: {len(FREE_MODELS)}"
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = ask_openrouter(user_msg)
        await update.message.reply_text(reply)
    except Exception:
        await update.message.reply_text(
            "⚠️ Sorry, AI is not available right now. Please try again later."
        )

async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    models_text = "\n".join(FREE_MODELS)
    await update.message.reply_text(f"Available models:\n{models_text}")

# --- Main ---
def main():
    if not BOT_TOKEN or not OPENROUTER_API_KEY:
        print("BOT_TOKEN or OPENROUTER_API_KEY not set")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_or_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start_or_message))
    app.add_handler(CommandHandler("models", show_models))

    print("Bot running...")
    print(f"Fallback models: {len(FREE_MODELS)} -> {', '.join(FREE_MODELS)}")
    app.run_polling()

if __name__ == "__main__":
    main()
