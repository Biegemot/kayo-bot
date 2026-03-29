#!/usr/bin/env python3
"""
Main entry point for the Кайо (Kayo) Telegram bot.
"""
import os
import logging
import subprocess
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables from .env file
load_dotenv()

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
    exit(1)

def get_version():
    """Get the current version from git tags."""
    try:
        # Run git describe --tags --abbrev=0
        version = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], 
                                          stderr=subprocess.DEVNULL,
                                          universal_newlines=True).strip()
        return version
    except Exception:
        return "dev"

# Import handlers
from bot.handlers.hug import hug_command
from bot.handlers.bite import bite_command
from bot.handlers.pat import pat_command
from bot.handlers.boop import boop_command
from bot.handlers.general import about_command, help_command, top_command, today_command, me_command
from bot.handlers.reactions import get_reaction
from bot.services.db_manager import DBManager
from bot.services.auto_update import setup_auto_update

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm Кайо, your friendly furry bunny bot. "
        "Use /help to see what I can do."
    )

async def help_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this help message
    /about - Info about the bot and version
    /hug [user] - Hug a user (or yourself if no user mentioned)
    /bite [user] - Playfully bite a user
    /pat [user] - Pat a user affectionately
    /boop [user] - Boop a user's nose
    /top - See top users by total message count
    /today - See top users by today's message count
    /me - See your own stats and title
    """
    await update.message.reply_text(help_text.strip())

async def about_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send info about the bot and its version."""
    version = get_version()
    bot_username = context.bot.username if context.bot else "unknown"
    
    about_text = f"""
    🐰 Кайо (Kayo) Telegram Bot
    Version: {version}
    Bot Username: @{bot_username}
    
    A friendly furry bunny bot that tracks activity and reacts to messages.
    """
    await update.message.reply_text(about_text.strip())



async def increment_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages to increment activity count."""
    # Get DB manager from bot_data
    db_manager = context.application.bot_data.get('db_manager')
    if db_manager:
        chat = update.effective_chat
        user = update.effective_user
        if chat and user:
            # Get activity manager for this chat
            activity_manager = db_manager.get_activity_manager(chat.id)
            activity_manager.increment_message(user.id, user.username or user.first_name or "")

async def reactions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reactions to text messages."""
    # Get the text of the message
    text = update.message.text
    if text:
        # 10-20% chance to trigger a reaction (using 15%)
        import random
        if random.random() < 0.15:
            reaction = get_reaction(text)
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
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("me", me_command))

    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, increment_message_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reactions_handler))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()