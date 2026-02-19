import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Привет! Бот работает и готов к работе с Инстаграм!")

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        token = "8318096413:AAFl58y0d_kHV4ep4co-8tX14hIqI9VVl5I"  # fallback для теста
    
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
