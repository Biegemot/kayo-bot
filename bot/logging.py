"""
Продвинутая система логирования для Kayo Bot.

Особенности:
- Структурированное логирование с поддержкой JSON
- Ротация логов по датам (новый файл каждый день)
- Контекстное логирование для отслеживания цепочек событий
- Автоматическое логирование вызовов функций через декоратор
- Поддержка разных уровней логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Сохранение трейсбэков при ошибках
- Отдельные лог-файлы за разные даты в структурированных папках
"""

import json
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, Union

# Конфигурация логирования
LOG_DIR = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = {
    "timestamp": "%(asctime)s",
    "logger": "%(name)s",
    "level": "%(levelname)s",
    "message": "%(message)s",
    "module": "%(module)s",
    "function": "%(funcName)s",
    "line": "%(lineno)d",
    "context": "%(context)s" if "%(context)s" in LOG_FORMAT else ""
}

# Контекст для логирования
class LoggingContext:
    """Контекстный менеджер для добавления контекста в логи."""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.context = kwargs or {}
        self.old_context = {}
        
    def __enter__(self):
        # Сохраняем старый контекст
        if hasattr(self.logger, 'context'):
            self.old_context = getattr(self.logger, 'context', {}).copy()
        
        # Устанавливаем новый контекст
        new_context = self.old_context.copy()
        new_context.update(self.context)
        setattr(self.logger, 'context', new_context)
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Восстанавливаем старый контекст
        setattr(self.logger, 'context', self.old_context)


class StructuredLogger:
    """Расширенный логгер со структурным выводом."""
    
    def __init__(self, name: str = "kayo-bot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Контекст для логирования
        self.context = {}
        
        # Создаем директорию для логов
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Настраиваем обработчики
        self._setup_handlers()
        
    def _get_dated_filename(self, prefix: str, extension: str = "log") -> str:
        """Генерирует имя файла с датой."""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(LOG_DIR, f"{prefix}_{today}.{extension}")
    
    def _setup_handlers(self):
        """Настраивает обработчики логов."""
        
        # Форматтер для текстовых логов
        text_formatter = logging.Formatter(LOG_FORMAT)
        
        # Форматтер для JSON логов
        json_formatter = logging.Formatter(json.dumps(JSON_LOG_FORMAT))
        
        # Обработчик для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(text_formatter)
        
        # Обработчик для основного лог-файла с ротацией по датам
        main_log_file = self._get_dated_filename("kayo-bot")
        main_handler = logging.handlers.TimedRotatingFileHandler(
            filename=main_log_file,
            when="midnight",
            interval=1,
            backupCount=30
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(text_formatter)
        
        # Обработчик для JSON логов (один файл на день)
        json_log_file = self._get_dated_filename("kayo-bot", "json")
        json_handler = logging.FileHandler(filename=json_log_file)
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(json_formatter)
        
        # Обработчик для ошибок (отдельный файл)
        error_log_file = self._get_dated_filename("errors")
        error_handler = logging.FileHandler(filename=error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(text_formatter)
        
        # Обработчик для команд бота (отдельный файл)
        commands_log_file = self._get_dated_filename("commands")
        commands_handler = logging.FileHandler(filename=commands_log_file)
        commands_handler.setLevel(logging.INFO)
        commands_formatter = logging.Formatter('%(asctime)s - COMMAND - %(message)s')
        commands_handler.setFormatter(commands_formatter)
        
        # Обработчик для базы данных (отдельный файл)
        db_log_file = self._get_dated_filename("database")
        db_handler = logging.FileHandler(filename=db_log_file)
        db_handler.setLevel(logging.DEBUG)
        db_formatter = logging.Formatter('%(asctime)s - DB - %(message)s')
        db_handler.setFormatter(db_formatter)
        
        # Создаем отдельный логгер для базы данных
        db_logger = logging.getLogger("kayo-bot.db")
        db_logger.addHandler(db_handler)
        db_logger.setLevel(logging.DEBUG)
        
        # Создаем отдельный логгер для команд
        cmd_logger = logging.getLogger("kayo-bot.commands")
        cmd_logger.addHandler(commands_handler)
        cmd_logger.setLevel(logging.INFO)
        
        # Добавляем обработчики к основному логгеру
        self.logger.addHandler(console_handler)
        self.logger.addHandler(main_handler)
        self.logger.addHandler(json_handler)
        self.logger.addHandler(error_handler)
        
        # Сохраняем ссылки на специализированные логгеры
        self.db_logger = db_logger
        self.cmd_logger = cmd_logger
    
    def set_context(self, **kwargs):
        """Устанавливает контекст для последующих логов."""
        self.context.update(kwargs)
        
    def clear_context(self):
        """Очищает контекст."""
        self.context.clear()
        
    def with_context(self, **kwargs):
        """Возвращает контекстный менеджер."""
        return LoggingContext(self.logger, **kwargs)
    
    def _prepare_message(self, msg: str, extra: Optional[Dict] = None) -> str:
        """Подготавливает сообщение для логирования."""
        if extra:
            # Добавляем контекст
            if self.context:
                extra = {**self.context, **extra}
            
            # Форматируем сообщение с дополнительными данными
            extra_str = " ".join([f"{k}={v}" for k, v in extra.items()])
            return f"{msg} | {extra_str}"
        elif self.context:
            # Добавляем только контекст
            context_str = " ".join([f"{k}={v}" for k, v in self.context.items()])
            return f"{msg} | {context_str}"
        else:
            return msg
    
    def debug(self, msg: str, **kwargs):
        """Логирование на уровне DEBUG."""
        self.logger.debug(self._prepare_message(msg, kwargs))
        
    def info(self, msg: str, **kwargs):
        """Логирование на уровне INFO."""
        self.logger.info(self._prepare_message(msg, kwargs))
        
    def warning(self, msg: str, **kwargs):
        """Логирование на уровне WARNING."""
        self.logger.warning(self._prepare_message(msg, kwargs))
        
    def error(self, msg: str, exc_info: bool = True, **kwargs):
        """Логирование на уровне ERROR."""
        self.logger.error(self._prepare_message(msg, kwargs), exc_info=exc_info)
        
    def critical(self, msg: str, **kwargs):
        """Логирование на уровне CRITICAL."""
        self.logger.critical(self._prepare_message(msg, kwargs))
        
    def log_command(self, command: str, user_id: int, chat_id: int, **kwargs):
        """Логирование команды бота."""
        log_msg = f"Command: {command} | user_id={user_id} | chat_id={chat_id}"
        for k, v in kwargs.items():
            log_msg += f" | {k}={v}"
        
        # Логируем в основной логгер
        self.info(log_msg)
        
        # Логируем в специализированный логгер команд
        self.cmd_logger.info(log_msg)
        
    def log_event(self, event_type: str, **kwargs):
        """Логирование события."""
        self.info(
            f"Event: {event_type}",
            event_type=event_type,
            **kwargs
        )
        
    def log_database(self, operation: str, table: str, **kwargs):
        """Логирование операции с базой данных."""
        log_msg = f"DB {operation} on {table}"
        for k, v in kwargs.items():
            log_msg += f" | {k}={v}"
        
        # Логируем в основной логгер
        self.debug(log_msg)
        
        # Логируем в специализированный логгер базы данных
        self.db_logger.debug(log_msg)


# Глобальный экземпляр логгера
logger = StructuredLogger("kayo-bot")


def log_function_call(func):
    """
    Декоратор для автоматического логирования вызовов функций.
    
    Пример использования:
    
    @log_function_call
    def process_message(message):
        # код функции
        return result
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Логируем вызов функции
        logger.debug(
            f"Calling {func.__name__}",
            function=func.__name__,
            module=func.__module__,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )
        
        try:
            # Выполняем функцию
            result = func(*args, **kwargs)
            
            # Логируем успешное выполнение
            logger.debug(
                f"Function {func.__name__} completed successfully",
                function=func.__name__
            )
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            logger.error(
                f"Function {func.__name__} failed: {str(e)}",
                function=func.__name__,
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc()
            )
            
            # Пробрасываем исключение дальше
            raise
    
    return wrapper


# Утилитарные функции
def setup_logging():
    """Настраивает логирование для всего приложения."""
    # Уже настроено через StructuredLogger
    return logger


def get_logger(name: str = "kayo-bot") -> StructuredLogger:
    """Возвращает именованный логгер."""
    return StructuredLogger(name)


if __name__ == "__main__":
    # Тестирование системы логирования
    logger.info("Система логирования запущена", test=True)
    
    # Тестирование контекста
    with logger.with_context(user_id=123, session_id="abc"):
        logger.info("Сообщение с контекстом")
        
    # Тестирование логирования команд
    logger.log_command("test", 123, 456, param1="value1", param2="value2")
    
    # Тестирование логирования базы данных
    logger.log_database("SELECT", "users", user_id=123)
    
    # Тестирование декоратора
    @log_function_call
    def test_function(x, y):
        return x + y
    
    test_function(2, 3)