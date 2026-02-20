import os
import tempfile
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from instagrapi import Client

# ====== НАСТРОЙКИ ======
TOKEN = "ВАШ_TELEGRAM_TOKEN"
IG_USERNAME = "ВАШ_ЛОГИН"
IG_PASSWORD = "ВАШ_ПАРОЛЬ"

SESSION_FILE = "session.json"  # файл сессии Instagram

PHOTO, CAPTION = range(2)


# ====== INSTAGRAM (работает в отдельном потоке) ======
def upload_to_instagram(photo_path: str, caption: str) -> str:
    cl = Client()

    # Загружаем сохранённую сессию (если есть)
    if os.path.exists(SESSION_FILE):
        cl.load_settings(SESSION_FILE)

    cl.login(IG_USERNAME, IG_PASSWORD)

    # Сохраняем сессию (чтобы не логиниться каждый раз)
    cl.dump_settings(SESSION_FILE)

    media = cl.photo_upload(photo_path, caption)
    return media.code


# ====== TELEGRAM HANDLERS ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['📤 Отправить пост в Инстаграм']]
    await update.message.reply_text(
        "✅ Бот публикации в Instagram готов.\n\n"
        "Нажмите кнопку ниже:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ConversationHandler.END


async def new_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Отправьте фото:",
        reply_markup=ReplyKeyboardRemove()
    )
    return PHOTO


async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Нужно отправить именно фото.")
        return PHOTO

    photo_file = await update.message.photo[-1].get_file()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
        await photo_file.download_to_drive(temp.name)
        context.user_data["photo_path"] = temp.name

    await update.message.reply_text("📝 Теперь отправьте текст поста:")
    return CAPTION


async def caption_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_path = context.user_data.get("photo_path")
    caption = update.message.text

    if not photo_path:
        await update.message.reply_text("❌ Фото потерялось. Начните заново /start")
        return ConversationHandler.END

    await update.message.reply_text("⏳ Публикую в Instagram...")

    try:
        # Запускаем Instagram в отдельном потоке (НЕ блокируем бота)
        code = await asyncio.to_thread(upload_to_instagram, photo_path, caption)

        await update.message.reply_text(
            f"✅ Готово!\nhttps://www.instagram.com/p/{code}/",
            reply_markup=ReplyKeyboardMarkup([['📤 Отправить пост в Инстаграм']], resize_keyboard=True)
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка публикации:\n{e}")

    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Отменено.",
        reply_markup=ReplyKeyboardMarkup([['📤 Отправить пост в Инстаграм']], resize_keyboard=True)
    )
    return ConversationHandler.END


# ====== MAIN ======
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & filters.Regex("^📤"), new_post),
        ],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, photo_received)],
            CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, caption_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
