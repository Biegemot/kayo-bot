import random
from telegram import Update
from telegram.ext import ContextTypes

def boop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /boop command."""
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
    
    # List of boop phrases in Russian
    boop_phrases = [
        '<i>Кайо босиком тычет {} в нос</i>',
        '<i>Кайо тычет {} в кнопку</i>',
        '<i>Кайо игриво тычет {} в носик</i>',
        '<i>Кайо тычет {} своей пушистой лапкой</i>',
        '<i>Кайо нежно тычет {} в носик</i>',
        '<i>Кайо ласково тычет {} в носик</i>',
        '<i>Кайо тычет {} в мордочку</i>',
        '<i>Кайо мило тычет {} в носик</i>'
    ]
    
    phrase = random.choice(boop_phrases)
    reply_text = phrase.format(mentioned_user)
    
    # Send the reply
    update.message.reply_text(reply_text, parse_mode='HTML')