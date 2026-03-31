"""
Profile system for Kayo Bot
Allows users to create and manage their fursona profiles
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters

logger = logging.getLogger(__name__)

# Field labels for display
FIELD_LABELS = {
    'fursona_name': '🐾 Имя фурсоны',
    'species': '🦊 Вид',
    'birth_date': '🎂 Дата рождения',
    'age': '🔢 Возраст',
    'orientation': '💕 Ориентация',
    'city': '🏙️ Город',
    'looking_for': '🤝 Ищет',
    'personality_type': '🎭 Тип личности',
    'reference_photo': '🖼️ Референс'
}

# Field descriptions for input prompts
FIELD_PROMPTS = {
    'fursona_name': "Введите имя фурсоны:",
    'species': "Введите вид (например, лис, волк, кот, дракон):",
    'birth_date': "Введите дату рождения (ДД.ММ.ГГГГ):",
    'age': "Введите возраст:",
    'orientation': "Введите ориентацию (например, гетеро, гей, би, пан):",
    'city': "Введите город:",
    'looking_for': "Введите, кого ищете (например, друга, парня, девочку):",
    'reference_photo': "Отправьте фото референса или URL:"
}

# Personality types for inline selection
PERSONALITY_TYPES = [
    "Интроверт",
    "Экстраверт",
    "Амбиверт"
]


async def generate_profile_text(user, profile, stats, titles, rank, max_length=1024):
    """Generate profile text with length limit."""
    # Build profile text
    profile_text = ""
    if profile:
        for field, label in FIELD_LABELS.items():
            value = profile.get(field)
            if value:
                if field == 'reference_photo':
                    continue
                profile_text += f"{label}: {value}\n"
    
    # Build message
    text = f"👤 Анкета @{user.username or user.first_name}\n\n"
    
    if profile_text:
        text += profile_text + "\n"
    
    # Add stats
    stats_text = f"📊 Общее количество сообщений: {stats['message_count']}\n"
    stats_text += f"📅 Сообщения за сегодня: {stats['today_count']}\n"
    stats_text += f"💋 Поцелуев сегодня: {stats['kiss_count_today']}\n"
    stats_text += f"👋 Шлёпков сегодня: {stats['slap_count_today']}\n"
    stats_text += f"🏆 Позиция в рейтинге: {rank}\n"
    
    # Add all titles
    if titles:
        titles_str = ", ".join(titles)
        stats_text += f"🏅 Титулы: {titles_str}\n"
    else:
        stats_text += f"🏅 Титул: Активный\n"
    
    # Check length and truncate if needed
    if len(text) + len(stats_text) > max_length:
        # Calculate available space for stats
        available = max_length - len(text) - 50  # Reserve space for "..."
        if available > 0:
            stats_text = stats_text[:available] + "..."
        else:
            stats_text = "Статистика слишком длинная..."
    
    text += stats_text
    
    return text


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile and stats in chat."""
    user = update.effective_user
    user_id = user.id
    
    # Get activity manager from bot_data
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        await update.message.reply_text("Извините, система анкет недоступна.")
        return
    
    # Use user_id for profile (stored in user-specific database)
    # But use chat_id for stats (stored in chat-specific database)
    profile_activity_manager = db_manager.get_activity_manager(user_id)
    profile = profile_activity_manager.get_profile(user_id)
    
    # Use chat_id for stats
    chat_activity_manager = db_manager.get_activity_manager(update.effective_chat.id)
    
    # Get stats
    stats = chat_activity_manager.get_user_stats(user_id)
    if not stats:
        await update.message.reply_text("Статистика пока отсутствует. Начните чат!")
        return
    
    # Get all titles for today
    titles = chat_activity_manager.get_all_user_titles(user_id)
    rank = chat_activity_manager.get_user_rank(user_id)
    
    # Generate profile text
    text = await generate_profile_text(user, profile, stats, titles, rank)
    
    # Get photo if available
    photo_file_id = None
    if profile and profile.get('reference_photo'):
        ref_photo = profile.get('reference_photo')
        if ref_photo and ref_photo.startswith('photo:'):
            photo_file_id = ref_photo.split(':', 1)[1]
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Редактировать", callback_data="profile_edit")],
        [InlineKeyboardButton("❌ Закрыть", callback_data="profile_close")]
    ])
    
    # Send photo if available
    if photo_file_id:
        await update.message.reply_photo(
            photo=photo_file_id,
            caption=text,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile-related callback queries."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "profile_edit":
        # Open edit menu (try private, fallback to group)
        await show_edit_menu(query.from_user.id, context, update)
    
    elif data == "profile_close":
        # Close the message
        await query.delete_message()
    
    elif data.startswith("edit_"):
        # Field editing
        field = data.split("_", 1)[1]
        if field in FIELD_PROMPTS or field == 'personality_type':
            await request_field_value(query.from_user.id, field, context, update)
    
    elif data == "edit_done":
        # Finish editing
        await query.edit_message_text(text="Редактирование завершено! Используй /me для просмотра анкеты.")
    
    elif data.startswith("personality_"):
        # Personality type selection
        personality_type = data.split("_", 1)[1]
        
        if personality_type == "custom":
            # Request custom text
            context.user_data['editing_field'] = 'personality_type'
            try:
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text="Введите свой вариант типа личности:"
                )
            except Exception as e:
                # If bot can't start conversation, ask user to write first
                await query.edit_message_text(
                    text="Напишите мне в личные сообщения, чтобы установить тип личности: @{}"
                    .format(context.bot.username)
                )
        else:
            # Save selected personality type
            db_manager = context.application.bot_data.get('db_manager')
            if db_manager:
                activity_manager = db_manager.get_activity_manager(query.from_user.id)
                activity_manager.save_profile_field(query.from_user.id, 'personality_type', personality_type)
            
            # Show updated menu
            await show_edit_menu(query.from_user.id, context, update)


async def show_edit_menu(user_id: int, context: ContextTypes.DEFAULT_TYPE, update: Update = None):
    """Show edit menu in private chat or edit message in group chat."""
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        if update and update.message:
            await update.message.reply_text("Извините, система анкет недоступна.")
        else:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="Извините, система анкет недоступна."
                )
            except Exception as e:
                logger.error(f"Can't send message to user {user_id}: {e}")
        return
    
    # Get activity manager (use user_id as chat_id for private)
    # Но для сохранения в правильную базу используем user_id
    activity_manager = db_manager.get_activity_manager(user_id)
    profile = activity_manager.get_profile(user_id)
    
    # Build menu text
    text = "✏️ Редактирование анкеты\n\n"
    if profile:
        text += "Текущие данные:\n"
        for field, label in FIELD_LABELS.items():
            value = profile.get(field)
            if value:
                text += f"{label}: {value}\n"
    else:
        text += "Анкета не заполнена. Начните заполнять!"
    
    text += "\nВыберите поле для редактирования:"
    
    # Create inline keyboard with field buttons
    keyboard = []
    for field, label in FIELD_LABELS.items():
        # Split into rows of 2 buttons
        if len(keyboard) == 0 or len(keyboard[-1]) >= 2:
            keyboard.append([])
        keyboard[-1].append(InlineKeyboardButton(label, callback_data=f"edit_{field}"))
    
    # Add "Готово" button
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="edit_done")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Try to send to private chat first
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup
        )
    except Exception as e:
        # If bot can't initiate conversation, try to edit message in group chat
        logger.error(f"Can't send message to user {user_id}: {e}")
        if update and update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup
                )
            except Exception as e2:
                logger.error(f"Can't edit message in group chat: {e2}")


async def request_field_value(user_id: int, field: str, context: ContextTypes.DEFAULT_TYPE, update: Update = None):
    """Request a field value from user."""
    # Store editing state
    context.user_data['editing_field'] = field
    
    # Special handling for personality_type
    if field == 'personality_type':
        # Show inline keyboard with personality types
        keyboard = []
        for i, ptype in enumerate(PERSONALITY_TYPES):
            if len(keyboard) == 0 or len(keyboard[-1]) >= 2:
                keyboard.append([])
            keyboard[-1].append(InlineKeyboardButton(ptype, callback_data=f"personality_{ptype}"))
        
        # Add custom text option
        keyboard.append([InlineKeyboardButton("✏️ Свой вариант", callback_data="personality_custom")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="Выберите тип личности:",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Can't send message to user {user_id}: {e}")
            # Try to edit message in group chat
            if update and update.callback_query:
                try:
                    await update.callback_query.edit_message_text(
                        text="❌ Невозможно отправить сообщение в личку. Бот заблокирован.",
                        reply_markup=None
                    )
                except Exception as e2:
                    logger.error(f"Can't edit message in group chat: {e2}")
    else:
        # Send prompt for text input
        prompt = FIELD_PROMPTS.get(field, "Введите новое значение:")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=prompt
            )
        except Exception as e:
            logger.error(f"Can't send message to user {user_id}: {e}")
            # Try to edit message in group chat
            if update and update.callback_query:
                try:
                    await update.callback_query.edit_message_text(
                        text="❌ Невозможно отправить сообщение в личку. Бот заблокирован.",
                        reply_markup=None
                    )
                except Exception as e2:
                    logger.error(f"Can't edit message in group chat: {e2}")


async def handle_profile_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input for profile fields."""
    user_id = update.effective_user.id
    
    # Check if we're expecting input
    if 'editing_field' not in context.user_data:
        return  # Return None explicitly (not awaited)
    
    field = context.user_data['editing_field']
    
    # Get activity manager
    db_manager = context.application.bot_data.get('db_manager')
    if not db_manager:
        await update.message.reply_text("Извините, система анкет недоступна.")
        return
    
    activity_manager = db_manager.get_activity_manager(user_id)
    
    # Handle photo upload
    if field == 'reference_photo':
        if update.message.photo:
            # Get the largest photo
            photo = update.message.photo[-1]
            file_id = photo.file_id
            value = f"photo:{file_id}"
        elif update.message.document:
            # Handle document (photo)
            file_id = update.message.document.file_id
            value = f"photo:{file_id}"
        elif update.message.text:
            # URL or text
            value = update.message.text
        else:
            await update.message.reply_text("Пожалуйста, отправьте фото или URL.")
            return
    else:
        # Text input
        if not update.message.text:
            await update.message.reply_text("Пожалуйста, введите текст.")
            return
        value = update.message.text
    
    # Save the field
    success = activity_manager.save_profile_field(user_id, field, value)
    
    if success:
        # Clear editing state
        del context.user_data['editing_field']
        
        # Show updated menu
        await show_edit_menu(user_id, context)
    else:
        await update.message.reply_text("Ошибка при сохранении. Попробуйте снова.")


# Register handlers
def register_profile_handlers(application):
    """Register all profile-related handlers."""
    application.add_handler(CommandHandler("me", profile_command))
    application.add_handler(CallbackQueryHandler(handle_profile_callback, pattern="^profile_"))
    application.add_handler(CallbackQueryHandler(handle_profile_callback, pattern="^edit_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profile_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_profile_message))
