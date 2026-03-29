from telegram import Update
from telegram.ext import ContextTypes
from bot.services.db_manager import DBManager

def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send info about the bot and its version."""
    # Get version from main.py (we'll import it or define a function)
    # Since we cannot import main.py directly (circular), we'll get version from context or define a helper
    # We'll store version in bot_data or compute it here? Let's compute it here using subprocess.
    import subprocess
    import os
    try:
        # Run git describe --tags --abbrev=0
        version = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], 
                                          stderr=subprocess.DEVNULL,
                                          universal_newlines=True).strip()
    except Exception:
        version = "dev"
    
    # Get the bot's username if available
    bot_username = context.bot.username if context.bot else "unknown"
    
    about_text = f"""
    🐰 Кайо (Kayo) Telegram Бот
    Версия: {version}
    Имя пользователя бота: @{bot_username}
    
    Дружелюбный пушистый кролик-бот, который отслеживает активность и реагирует на сообщения.
    """
    update.message.reply_text(about_text.strip())

def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a list of available commands with descriptions."""
    help_text = """
    🐰 Доступные команды:
    /start - Запустить бота и увидеть приветственное сообщение
    /help - Показать это сообщение помощи
    /about - Информация о боте и версии
    /hug [пользователь] - Обнять пользователя (или себя, если пользователь не указан)
    /bite [пользователь] - Укусить пользователя (или себя, если пользователь не указан)
    /pat [пользователь] - Погладить пользователя (или себя, если пользователь не указан)
    /boop [пользователь] - Ткнуть пользователя в нос (или себя, если пользователь не указан)
    /top - Посмотреть топ пользователей по общему количеству сообщений
    /today - Посмотреть топ пользователей по сообщениям за сегодня
    /me - Посмотреть свою статистику и титул
    """
    update.message.reply_text(help_text.strip())

def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top users by total message count."""
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        update.message.reply_text("Извините, отслеживание активности недоступно.")
        return
    
    chat = update.effective_chat
    if not chat:
        update.message.reply_text("Извините, не удалось определить чат.")
        return
    
    activity_manager = db_manager.get_activity_manager(chat.id)
    top_users = activity_manager.get_top(limit=10)
    if not top_users:
        update.message.reply_text("Данные об активности пока отсутствуют.")
        return
    
    message = "🥕 Топ болтунов:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(top_users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        message += f"{medal} {user['username'] or user['user_id']}: {user['message_count']} сообщений\n"
    
    update.message.reply_text(message)

def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top users by today's message count."""
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        update.message.reply_text("Извините, отслеживание активности недоступно.")
        return
    
    chat = update.effective_chat
    if not chat:
        update.message.reply_text("Извините, не удалось определить чат.")
        return
    
    activity_manager = db_manager.get_activity_manager(chat.id)
    top_users = activity_manager.get_today_top(limit=10)
    if not top_users:
        update.message.reply_text("Данных об активности за сегодня пока нет.")
        return
    
    message = "🥕 Активность за сегодня:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(top_users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        message += f"{medal} {user['username'] or user['user_id']}: {user['today_count']} сообщений сегодня\n"
    
    update.message.reply_text(message)

def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show your own stats and title."""
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        update.message.reply_text("Извините, отслеживание активности недоступно.")
        return
    
    chat = update.effective_chat
    if not chat:
        update.message.reply_text("Извините, не удалось определить чат.")
        return
    
    activity_manager = db_manager.get_activity_manager(chat.id)
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Неизвестно"
    
    stats = activity_manager.get_user_stats(user_id)
    if not stats:
        update.message.reply_text("Статистика пока отсутствует. Начните чат!")
        return
    
    title = activity_manager.get_dynamic_title(user_id)
    
    # Map English titles to Russian titles
    title_mapping = {
        "Chatter of the Day": "Болтун дня",
        "Night Owl": "Ночной житель",
        "Early Bird": "Ранний зверь",
        "Quiet but Deadly": "Тихий, но опасный",
        "Ghost": "Призрак"
    }
    russian_title = title_mapping.get(title, title)
    
    message = f"""
    👤 Ваша статистика:
    Пользователь: {username}
    Общее количество сообщений: {stats['message_count']}
    Сообщения за сегодня: {stats['today_count']}
    Позиция в рейтинге /top: {stats.get('rank', 'Н/Д')}
    Динамический титул: {russian_title}
    """
    update.message.reply_text(message.strip())