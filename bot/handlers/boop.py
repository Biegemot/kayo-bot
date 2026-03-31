"""Handle the /boop command."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.rp_utils import rp_command_handler

BOOP_PHRASES = [
    "босиком ткнул в нос",
    "ткнул в кнопку",
    "игриво ткнул в носик",
    "ткнул своей пушистой лапкой",
    "нежно ткнул в носик",
    "ласково ткнул в носик",
    "ткнул в мордочку",
    "мило ткнул в носик",
]


def boop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /boop command."""
    rp_command_handler(update, context, BOOP_PHRASES, increment_callback=lambda am, uid: am.increment_boop(uid))
