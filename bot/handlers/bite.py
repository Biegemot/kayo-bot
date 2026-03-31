"""Handle the /bite command."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.rp_utils import rp_command_handler

BITE_PHRASES = [
    "кусает",
    "нежно кусает",
    "кусает за ушко",
    "игриво кусает",
    "любовно кусает",
    "слегка прикусывает",
    "нежно покусывает",
    "играючи кусает",
]


def bite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /bite command."""
    rp_command_handler(update, context, BITE_PHRASES, increment_callback=lambda am, uid: am.increment_bite(uid))
