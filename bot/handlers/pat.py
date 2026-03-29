import random
from telegram import Update
from telegram.ext import ContextTypes

def pat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /pat command."""
    # Extract mentioned user
    mentioned_user = None
    
    # Check if there are command arguments
    if context.args:
        mentioned_user = ' '.join(context.args)
        if not mentioned_user.startswith('@'):
            mentioned_user = f"@{mentioned_user}"
    else:
        # Check entities for mentions
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == 'mention':
                    # Extract the mention text
                    mentioned_user = update.message.text[entity.offset:entity.offset+entity.length]
                    break
        # If no user mentioned, default to self
        if not mentioned_user:
            mentioned_user = "себя"
    
    # List of pat phrases in Russian
    pat_phrases = [
        '<i>Вы нежно гладите {} по голове</i>',
        '<i>Вы дружелюбно похлопали {} по плечу</i>',
        '<i>Вы мягко погладили {}</i>',
        '<i>Вы поддерживающе похлопали {} по спине</i>',
        '<i>Вы погладили {} своими руками</i>',
        '<i>Вы утешающе погладили {}</i>',
        '<i>Вы ласково погладили {}</i>',
        '<i>Вы игриво похлопали {} по плечу</i>'
    ]
    
    phrase = random.choice(pat_phrases)
    reply_text = phrase.format(mentioned_user)
    
    # Send the reply
    update.message.reply_text(reply_text, parse_mode='HTML')