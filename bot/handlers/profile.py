# Обновлённый обработчик профиля `/me`
# Без WebApp — всё inline, с автоудалением сообщений

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────
# Profile fields
# ──────────────────────────────────────────────────────
PROFILE_FIELDS = [
    "fursona_name",
    "species",
    "birth_date",
    "age",
    "orientation",
    "city",
    "looking_for",
    "personality_type",
    "reference_photo",
]

FIELD_LABELS = {
    "fursona_name": "Имя фурсоны",
    "species": "Вид",
    "birth_date": "Дата рождения",
    "age": "Возраст",
    "orientation": "Ориентация",
    "city": "Город",
    "looking_for": "Ищу",
    "personality_type": "Тип личности",
    "reference_photo": "Референс (фото)",
}

# Группа для profile handlers — выше приоритет, чем у combined_message_handler
PROFILE_HANDLER_GROUP = 1


# ──────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────
def _get_profile(user_id, chat_data):
    """Load profile dict from chat_data for a user."""
    return chat_data.setdefault("profiles", {}).setdefault(user_id, {})


def _build_profile_keyboard(profile: dict, editable: bool = True):
    """Build inline keyboard for profile. If editable=False, show read-only view."""
    rows = []
    for f in PROFILE_FIELDS:
        label = FIELD_LABELS[f]
        value = profile.get(f, "Не задано")
        if f == "reference_photo":
            value = "📷 Установлено" if value else "Не задано"
        
        if editable:
            # Editable version - clickable buttons
            rows.append(
                [InlineKeyboardButton(f"{label}: {value}", callback_data=f"prof_edit_{f}")]
            )
        else:
            # Read-only version - just text (no callback)
            rows.append(
                [InlineKeyboardButton(f"{label}: {value}", callback_data="prof_noop")]
            )
    
    if editable:
        rows.append(
            [
                InlineKeyboardButton("✅ Готово", callback_data="prof_done"),
                InlineKeyboardButton("❌ Закрыть", callback_data="prof_close"),
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton("❌ Закрыть", callback_data="prof_close"),
            ]
        )
    return InlineKeyboardMarkup(rows)


async def _delete_safe(context: ContextTypes.DEFAULT_TYPE, chat_id, msg_id):
    """Delete a message without raising on failure."""
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        logger.debug("Could not delete message %s in %s", msg_id, chat_id)


# ──────────────────────────────────────────────────────
# Command handler: /me
# ──────────────────────────────────────────────────────
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show inline profile menu. Deletes the /me command message.
    
    Usage:
    /me - show and edit your own profile
    /me @username - view another user's profile (read-only)
    """
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if user wants to view another profile
    target_user_id = user_id
    target_username = None
    editable = True
    
    if context.args and len(context.args) > 0:
        # Extract username from arguments (remove @ if present)
        arg = context.args[0].lstrip('@')
        if arg and arg != str(user_id):
            # In real implementation, you would need to resolve username to user_id
            # For now, we'll show a placeholder message
            target_username = arg
            editable = False
    
    profile = _get_profile(target_user_id, context.chat_data)

    # Delete user command
    try:
        await context.bot.delete_message(
            chat_id=chat_id, message_id=update.effective_message.message_id
        )
    except Exception:
        pass
    
    # Prepare message text based on mode
    if editable:
        text = "🦊 *Твоя анкета*\n\nРедактируй поля кнопками ниже:"
    else:
        if target_username:
            text = f"👤 *Анкета пользователя @{target_username}*\n\n(режим просмотра)"
        else:
            text = "👤 *Анкета пользователя*\n\n(режим просмотра)"

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=_build_profile_keyboard(profile, editable=editable),
    )
    context.chat_data["profile_msg_id"] = msg.message_id
    context.chat_data["editing_field"] = None
    context.chat_data["profile_editable"] = editable


# ──────────────────────────────────────────────────────
# Inline callbacks
# ──────────────────────────────────────────────────────
async def prof_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to enter a new value for a specific field."""
    query = update.callback_query
    await query.answer()
    
    # Check if profile is editable (not in view-only mode)
    if not context.chat_data.get("profile_editable", True):
        await query.answer("Эта анкета доступна только для просмотра", show_alert=True)
        return
    
    chat_id = query.message.chat_id
    field = query.data.replace("prof_edit_", "")
    label = FIELD_LABELS.get(field, field)

    context.chat_data["editing_field"] = field
    context.chat_data["profile_msg_id"] = query.message.message_id

    if field == "reference_photo":
        prompt_text = f"📷 Отправь фото для *{label}*:"
    else:
        prompt_text = f"✏️ Введи новое значение для *{label}*:"

    prompt = await query.message.reply_text(
        prompt_text,
        parse_mode="Markdown",
    )
    context.chat_data["prompt_msg_id"] = prompt.message_id


async def prof_set_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user text/photo reply for the field being edited."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    field = context.chat_data.get("editing_field")

    # Если сейчас не редактируем — пропускаем (чтобы не конфликтовать с другими хендлерами)
    if field is None:
        return

    profile = _get_profile(user_id, context.chat_data)

    if field == "reference_photo":
        if update.message and update.message.photo:
            profile[field] = update.message.photo[-1].file_id
        else:
            await update.message.reply_text("📷 Отправь фото!")
            return
    else:
        profile[field] = update.message.text

    # Delete prompt + user reply
    prompt_id = context.chat_data.pop("prompt_msg_id", None)
    if prompt_id:
        await _delete_safe(context, chat_id, prompt_id)
    await _delete_safe(context, chat_id, update.message.message_id)

    context.chat_data["editing_field"] = None

    # Update profile message
    msg_id = context.chat_data.get("profile_msg_id")
    if msg_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text="🦊 *Твоя анкета*\n\nРедактируй поля кнопками ниже:",
            parse_mode="Markdown",
            reply_markup=_build_profile_keyboard(profile),
        )


async def prof_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete profile menu and clear state."""
    query = update.callback_query
    await query.answer("✅ Профиль сохранён!")
    msg_id = context.chat_data.pop("profile_msg_id", None)
    if msg_id:
        await _delete_safe(context, query.message.chat_id, msg_id)
    context.chat_data["editing_field"] = None


async def prof_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete profile menu without saving."""
    query = update.callback_query
    await query.answer()
    msg_id = context.chat_data.pop("profile_msg_id", None)
    if msg_id:
        await _delete_safe(context, query.message.chat_id, msg_id)
    context.chat_data["editing_field"] = None


async def prof_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to profile menu."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    profile = _get_profile(user_id, context.chat_data)
    context.chat_data["editing_field"] = None

    # Delete prompt if any
    prompt_id = context.chat_data.pop("prompt_msg_id", None)
    chat_id = query.message.chat_id
    if prompt_id:
        await _delete_safe(context, chat_id, prompt_id)

    await query.message.edit_text(
        "🦊 *Твоя анкета*\n\nРедактируй поля кнопками ниже:",
        parse_mode="Markdown",
        reply_markup=_build_profile_keyboard(profile),
    )


# ──────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────
def register_profile_handlers(application: Application):
    """Register all profile handlers on the given application."""
    application.add_handler(CommandHandler("me", profile_command))
    application.add_handler(CallbackQueryHandler(prof_edit_field, pattern="^prof_edit_.*$"))
    application.add_handler(CallbackQueryHandler(prof_done, pattern="^prof_done$"))
    application.add_handler(CallbackQueryHandler(prof_close, pattern="^prof_close$"))
    application.add_handler(CallbackQueryHandler(prof_back, pattern="^prof_back$"))
    # Catch text & photo replies for field editing (в отдельной группе, выше приоритет)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, prof_set_field),
        group=PROFILE_HANDLER_GROUP,
    )
    application.add_handler(
        MessageHandler(filters.PHOTO, prof_set_field),
        group=PROFILE_HANDLER_GROUP,
    )
