#!/usr/bin/env python3
"""
Main entry point for the Кайо (Kayo) Telegram bot.
On Windows .exe: launches GUI by default, use --run-bot to run bot directly.
On Linux / dev mode: runs bot directly.
"""
import os
import sys
import random
import logging
from pathlib import Path
from dotenv import load_dotenv

# Determine base directory (works with PyInstaller .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# Load environment variables from .env file next to executable/script
load_dotenv(BASE_DIR / '.env')

# Windows .exe: launch GUI unless --run-bot flag is passed
if __name__ == '__main__' and getattr(sys, 'frozen', False) and '--run-bot' not in sys.argv:
    from bot.gui import main as gui_main
    gui_main()
    sys.exit(0)

# Normal bot startup continues below
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Импортируем продвинутую систему логирования
from bot.logging import setup_logging, log_function_call

# Настраиваем логирование
logger = setup_logging()

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
from bot.handlers.slapass import slapass_command
from bot.handlers.general import top_command, today_command, titles_command, summarize_command, update_command
from bot.handlers.reactions import get_reaction
from bot.services.db_manager import DBManager
from bot.services.auto_update import setup_auto_update

# Define command handlers
@log_function_call
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.log_command("start", user.id, update.effective_chat.id if update.effective_chat else 0)
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я Кайо, твой дружелюбный пушистый кролик-бот. "
        "Используй /help, чтобы увидеть, что я могу."
    )

@log_function_call
async def help_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user = update.effective_user
    logger.log_command("help", user.id, update.effective_chat.id if update.effective_chat else 0)
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
    /summarize - Итоги дня с темами и настроением чата
    /update - Проверить и установить обновления
    """
    await update.message.reply_text(help_text.strip())

@log_function_call
async def about_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send info about the bot and its version."""
    user = update.effective_user
    logger.log_command("about", user.id, update.effective_chat.id if update.effective_chat else 0)
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

@log_function_call
async def chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bot being added to or removed from a group."""
    result = update.my_chat_member
    if not result:
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    # Bot was added to a group (member or administrator)
    if new_status in ('member', 'administrator') and old_status in ('left', 'kicked'):
        chat = update.effective_chat
        if chat and chat.type in ('group', 'supergroup'):
            logger.log_event("bot_added_to_group", chat_id=chat.id, chat_title=chat.title)
            welcome = (
                "🐰 Привет! Я Кайо, ваш дружелюбный пушистый кролик-бот!\n\n"
                "Вот что я умею:\n"
                "• Отслеживаю активность чата 📊\n"
                "• Реагирую на сообщения (попробуйте написать \"хочу спать\" 😴)\n"
                "• Умею обнимать, кусать, целовать и шлёпать! /help\n"
                "• Показываю топ активных и итоги дня /summarize\n\n"
                "Используйте /help чтобы увидеть все команды. Приятного общения! 🐾"
            )
            try:
                await context.bot.send_message(chat_id=chat.id, text=welcome)
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")

    # Bot was removed from group
    elif new_status in ('left', 'kicked'):
        logger.log_event("bot_removed_from_group", chat_id=update.effective_chat.id if update.effective_chat else 0)
        # Could clean up DB here if needed
        pass

@log_function_call
async def combined_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages to increment activity count and trigger reactions."""
    # Log handler activation
    logger.debug(f"Message handler triggered", 
                 update_type=type(update).__name__,
                 has_message=update.message is not None)
    
    # Check if message exists
    if not update.message or not update.message.text:
        logger.debug("Message check failed - no message or text")
        return
    
    # Get chat and user info
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        logger.warning("Chat or user is None", chat_id=chat.id if chat else None, user_id=user.id if user else None)
        return
    
    # Log message details
    logger.info(f"Message received",
                chat_id=chat.id,
                user_id=user.id,
                username=user.username,
                message_length=len(update.message.text))
    
    # Update activity in database
    db_manager = context.application.bot_data.get('db_manager')
    if db_manager:
        try:
            activity_manager = db_manager.get_activity_manager(chat.id)
            activity_manager.increment_message(user.id, user.username or user.first_name or "")
            # Store message text for topic extraction
            activity_manager.store_message(user.id, update.message.text)
            logger.debug("Activity updated in database",
                         chat_id=chat.id, user_id=user.id)
        except Exception as e:
            logger.error(f"Failed to update activity: {e}",
                         chat_id=chat.id, user_id=user.id)
    else:
        logger.warning("db_manager is None", chat_id=chat.id)

    # Handle reactions
    text = update.message.text
    user_mention = update.effective_user.mention_html() if update.effective_user else ""
    reaction = get_reaction(text, user_mention)
    if reaction:
        # Random chance to react (15%)
        if random.random() < 0.15:
            logger.info("Sending reaction", 
                        reaction_type="auto_reaction",
                        user_id=user.id,
                        chat_id=chat.id)
            await update.message.reply_html(reaction)

@log_function_call
def main() -> None:
    """Start the bot."""
    logger.info("Starting Kayo Bot", version=get_current_version())
    
    # Create the Application and pass it your bot's token.
    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        logger.info("Telegram application created successfully")
    except Exception as e:
        logger.error(f"Failed to create Telegram application: {e}")
        sys.exit(1)

    # Create and store DB manager
    try:
        db_manager = DBManager()
        application.bot_data['db_manager'] = db_manager
        logger.info("Database manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database manager: {e}")
        sys.exit(1)

    # Setup auto-update
    try:
        setup_auto_update(application)
        logger.info("Auto-update system configured")
    except Exception as e:
        logger.warning(f"Failed to setup auto-update: {e}")

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
    # /me команда теперь обрабатывается в bot/handlers/profile.py
    application.add_handler(CommandHandler("titles", titles_command))
    application.add_handler(CommandHandler("summarize", summarize_command))
    application.add_handler(CommandHandler("update", update_command))

    # Register profile handlers
    try:
        from bot.handlers.profile import register_profile_handlers
        register_profile_handlers(application)
        logger.info("Profile handlers registered")
    except Exception as e:
        logger.error(f"Failed to register profile handlers: {e}")
    
    # Register webapp handlers
    try:
        from bot.handlers.webapp import register_webapp_handlers
        register_webapp_handlers(application)
        logger.info("WebApp handlers registered")
    except Exception as e:
        logger.error(f"Failed to register webapp handlers: {e}")
    
    # Register stats handlers
    try:
        from bot.handlers.stats import register_stats_handlers
        register_stats_handlers(application)
        logger.info("Stats handlers registered")
    except Exception as e:
        logger.error(f"Failed to register stats handlers: {e}")

    # Register message and chat member handlers
    # Обрабатываем все текстовые сообщения, включая команды
    application.add_handler(MessageHandler(filters.TEXT, combined_message_handler))
    from telegram.ext import ChatMemberHandler
    application.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))

    # Register commands in Telegram menu
    from telegram import BotCommand
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("help", "Список команд"),
        BotCommand("about", "Информация о боте"),
        BotCommand("hug", "Обнять пользователя"),
        BotCommand("bite", "Укусить пользователя"),
        BotCommand("pat", "Погладить пользователя"),
        BotCommand("boop", "Ткнуть в нос"),
        BotCommand("kiss", "Поцеловать пользователя"),
        BotCommand("slapass", "Шлёпнуть пользователя"),
        BotCommand("top", "Топ по сообщениям"),
        BotCommand("today", "Активность за сегодня"),
        BotCommand("me", "Моя анкета"),
        BotCommand("stats", "Моя статистика"),
        BotCommand("webapp", "Открыть Mini-App для анкеты"),
        BotCommand("titles", "Список титулов"),
        BotCommand("summarize", "Итоги дня"),
        BotCommand("update", "Проверить обновления"),
    ]

    @log_function_call
    async def post_init(app):
        await app.bot.set_my_commands(commands)
        logger.info("Bot commands registered in Telegram menu")

    application.post_init = post_init

    # Add error handler
    @log_function_call
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors."""
        logger.error(f"Exception while handling an update: {context.error}",
                     error_type=type(context.error).__name__,
                     update=str(update),
                     exc_info=True)
    
    application.add_error_handler(error_handler)
    
    # Add a handler to log ALL updates (for debugging)
    @log_function_call
    async def log_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log all incoming updates."""
        logger.debug(f"Received update",
                     update_type=type(update).__name__,
                     has_message=update.message is not None)
        if update.message:
            logger.debug(f"Message details",
                         chat_id=update.message.chat.id if update.message.chat else None,
                         message_type=update.message.chat.type if update.message.chat else None)
    
    # This will be called before any other handler
    application.add_handler(MessageHandler(filters.ALL, log_all_updates), group=-1)

    # Run the bot until the user presses Ctrl-C
    try:
        logger.info("Starting bot polling...")
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.critical(f"Failed to start the bot: {e}", exc_info=True)
        logger.critical("Please check your TELEGRAM_BOT_TOKEN and network connection.")
        sys.exit(1)

if __name__ == '__main__':
    main()