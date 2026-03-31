"""Handle the /hug command."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.rp_utils import rp_command_handler

HUG_PHRASES = [
    "обнял",
    "тепло обнял",
    "крепко обнял",
    "нежно обнял",
    "обнял и прижался",
    "ласково обнял",
    "обнял и слегка сжал",
]


async def hug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /hug command."""
    await rp_command_handler(update, context, HUG_PHRASES, increment_callback=lambda am, uid: am.increment_hug(uid))
