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
        mentioned_user = user.mention_html() if user else "someone"
    elif not mentioned_user.startswith('@'):
        # If it's not already a mention, make it one
        mentioned_user = f"@{mentioned_user}"
    
    # List of bite phrases
    bite_phrases = [
        "playfully nips",
        "gives a gentle bite",
        "nibbles on ear",
        "playfully bites",
        "gives a love bite",
        "softly chomps",
        "gives a tiny nibble",
        "playfully munches"
    ]
    
    phrase = random.choice(bite_phrases)
    reply_text = f"{mentioned_user} {phrase}!"
    
    # Send the reply
    update.message.reply_text(reply_text, parse_mode='HTML')