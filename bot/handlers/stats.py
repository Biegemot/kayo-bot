"""
Обработчики для статистики Kayo Bot
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

logger = logging.getLogger(__name__)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для просмотра статистики"""
    if not update.message:
        return
    
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    
    # Получаем менеджер базы данных
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        await update.message.reply_text("Извините, статистика недоступна.")
        return
    
    # Получаем менеджер активности для чата
    activity_manager = db_manager.get_activity_manager(chat_id)
    
    # Получаем статистику пользователя
    user_stats = activity_manager.get_user_stats(user_id)
    
    if not user_stats:
        await update.message.reply_text("Статистика не найдена.")
        return
    
    # Формируем текст статистики
    text = f"📊 Статистика пользователя {update.effective_user.first_name}\n\n"
    text += f"📨 Всего сообщений: {user_stats.get('message_count', 0)}\n"
    text += f"📅 Сообщений сегодня: {user_stats.get('today_count', 0)}\n"
    text += f"🤗 Обнимашек: {user_stats.get('hug_count_today', 0)}\n"
    text += f"😠 Укусов: {user_stats.get('bite_count_today', 0)}\n"
    text += f"🐾 Поглаживаний: {user_stats.get('pat_count_today', 0)}\n"
    text += f"👃 Boop: {user_stats.get('boop_count_today', 0)}\n"
    text += f"💋 Поцелуев: {user_stats.get('kiss_count_today', 0)}\n"
    text += f"👋 Шлёпов: {user_stats.get('slap_count_today', 0)}\n"
    
    await update.message.reply_text(text)

def register_stats_handlers(application):
    """Регистрация обработчиков статистики"""
    application.add_handler(CommandHandler("stats", stats_command))