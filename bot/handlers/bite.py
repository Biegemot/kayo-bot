import random
from telegram import Update
from telegram.ext import ContextTypes

def bite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /bite command."""
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
    
    # List of bite phrases in Russian
    bite_phrases = [
        '<i>Вы кусаете {}</i>',
        '<i>Вы нежно кусаете {}</i>',
        '<i>Вы кусаете {} за ушко</i>',
        '<i>Вы игриво кусаете {}</i>',
        '<i>Вы любовно кусаете {}</i>',
        '<i>Вы слегка прикусываете {}</i>',
        '<i>Вы нежно покусываете {}</i>',
        '<i>Вы играючи кусаете {}</i>'
    ]
    
    phrase = random.choice(bite_phrases)
    reply_text = phrase.format(mentioned_user)
    
    # Send the reply
    update.message.reply_text(reply_text, parse_mode='HTML')