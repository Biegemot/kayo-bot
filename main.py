#!/usr/bin/env python3
"""
Main entry point for the Кайо (Kayo) Telegram bot.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Determine base directory (works with PyInstaller .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# Load environment variables from .env file next to executable/script
load_dotenv(BASE_DIR / '.env')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
    logger.error(f"Looked for .env in: {BASE_DIR / '.env'}")
    sys.exit(1)

# Version constant
try:
    from version import get_current_version
except ImportError:
    def get_current_version():
        return "dev"

# Import handlers
from bot.handlers.hug import hug_command
from bot.handlers.bite import bite_command
from bot.handlers.pat import pat_command
from bot.handlers.boop import boop_command
from bot.handlers.kiss import kiss_command
from bot.handlers.slappass import slapass_command
from bot.handlers.general import about_command, help_command, top_command, today_command, me_command, titles_command
from bot.handlers.reactions import get_reaction
from bot.services.db_manager import DBManager
from bot.services.auto_update import setup_auto_update

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я Кайо, твой дружелюбный пушистый кролик-бот. "
        "Используй /help, чтобы увидеть, что я могу."
    )

async def help_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
    Доступные команды:
    /start - Запустить бота
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
    await update.message.reply_text(help_text.strip())

async def about_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send info about the bot and its version."""
    version = get_current_version() # использовать новую функцию вместо get_version()
    bot_username = context.bot.username if context.bot else "unknown"
    about_text = f"""
🐰 Кайо (Kayo) Telegram Бот

Версия: {version}
Имя пользователя бота: @{bot_username}

Дружелюбный пушистый кролик-бот, который отслеживает активность и реагирует на сообщения.

👤 Creator: SkyFox
"""
    await update.message.reply_text(about_text.strip())



async def combined_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages to increment activity count and trigger reactions."""
    # Get DB manager from bot_data
    db_manager = context.application.bot_data.get('db_manager')
    if db_manager:
        chat = update.effective_chat
        user = update.effective_user
        if chat and user:
            # Get activity manager for this chat
            activity_manager = db_manager.get_activity_manager(chat.id)
            activity_manager.increment_message(user.id, user.username or user.first_name or "")
    
    # Handle reactions to text messages
    text = update.message.text
    if text:
        user_mention = update.effective_user.mention_html() if update.effective_user else ""
        reaction = get_reaction(text, user_mention)
        if reaction:
            await update.message.reply_text(reaction)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Create and store DB manager
    db_manager = DBManager()
    application.bot_data['db_manager'] = db_manager

    # Setup auto-update
    setup_auto_update(application)

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command_wrapper))
    application.add_handler(CommandHandler("about", about_command_wrapper))
    application.add_handler(CommandHandler("hug", hug_command))
    application.add_handler(CommandHandler("bite", bite_command))
    application.add_handler(CommandHandler("pat", pat_command))
    application.add_handler(CommandHandler("boop", boop_command))
    application.add_handler(CommandHandler("kiss", kiss_command))
    application.add_handler(CommandHandler("slapass", slapass_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(CommandHandler("titles", titles_command))

    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, combined_message_handler))

    # Run the bot until the user presses Ctrl-C
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start the bot: {e}")
        logger.error("Please check your TELEGRAM_BOT_TOKEN and network connection.")
        exit(1)

if __name__ == '__main__':
    main()