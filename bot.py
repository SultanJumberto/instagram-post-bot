import os
import tempfile
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    ContextTypes, 
    ConversationHandler, 
    filters
)
from instagrapi import Client

# Статусы для диалога
PHOTO, CAPTION = range(2)

# Хранилище данных пользователей
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [['📤 Отправить пост в Инстаграм']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "✅ Привет! Я бот для публикации постов в Инстаграм.\n\n"
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text(
        "❌ Отменено. Нажмите /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def new_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания нового поста"""
    await update.message.reply_text(
        "📸 Отправьте фото для публикации:",
        reply_markup=ReplyKeyboardRemove()
    )
    return PHOTO

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка полученного фото"""
    # Скачиваем фото
    photo_file = await update.message.photo[-1].get_file()
    
    # Сохраняем во временную папку
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        await photo_file.download_to_drive(temp_file.name)
        temp_file_path = temp_file.name
    
    # Сохраняем путь к фото
    user_id = update.message.from_user.id
    user_data[user_id] = {'photo_path': temp_file_path}
    
    await update.message.reply_text(
        "📝 Теперь отправьте текст (описание) для поста:"
    )
    return CAPTION

async def caption_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка полученного текста и публикация"""
    user_id = update.message.from_user.id
    caption = update.message.text
    
    # Получаем путь к фото
    photo_path = user_data.get(user_id, {}).get('photo_path')
    
    if not photo_path:
        await update.message.reply_text("❌ Ошибка: фото не найдено. Начните заново с /start")
        return ConversationHandler.END
    
    try:
        await update.message.reply_text("⏳ Публикую пост в Инстаграм...")
        
        # Авторизация в Инстаграм
        ig_client = Client()
        ig_username = "ваш_логин_инстаграм"  # ← ЗАМЕНИТЕ НА СВОЙ ЛОГИН
        ig_password = "ваш_пароль_инстаграм"  # ← ЗАМЕНИТЕ НА СВОЙ ПАРОЛЬ
        
        ig_client.login(ig_username, ig_password)
        
        # Публикация фото
        media = ig_client.photo_upload(photo_path, caption)
        
        await update.message.reply_text(
            f"✅ Пост успешно опубликован в Инстаграм!\n\n"
            f"🔗 Ссылка: {media.code}\n"
            f"https://www.instagram.com/p/{media.code}/",
            reply_markup=ReplyKeyboardMarkup([['📤 Отправить пост в Инстаграм']], resize_keyboard=True)
        )
        
        # Удаляем временный файл
        os.unlink(photo_path)
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при публикации:\n{str(e)}\n\n"
            f"Попробуйте снова или проверьте настройки Инстаграм.",
            reply_markup=ReplyKeyboardMarkup([['📤 Отправить пост в Инстаграм']], resize_keyboard=True)
        )
    
    # Очищаем данные пользователя
    user_data.pop(user_id, None)
    
    return ConversationHandler.END

def main():
    # Токен бота — уже встроен
    token = "8318096413:AAFl58y0d_kHV4ep4co-8tX14hIqI9VVl5I"
    
    # Создаём приложение со стандартным updater
    application = Application.builder().token(token).build()
    
    # Создаём ConversationHandler для пошагового диалога
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("📤 Отправить пост в Инстаграм"), new_post)
        ],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, photo_received)],
            CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, caption_received)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel)
        ]
    )
    
    application.add_handler(conv_handler)
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
