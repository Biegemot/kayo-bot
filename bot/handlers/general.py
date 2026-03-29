from telegram import Update
from telegram.ext import ContextTypes
from bot.services.activity import ActivityManager

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
    🐰 Кайо (Kayo) Telegram Bot
    Version: {version}
    Bot Username: @{bot_username}
    
    A friendly furry bunny bot that tracks activity and reacts to messages.
    """
    update.message.reply_text(about_text.strip())

def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a list of available commands with descriptions."""
    help_text = """
    Available commands:
    /start - Start the bot and see welcome message
    /help - Show this help message
    /about - Info about the bot and version
    /hug [user] - Hug a user (or yourself if no user mentioned)
    /bite [user] - Playfully bite a user
    /pat [user] - Pat a user affectionately
    /boop [user] - Boop a user's nose
    /top - See top users by total message count
    /today - See top users by today's message count
    /me - See your own stats and title
    /remind - Set a reminder (stub)
    /backup - Backup data (stub)
    """
    update.message.reply_text(help_text.strip())

def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top users by total message count."""
    activity_manager = context.application.bot_data.get('activity_manager')
    if not activity_manager:
        update.message.reply_text("Sorry, activity tracking is not available.")
        return
    
    top_users = activity_manager.get_top(limit=10)
    if not top_users:
        update.message.reply_text("No activity data yet.")
        return
    
    message = "🏆 Top Users by Total Messages:\n\n"
    for i, user in enumerate(top_users, 1):
        message += f"{i}. {user['username'] or user['user_id']}: {user['message_count']} messages\n"
    
    update.message.reply_text(message)

def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top users by today's message count."""
    activity_manager = context.application.bot_data.get('activity_manager')
    if not activity_manager:
        update.message.reply_text("Sorry, activity tracking is not available.")
        return
    
    top_users = activity_manager.get_today_top(limit=10)
    if not top_users:
        update.message.reply_text("No activity data for today yet.")
        return
    
    message = "📅 Top Users Today:\n\n"
    for i, user in enumerate(top_users, 1):
        message += f"{i}. {user['username'] or user['user_id']}: {user['today_count']} messages today\n"
    
    update.message.reply_text(message)

def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show your own stats and title."""
    activity_manager = context.application.bot_data.get('activity_manager')
    if not activity_manager:
        update.message.reply_text("Sorry, activity tracking is not available.")
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Unknown"
    
    stats = activity_manager.get_user_stats(user_id)
    if not stats:
        update.message.reply_text("No stats found for you yet. Start chatting!")
        return
    
    title = activity_manager.get_dynamic_title(user_id)
    
    message = f"""
    👤 Your Stats:
    User ID: {user_id}
    Username: @{username}
    Total Messages: {stats['message_count']}
    Today's Messages: {stats['today_count']}
    Title: {title}
    """
    update.message.reply_text(message.strip())