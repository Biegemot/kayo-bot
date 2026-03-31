"""
Обработчики для Web App (Mini-App) Kayo Bot
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

logger = logging.getLogger(__name__)

async def webapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для открытия Mini-App"""
    logger.info(f"[webapp_command] Команда /webapp вызвана")
    logger.info(f"[webapp_command] update.message: {update.message}")
    logger.info(f"[webapp_command] chat_id: {update.message.chat_id if update.message else 'NO MESSAGE'}")
    
    if not update.message:
        logger.info(f"[webapp_command] update.message is None, возвращаемся")
        return
    
    # Создаем кнопку для открытия Web App
    # Для Mini-App нужно использовать WebAppInfo объект
    web_app_url = "https://biegemot.github.io/kayo-bot-webapp/"
    
    keyboard = [
        [InlineKeyboardButton(
            "📝 Заполнить анкету",
            web_app=WebAppInfo(url=web_app_url)
        )]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.info(f"[webapp_command] Отправляем сообщение в чат {update.message.chat_id}")
    await update.message.reply_text(
        "🐰 Нажмите кнопку ниже, чтобы заполнить анкету фурсоны:",
        reply_markup=reply_markup
    )
    logger.info(f"[webapp_command] Сообщение отправлено")

async def webapp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback от Web App"""
    query = update.callback_query
    await query.answer()
    
    # Здесь можно обработать данные из Web App
    # Например, сохранить анкету в базу данных
    
    await query.edit_message_text("✅ Анкета сохранена!")

def register_webapp_handlers(application):
    """Регистрация обработчиков Web App"""
    application.add_handler(CommandHandler("webapp", webapp_command))
    application.add_handler(CallbackQueryHandler(webapp_callback, pattern='^webapp_'))