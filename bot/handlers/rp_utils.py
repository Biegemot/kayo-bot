"""
Shared utilities for RP command handlers.
Reduces code duplication across hug, bite, pat, boop, kiss, slapass.
"""
import random
from telegram import Update
from telegram.ext import ContextTypes


def get_initiator_mention(update: Update) -> str:
    """Get the @mention string for the user who sent the command."""
    user = update.effective_user
    name = user.username or user.first_name or ""
    if name:
        return f"@{name}"
    return user.first_name or "пользователь"


def get_target_mention(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """
    Extract target user mention from command arguments or message entities.
    Returns @username if mentioned, otherwise returns initiator's mention (self).
    """
    # Check command arguments first
    if context.args:
        target = ' '.join(context.args)
        if not target.startswith('@'):
            target = f"@{target}"
        return target

    # Check message entities for @mentions
    if update.message and update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'mention':
                return update.message.text[entity.offset:entity.offset + entity.length]

    # Default to self
    return get_initiator_mention(update)


def format_rp_action(initiator: str, phrase: str, target: str) -> str:
    """Format RP action as '@initiator действие @target'."""
    return f"{initiator} {phrase} {target}"


async def rp_command_handler(update, context, phrases, increment_callback=None):
    """
    Generic RP command handler.
    
    Args:
        update: Telegram update object
        context: Telegram context object
        phrases: List of possible action phrases
        increment_callback: Optional callback(activity_manager, user_id) to track action
    """
    initiator = get_initiator_mention(update)
    target = get_target_mention(update, context)
    phrase = random.choice(phrases)
    reply = format_rp_action(initiator, phrase, target)

    # Track action if callback provided
    if increment_callback:
        try:
            db_manager = context.application.bot_data.get('db_manager')
            if db_manager:
                chat = update.effective_chat
                if chat:
                    activity_manager = db_manager.get_activity_manager(chat.id)
                    increment_callback(activity_manager, update.effective_user.id)
        except Exception:
            pass  # Don't fail the command if tracking fails

    await update.message.reply_text(reply)
