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
    else:
        # Check entities for mentions
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == 'mention':
                    # Extract the mention text
                    mentioned_user = update.message.text[entity.offset:entity.offset+entity.length]
                    break
    
    # If no user mentioned, default to the sender
    if not mentioned_user:
        user = update.effective_user
        mentioned_user = user.mention_html() if user else "кого-то"
    elif not mentioned_user.startswith('@'):
        # If it's not already a mention, make it one
        mentioned_user = f"@{mentioned_user}"
    
    # List of pat phrases in Russian
    pat_phrases = [
        '<i>Кайо нежно гладит {} по голове</i>',
        '<i>Кайо дружелюбно похлопал {} по плечу</i>',
        '<i>Кайо мягко погладил {}</i>',
        '<i>Кайо поддерживающе похлопал {} по спине</i>',
        '<i>Кайо погладил {} своими пушистыми лапками</i>',
        '<i>Кайо утешающе погладил {}</i>',
        '<i>Кайо ласково погладил {}</i>',
        '<i>Кайо игриво похлопал {} по плечу</i>'
    ]
    
    phrase = random.choice(pat_phrases)
    reply_text = phrase.format(mentioned_user)
    
    # Send the reply
    update.message.reply_text(reply_text, parse_mode='HTML')