import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Привет! Я бот для постов в Инстаграм.")

def main():
    token = "8318096413:AAFl58y0d_kHV4ep4co-8tX14hIqI9VVl5I"
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.run_webhook(
        listen="0.0.0.0",
        port=18789,
        webhook_url="https://clawdbot-railway-template-production-cdd7.up.railway.app/clawdbot/webhook/telegram"
    )

if __name__ == "__main__":
    main()
