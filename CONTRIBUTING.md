# Руководство для контрибьюторов

Спасибо за интерес к проекту Kayo Bot! Мы рады любому вкладу.

## Как начать

1. Форкните репозиторий
2. Клонируйте свой форк: `git clone https://github.com/YOUR_USERNAME/kayo-bot.git`
3. Создайте ветку для вашего изменения: `git checkout -b feature/your-feature`
4. Внесите изменения
5. Запушьте изменения: `git push origin feature/your-feature`
6. Создайте Pull Request

## Структура кода

- `bot/handlers/` — обработчики команд Telegram
- `bot/services/` — сервисы (база данных, автообновление)
- `bot/database/` — модули работы с базой данных
- `main.py` — точка входа приложения

## Стиль кода

- Используйте Python 3.8+
- Следуйте PEP 8
- Добавляйте docstrings для всех функций и классов
- Используйте type hints где возможно
- Добавляйте комментарии для сложной логики

## Добавление новых команд

1. Создайте файл в `bot/handlers/` (например, `new_command.py`)
2. Реализуйте обработчик команды:
   ```python
   from telegram import Update
   from telegram.ext import ContextTypes

   def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
       """Описание команды."""
       update.message.reply_text("Ответ команды")
   ```
3. Добавьте импорт и регистрацию в `main.py`:
   ```python
   from bot.handlers.new_command import new_command
   # ...
   application.add_handler(CommandHandler("newcommand", new_command))
   ```

## Тестирование

- Запуск бота: `python main.py`
- Проверка команд вручную через Telegram
- Для автоматизированного тестирования добавьте тесты в `tests/`

## Отправка изменений

1. Убедитесь, что все тесты проходят
2. Обновите документацию если нужно
3. Добавьте запись в CHANGELOG.md если это значительное изменение
4. Создайте Pull Request с описанием изменений

## Вопросы?

Если у вас есть вопросы, откройте Issue в репозитории.
