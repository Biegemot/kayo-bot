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
    
    # List of hug phrases in Russian
    hug_phrases = [
        '<i>Кайо обнял {} и прижался носом</i>',
        '<i>Кайо нежно обнял {}</i>',
        '<i>Кайо прижался к {} пушистым ухом</i>',
        '<i>Кайо крепко обнял {} и заурчал</i>',
        '<i>Кайо ласково обнял {}</i>',
        '<i>Кайо нежно притянул {} к себе</i>',
        '<i>Кайо обнял {} и уткнулся носом в плечо</i>'
    ]
    
    phrase = random.choice(hug_phrases)
    reply_text = phrase.format(mentioned_user)
    
    # Send the reply
    update.message.reply_text(reply_text, parse_mode='HTML')