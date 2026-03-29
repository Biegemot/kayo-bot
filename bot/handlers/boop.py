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
    
    # List of boop phrases in Russian
    boop_phrases = [
        '<i>Вы босиком тычете {} в нос</i>',
        '<i>Вы тычете {} в кнопку</i>',
        '<i>Вы игриво тычете {} в носик</i>',
        '<i>Вы тычете {} своей пушистой лапкой</i>',
        '<i>Вы нежно тычете {} в носик</i>',
        '<i>Вы ласково тычете {} в носик</i>',
        '<i>Вы тычете {} в мордочку</i>',
        '<i>Вы мило тычете {} в носик</i>'
    ]
    
    phrase = random.choice(boop_phrases)
    reply_text = phrase.format(mentioned_user)
    
    # Send the reply
    update.message.reply_text(reply_text, parse_mode='HTML')