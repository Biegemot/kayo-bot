"""Handle the /slapass command."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.rp_utils import rp_command_handler

SLAPASS_PHRASES = [
    "шлёпнул и довольно фыркнул",
    "шлёпнул и засмеялся",
    "шлёпнул и подмигнул",
    "шлёпнул и отпрыгнул назад",
    "шлёпнул и сказал: 'Не балуйся!'",
    "шлёпнул и погладил место шлепка",
    "шлёпнул и ушёл смеяться",
]


def slapass_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /slapass command."""
    rp_command_handler(update, context, SLAPASS_PHRASES, increment_callback=lambda am, uid: am.increment_slap(uid))
