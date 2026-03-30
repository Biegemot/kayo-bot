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
    /kiss [пользователь] - Поцеловать пользователя (или себя, если пользователь не указан)
    /slapass [пользователь] - Шлёпнуть пользователя по заднице (или себя, если пользователь не указан)
    /top - Посмотреть топ пользователей по общему количеству сообщений
    /today - Посмотреть топ пользователей по сообщениям за сегодня
    /me [@username] - Посмотреть статистику и титул себя или другого пользователя
    /titles - Посмотреть список всех доступных титулов
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
    """Show stats and title for yourself or another user."""
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        update.message.reply_text("Извините, отслеживание активности недоступно.")
        return
    
    chat = update.effective_chat
    if not chat:
        update.message.reply_text("Извините, не удалось определить чат.")
        return
    
    activity_manager = db_manager.get_activity_manager(chat.id)
    
    # Determine target user
    target_user_id = update.effective_user.id
    target_username = update.effective_user.username or update.effective_user.first_name or "Неизвестно"
    
    # Check for mentioned user in arguments
    if context.args:
        # Try to find a mention in entities (text_mention or mention)
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == 'text_mention' and entity.user:
                    target_user_id = entity.user.id
                    target_username = entity.user.username or entity.user.first_name or "Неизвестно"
                    break
                elif entity.type == 'mention':
                    # Extract username without @
                    username_mention = update.message.text[entity.offset:entity.offset+entity.length]
                    if username_mention.startswith('@'):
                        username_mention = username_mention[1:]
                    # Find user by username
                    found_user_id = activity_manager.find_user_by_username(username_mention)
                    if found_user_id:
                        target_user_id = found_user_id
                        target_username = username_mention
                    break
    
    stats = activity_manager.get_user_stats(target_user_id)
    if not stats:
        update.message.reply_text("Статистика пока отсутствует. Начните чат!")
        return
    
    title = activity_manager.get_dynamic_title(target_user_id)
    rank = activity_manager.get_user_rank(target_user_id)
    
    message = f"""
👤 Статистика пользователя {target_username}:
📊 Общее количество сообщений: {stats['message_count']}
📅 Сообщения за сегодня: {stats['today_count']}
💋 Поцелуев сегодня: {stats['kiss_count_today']}
👋 Шлёпков сегодня: {stats['slap_count_today']}
🏆 Позиция в рейтинге: {rank}
🏅 Титул: {title}
"""
    update.message.reply_text(message.strip())

def titles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of all titles with descriptions."""
    titles_text = """
🏅 Доступные титулы:

Болтун дня — больше всего сообщений сегодня :)
Ночной житель — активен ночью
Ранний зверь — активен утром
Тихий, но опасный — мало говорит, но когда говорит — точно
Призрак — давно не был в сети
Хорни — чаще всего шлёпает других сегодня
Романтик — чаще всего целует других сегодня
"""
    update.message.reply_text(titles_text.strip())


def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show a fun daily summary of chat activity."""
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        update.message.reply_text("Извините, отслеживание активности недоступно.")
        return

    chat = update.effective_chat
    if not chat:
        update.message.reply_text("Извините, не удалось определить чат.")
        return

    activity_manager = db_manager.get_activity_manager(chat.id)

    # Get today's top users
    today_top = activity_manager.get_today_top(limit=5)
    if not today_top:
        update.message.reply_text("📊 Сегодня пока тихо... Никто ничего не написал.")
        return

    # Count total messages today
    total_today = sum(u['today_count'] for u in today_top)

    # Get action stats
    kiss_top = activity_manager.get_kiss_top_today(limit=1)
    slap_top = activity_manager.get_slap_top_today(limit=1)
    total_kisses = sum(u['kiss_count_today'] for u in today_top)
    total_slaps = sum(u['slap_count_today'] for u in today_top)

    # Build summary
    lines = ["📊 Итоги дня\n"]

    # Activity level
    if total_today >= 50:
        vibe = "🔥 Сегодня чат просто горел!"
    elif total_today >= 20:
        vibe = "💬 Неплохой денёк, болтали активно!"
    elif total_today >= 5:
        vibe = "🙂 Спокойный день, но общались."
    else:
        vibe = "😴 Тишина... Все спят?"

    lines.append(vibe)
    lines.append("")
    lines.append(f"📝 Сообщений: {total_today}")

    # Most active user
    top_user = today_top[0]
    name = top_user['username'] or f"id:{top_user['user_id']}"
    lines.append(f"🏆 Болтун дня: @{name} ({top_user['today_count']} сообщ.)")

    # RP stats
    if total_kisses > 0 or total_slaps > 0:
        lines.append("")
        lines.append("💕 Действия:")
        if total_kisses > 0:
            lines.append(f"  Поцелуев: {total_kisses}")
            if kiss_top:
                kisser = kiss_top[0]
                kname = kisser['username'] or f"id:{kisser['user_id']}"
                lines.append(f"  Романтик: @{kname}")
        if total_slaps > 0:
            lines.append(f"  Шлёпков: {total_slaps}")
            if slap_top:
                slapper = slap_top[0]
                sname = slapper['username'] or f"id:{slapper['user_id']}"
                lines.append(f"  Хорни: @{sname}")

    # Activity chart (simple bar)
    if len(today_top) > 1:
        lines.append("")
        lines.append("📈 Активность:")
        max_count = today_top[0]['today_count']
        for i, user in enumerate(today_top[:3], 1):
            uname = user['username'] or f"id:{user['user_id']}"
            bar_len = max(1, int((user['today_count'] / max_count) * 10))
            bar = "█" * bar_len
            medals = ["🥇", "🥈", "🥉"]
            medal = medals[i - 1]
            lines.append(f"  {medal} {uname}: {bar} {user['today_count']}")

    update.message.reply_text("\n".join(lines))