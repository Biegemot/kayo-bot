from telegram import Update
from telegram.ext import ContextTypes
from bot.services.db_manager import DBManager
import os
import asyncio

def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send info about the bot and its version."""
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

# me_stats_command removed - functionality moved to profile.py

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


import random
import re
import sys
import os
from collections import Counter


# Stop words for topic extraction (Russian)
STOP_WORDS = {
    'и', 'в', 'на', 'с', 'по', 'за', 'к', 'у', 'о', 'а', 'но', 'да', 'или',
    'не', 'ни', 'что', 'как', 'это', 'все', 'мне', 'мой', 'моя', 'моё',
    'он', 'она', 'они', 'мы', 'вы', 'я', 'ты', 'его', 'её', 'их', 'нас',
    'вас', 'быть', 'был', 'была', 'было', 'были', 'будет', 'будут',
    'тот', 'та', 'то', 'те', 'этот', 'эта', 'эти', 'так', 'тоже', 'же',
    'уже', 'ещё', 'только', 'очень', 'можно', 'нужно', 'надо', 'есть',
    'там', 'тут', 'здесь', 'сейчас', 'потом', 'когда', 'если', 'чтобы',
    'где', 'куда', 'откуда', 'почему', 'зачем', 'сколько', 'какой',
    'какая', 'какие', 'чей', 'чья', 'чьи', 'свой', 'сам', 'сама', 'сами',
    'для', 'без', 'под', 'над', 'перед', 'между', 'через', 'после',
    'до', 'от', 'из', 'со', 'об', 'про', 'при', 'насчёт',
    'ну', 'да', 'нет', 'ага', 'угу', 'ой', 'ах', 'эх', 'ого',
    'короче', 'типа', 'прям', 'просто', 'вообще', 'блин', 'чё', 'чо',
    'лол', 'кек', 'хаха', 'хех', 'хм', 'эм', 'м', 'хмм',
    'https', 'http', 'com', 'ru', 'www',
}


def extract_topics(messages, top_n=3):
    """Extract top topics from messages by finding frequent words."""
    word_counts = Counter()
    for text in messages:
        # Clean text: lowercase, remove non-alpha
        words = re.findall(r'[а-яёa-z]{4,}', text.lower())
        for word in words:
            if word not in STOP_WORDS and len(word) >= 4:
                word_counts[word] += 1
    return [word for word, _ in word_counts.most_common(top_n)]


def detect_mood(messages, total_messages, total_actions):
    """Detect the mood/character of the day."""
    text_all = ' '.join(messages).lower()

    sleep_words = sum(1 for w in ['спать', 'устал', 'сон', 'засып', 'сплю', 'хочу спать'] if w in text_all)
    food_words = sum(1 for w in ['есть', 'еда', 'кушать', 'голодн', 'обед', 'ужин', 'завтрак'] if w in text_all)
    work_words = sum(1 for w in ['работ', 'задач', 'проект', 'дедлайн', 'код', 'баг'] if w in text_all)

    if total_messages <= 3:
        return random.choice(["Тихий день — почти штиль", "Сегодня было тихо", "День прошёл в тишине"])
    elif total_actions >= total_messages * 0.3:
        return random.choice(["Активный день — много действий!", "Сегодня было жарко", "Бурный день!"])
    elif sleep_words >= 2:
        return random.choice(["Уставший день", "Сегодня все хотели спать", "Сонный денёк"])
    elif food_words >= 2:
        return random.choice(["Сытый день", "Сегодня обсуждали еду", "Гастрономический день"])
    elif work_words >= 2:
        return random.choice(["Рабочий день", "Сегодня говорили о делах", "Деловой день"])
    elif total_messages >= 50:
        return random.choice(["Очень активный день!", "Чат просто горел!", "Невероятно болтливый день"])
    elif total_messages >= 20:
        return random.choice(["Неплохой день", "Живой день", "Оживлённый денёк"])
    else:
        return random.choice(["Спокойный день", "Обычный денёк", "Тихий, но тёплый день"])


def _user_name(user):
    """Get display name for user."""
    return f"@{user['username']}" if user['username'] else f"id:{user['user_id']}"


# Templates for /summarize output
SUMMARY_TEMPLATES = [
    # Template 1
    lambda data: (
        f"📊 Итоги дня\n\n"
        f"{data['mood']}.\n\n"
        f"{'Сегодня было ' + str(data['total']) + ' сообщений.' if data['total'] > 0 else 'Сегодня было тихо.'}\n"
        f"{_summary_users(data)}"
        f"{_summary_rp(data)}"
        f"{_summary_topics(data)}"
    ),
    # Template 2
    lambda data: (
        f"📋 Дневной отчёт\n\n"
        f"{data['mood']} — {data['total']} сообщений.\n\n"
        f"{_summary_users(data)}"
        f"{_summary_rp(data)}"
        f"{_summary_topics(data)}"
    ),
    # Template 3
    lambda data: (
        f"🐰 Итоги\n\n"
        f"{_summary_users(data)}"
        f"Всего: {data['total']} сообщений. {data['mood']}.\n\n"
        f"{_summary_rp(data)}"
        f"{_summary_topics(data)}"
    ),
]


def _summary_users(data):
    """Format top users section."""
    if not data['top_users']:
        return ""
    lines = []
    top = data['top_users']
    if len(top) >= 3:
        lines.append(f"Больше всех писали {_user_name(top[0])}, {_user_name(top[1])} и {_user_name(top[2])}.")
    elif len(top) == 2:
        lines.append(f"Больше всех писали {_user_name(top[0])} и {_user_name(top[1])}.")
    else:
        lines.append(f"Больше всех писал {_user_name(top[0])}.")
    return '\n'.join(lines) + '\n'


def _summary_rp(data):
    """Format RP actions section."""
    parts = []
    if data['kiss_top']:
        parts.append(f"{_user_name(data['kiss_top'])} сегодня был самым романтичным 💋")
    if data['slap_top']:
        parts.append(f"{_user_name(data['slap_top'])} явно не сдерживался 👋")
    if parts:
        return '\n' + '\n'.join(parts) + '\n'
    return ''


def _summary_topics(data):
    """Format topics section."""
    if not data['topics']:
        return ""
    return f"\nЧаще всего обсуждали: {', '.join(data['topics'])}."


def summarize_command(update, context):
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

    # Gather data
    today_top = activity_manager.get_today_top(limit=5)
    if not today_top:
        update.message.reply_text("📊 Сегодня пока тихо... Никто ничего не написал.")
        return

    total = sum(u['today_count'] for u in today_top)
    kiss_top_list = activity_manager.get_kiss_top_today(limit=1)
    slap_top_list = activity_manager.get_slap_top_today(limit=1)
    total_actions = sum(u['kiss_count_today'] + u['slap_count_today'] for u in today_top)

    # Get messages for topic extraction
    messages = activity_manager.get_today_messages()
    topics = extract_topics(messages)
    mood = detect_mood(messages, total, total_actions)

    # Build data dict
    data = {
        'total': total,
        'top_users': today_top[:3],
        'kiss_top': kiss_top_list[0] if kiss_top_list else None,
        'slap_top': slap_top_list[0] if slap_top_list else None,
        'topics': topics,
        'mood': mood,
    }

    # Pick random template
    template = random.choice(SUMMARY_TEMPLATES)
    result = template(data)

    update.message.reply_text(result.strip())


def update_command(update, context):
    """Check for updates and apply if available."""
    try:
        from bot.services.auto_update import check_and_apply_update, get_current_version, restart_application

        current = get_current_version()
        update.message.reply_text(f"🔄 Проверяю обновления... (текущая: v{current})")

        updated, msg = check_and_apply_update(force=True)

        if updated:
            update.message.reply_text(f"✅ {msg}\nПерезапускаюсь...")
            # Give time for the message to be sent
            import threading
            def delayed_restart():
                import time
                time.sleep(2)
                restart_application()
            threading.Thread(target=delayed_restart, daemon=True).start()
        else:
            update.message.reply_text(f"ℹ️ {msg}")

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка при обновлении: {e}")