import random
from telegram import Update
from telegram.ext import ContextTypes

def hug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /hug command."""
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
    
    # List of hug phrases in Russian
    hug_phrases = [
        '<i>Вы обняли {}</i>',
        '<i>Вы тепло обняли {}</i>',
        '<i>Вы крепко обняли {}</i>',
        '<i>Вы нежно обняли {}</i>',
        '<i>Вы обняли {} и прижались</i>',
        '<i>Вы ласково обняли {}</i>',
        '<i>Вы обняли {} и слегка сжали</i>'
    ]
    
    phrase = random.choice(hug_phrases)
    reply_text = phrase.format(mentioned_user)
    
    # Send the reply
    update.message.reply_text(reply_text, parse_mode='HTML')