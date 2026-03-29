import random
from telegram import Update
from telegram.ext import ContextTypes

def pat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /pat command."""
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
    
    # List of pat phrases in Russian (action initiated by initiator on target)
    pat_phrases = [
        "нежно погладил по голове",
        "дружелюбно похлопал по плечу",
        "мягко погладил",
        "поддерживающе похлопал по спине",
        "погладил своими руками",
        "утешающе погладил",
        "ласково погладил",
        "игриво похлопал по плечу"
    ]
    
    phrase = random.choice(pat_phrases)
    # Format: @initiator действие @target
    reply_text = f"{initiator_mention} {phrase} {target_user}"
    
    # Send the reply
    update.message.reply_text(reply_text)