#!/usr/bin/env python3
"""
Main entry point for the Кайо (Kayo) Telegram bot.
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

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

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm Кайо, your friendly furry bunny bot. "
        "Use /help to see what I can do."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this help message
    /remind - Set a reminder (stub)
    /backup - Backup data (stub)
    """
    await update.message.reply_text(help_text)

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stub for /remind command."""
    await update.message.reply_text("Reminder feature is not implemented yet.")

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stub for /backup command."""
    await update.message.reply_text("Backup feature is not implemented yet.")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("remind", remind))
    application.add_handler(CommandHandler("backup", backup))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()