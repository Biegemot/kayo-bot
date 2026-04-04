from telegram import Update
from telegram.ext import ContextTypes
from bot.services.db_manager import DBManager
import random
import re
from collections import Counter

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send info about the bot and its version."""
    if not update.message:
        return
    
    # Try to get version from version.py first
    try:
        from version import get_current_version
        version = get_current_version()
    except ImportError:
        # Fallback to git if version.py not available
        try:
            import subprocess
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
    await update.message.reply_text(about_text.strip())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a list of available commands with descriptions."""
    if not update.message:
        return
    
    help_text = """
    🐰 Доступные команды:

    🎮 **Основные команды:**
    /start - Запустить бота и увидеть приветственное сообщение
    /help - Показать это сообщение помощи
    /about - Информация о боте и версии
    /update - Проверить и установить обновления

    🫂 **RP-команды (обнимашки и взаимодействия):**
    /hug [@пользователь] - Обнять пользователя (или себя)
    /bite [@пользователь] - Укусить пользователя (или себя)
    /pat [@пользователь] - Погладить пользователя (или себя)
    /boop [@пользователь] - Ткнуть пользователя в нос (или себя)
    /kiss [@пользователь] - Поцеловать пользователя (или себя)
    /slapass [@пользователь] - Шлёпнуть пользователя по заднице (или себя)

    📊 **Статистика и активность:**
    /top - Топ пользователей по общему количеству сообщений
    /today - Топ пользователей по сообщениям за сегодня
    /stats - Показать свою статистику
    /summarize - Итоги дня с темами и настроением чата

    👤 **Профиль и анкета:**
    /me - Открыть свою анкету для редактирования (в группе удаляет команду, показывает inline-меню)
    /me @username - Посмотреть анкету другого пользователя (только просмотр)
    /titles - Посмотреть список всех доступных титулов

    📈 **Отслеживание активности:**
    • Бот автоматически считает сообщения и начисляет титулы
    • Реагирует на сообщения с вероятностью 15%
    • Отслеживает активность по дням и в целом

    💡 **Примечания:**
    • RP-команды можно использовать без упоминания — бот обратится к вам
    • Анкета (/me) в личных сообщениях работает как обычно
    • В группах анкета открывается через inline-меню
    """
    await update.message.reply_text(help_text.strip())

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top users by message count."""
    if not update.message:
        return
    
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        await update.message.reply_text("Извините, статистика недоступна.")
        return
    
    # Get activity manager for this chat
    activity_manager = db_manager.get_activity_manager(update.effective_chat.id)
    
    # Get top users (исправлено: используем get_top вместо get_top_users)
    try:
        top_users = activity_manager.get_top(10)  # Используем метод get_top который теперь существует
    except AttributeError:
        # Fallback to get_top_users
        top_users = activity_manager.get_top_users(10)
    
    if not top_users:
        await update.message.reply_text("Пока нет статистики.")
        return
    
    # Format the response
    response = "🏆 Топ активных пользователей (всего сообщений):\n\n"
    for i, user in enumerate(top_users, 1):
        username = user['username'] or f"ID: {user['user_id']}"
        response += f"{i}. @{username} - {user['message_count']} сообщ.\n"
    
    await update.message.reply_text(response)

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top users for today."""
    if not update.message:
        return
    
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        await update.message.reply_text("Извините, статистика недоступна.")
        return
    
    # Get activity manager for this chat
    activity_manager = db_manager.get_activity_manager(update.effective_chat.id)
    
    # Get today's top
    today_top = activity_manager.get_today_top(10)
    
    if not today_top:
        await update.message.reply_text("Сегодня еще нет сообщений.")
        return
    
    # Format the response
    response = "📊 Активность за сегодня:\n\n"
    for i, user in enumerate(today_top, 1):
        username = user['username'] or f"ID: {user['user_id']}"
        response += f"{i}. @{username} - {user['today_count']} сообщ.\n"
    
    await update.message.reply_text(response)

async def titles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available titles."""
    if not update.message:
        return
    
    # Define titles with descriptions
    titles = {
        "🐰 Кролик-новичок": "Первое сообщение в чате",
        "🐾 Активный пушистик": "10 сообщений",
        "🌟 Пушистая звезда": "50 сообщений",
        "👑 Король/Королева чата": "100 сообщений",
        "💎 Легенда Кайо": "500 сообщений",
        "✨ Магический фурри": "1000 сообщений",
        "🔥 Огненный фурри": "2000 сообщений",
        "🌌 Космический фурри": "5000 сообщений",
        "⚡ Молниеносный фурри": "10000 сообщений",
        "💫 Бессмертный фурри": "20000 сообщений",
        "👻 Призрачный фурри": "Уникальный титул за особые достижения",
        "🎭 Драматический фурри": "За самые эмоциональные сообщения",
        "🤖 Робо-фурри": "За технические вопросы",
        "🎨 Креативный фурри": "За творческие идеи",
        "🦊 Хитрый лис": "За умные и хитрые сообщения",
        "🐺 Верный волк": "За постоянную активность",
        "🐱 Игривый кот": "За веселые и игривые сообщения",
        "🦁 Гордый лев": "За уверенные и сильные сообщения",
        "🐉 Мудрый дракон": "За мудрые советы",
        "🦄 Волшебный единорог": "За волшебные и вдохновляющие сообщения",
    }
    
    response = "🎖️ Доступные титулы в Кайо-чате:\n\n"
    for title, description in titles.items():
        response += f"{title}: {description}\n"
    
    response += "\nТитулы присваиваются автоматически на основе активности!"
    await update.message.reply_text(response)

async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate daily summary with topics and mood."""
    if not update.message:
        return
    
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        await update.message.reply_text("Извините, статистика недоступна.")
        return
    
    # Get activity manager for this chat
    activity_manager = db_manager.get_activity_manager(update.effective_chat.id)
    
    # Get today's messages for topic analysis
    messages = activity_manager.get_today_messages()
    
    # Get top users for today
    today_top = activity_manager.get_today_top(5)
    
    # Get kiss and slap tops (исправлено: используем новые методы)
    try:
        kiss_top = activity_manager.get_kiss_top_today(1)
        slap_top = activity_manager.get_slap_top_today(1)
    except AttributeError:
        kiss_top = []
        slap_top = []
    
    # Build summary
    summary = "📈 Итоги дня:\n\n"
    
    # Activity stats
    total_messages = sum(user['today_count'] for user in today_top)
    summary += f"📊 Всего сообщений сегодня: {total_messages}\n"
    
    if today_top:
        summary += "\n🏆 Топ активных:\n"
        for i, user in enumerate(today_top, 1):
            username = user['username'] or f"ID: {user['user_id']}"
            summary += f"{i}. @{username} - {user['today_count']} сообщ.\n"
    
    # Kiss and slap stats
    if kiss_top:
        username = kiss_top[0]['username'] or f"ID: {kiss_top[0]['user_id']}"
        summary += f"\n💋 Больше всех целовался: @{username} ({kiss_top[0]['kiss_count_today']} раз)\n"
    
    if slap_top:
        username = slap_top[0]['username'] or f"ID: {slap_top[0]['user_id']}"
        summary += f"👋 Больше всех шлепал: @{username} ({slap_top[0]['slap_count_today']} раз)\n"
    
    # Topic analysis (simplified)
    if messages:
        # Extract common words
        all_words = []
        for msg in messages:
            words = re.findall(r'\b\w{3,}\b', msg.lower())
            all_words.extend(words)
        
        # Count word frequencies
        word_counts = Counter(all_words)
        common_words = word_counts.most_common(5)
        
        if common_words:
            summary += "\n🗣️ Частые темы:\n"
            for word, count in common_words:
                summary += f"• {word} ({count} раз)\n"
    
    # Mood analysis
    mood_keywords = {
        'happy': ['смех', 'смеюсь', 'рад', 'радость', 'ура', 'весело', 'класс', 'круто'],
        'sad': ['грустно', 'печаль', 'плохо', 'тоска', 'слезы'],
        'angry': ['злой', 'злюсь', 'бесит', 'разозлился'],
        'tired': ['устал', 'спать', 'сон', 'усталость', 'утомился'],
        'love': ['любовь', 'люблю', 'мило', 'обнимашки', 'целую']
    }
    
    mood_counts = {mood: 0 for mood in mood_keywords}
    
    for msg in messages:
        msg_lower = msg.lower()
        for mood, keywords in mood_keywords.items():
            for keyword in keywords:
                if keyword in msg_lower:
                    mood_counts[mood] += 1
    
    # Determine dominant mood
    if any(mood_counts.values()):
        dominant_mood = max(mood_counts.items(), key=lambda x: x[1])
        if dominant_mood[1] > 0:
            mood_emojis = {
                'happy': '😊',
                'sad': '😢',
                'angry': '😠',
                'tired': '😴',
                'love': '❤️'
            }
            summary += f"\n🎭 Настроение чата: {mood_emojis.get(dominant_mood[0], '😐')} {dominant_mood[0]}\n"
    
    summary += "\nПродолжайте общаться и быть активными! 🐰"
    await update.message.reply_text(summary)

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check for and apply updates."""
    if not update.message:
        return
    
    try:
        # Import auto_update functions
        from bot.services.auto_update import check_and_apply_update, restart_application
        
        # Get current version
        from version import get_current_version
        current = get_current_version()
        await update.message.reply_text(f"🔄 Проверяю обновления... (текущая: v{current})")

        updated, msg = check_and_apply_update(force=True)

        if updated:
            await update.message.reply_text(f"✅ {msg}\nПерезапускаюсь...")
            # Give time for the message to be sent
            import threading
            def delayed_restart():
                import time
                time.sleep(2)
                restart_application()
            threading.Thread(target=delayed_restart, daemon=True).start()
        else:
            await update.message.reply_text(f"ℹ️ {msg}")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обновлении: {e}")