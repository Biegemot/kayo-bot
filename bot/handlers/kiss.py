"""Handle the /kiss command."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.rp_utils import rp_command_handler

KISS_PHRASES = [
    "нежно поцеловал в щёчку",
    "страстно поцеловал в губы",
    "быстро чмокнул в слёзку",
    "нежно поцеловал в лобик",
    "страстно поцеловал в шею",
    "быстро чмокнул в носик",
    "нежно поцеловал в ручку",
]


async def kiss_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /kiss command."""
    await rp_command_handler(update, context, KISS_PHRASES, increment_callback=lambda am, uid: am.increment_kiss(uid))
