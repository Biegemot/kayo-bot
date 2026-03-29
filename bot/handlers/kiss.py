import random
from telegram import Update
from telegram.ext import ContextTypes

def kiss_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /kiss command."""
    # Get the initiator (user who sent the command)
    initiator = update.effective_user
    initiator_name = initiator.username or initiator.first_name or ""
    if initiator_name:
        initiator_mention = f"@{initiator_name}"
    else:
        initiator_mention = initiator.first_name or "пользователь"
    
    # Extract mentioned user (target)
    target_user = None
    if context.args:
        target_user = ' '.join(context.args)
        if not target_user.startswith('@'):
            target_user = f"@{target_user}"
    else:
        # Check entities for mentions
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == 'mention':
                    # Extract the mention text
                    target_user = update.message.text[entity.offset:entity.offset+entity.length]
                    break
        # If no user mentioned, default to self
        if not target_user:
            target_user = initiator_mention  # self
    
    # List of kiss phrases in Russian
    kiss_phrases = [
        "нежно поцеловал в щёчку",
        "страстно поцеловал в губы",
        "быстро чмокнул в слёзку",
        "нежно поцеловал в лобик",
        "страстно поцеловал в шею",
        "быстро чмокнул в носик",
        "нежно поцеловал в ручку"
    ]
    
    phrase = random.choice(kiss_phrases)
    # Format: @initiator действие @target
    reply_text = f"{initiator_mention} {phrase} {target_user}"
    
    # Increment kiss count for initiator
    db_manager = context.application.bot_data.get('db_manager')
    if db_manager:
        chat = update.effective_chat
        if chat:
            activity_manager = db_manager.get_activity_manager(chat.id)
            activity_manager.increment_kiss(initiator.id)
    
    # Send the reply
    update.message.reply_text(reply_text)