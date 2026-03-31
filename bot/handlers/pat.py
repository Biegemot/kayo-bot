"""Handle the /pat command."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.rp_utils import rp_command_handler

PAT_PHRASES = [
    "нежно погладил по голове",
    "дружелюбно похлопал по плечу",
    "мягко погладил",
    "поддерживающе похлопал по спине",
    "погладил своими руками",
    "утешающе погладил",
    "ласково погладил",
    "игриво похлопал по плечу",
]


def pat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /pat command."""
    rp_command_handler(update, context, PAT_PHRASES, increment_callback=lambda am, uid: am.increment_pat(uid))
