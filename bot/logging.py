"""
Продвинутая система логирования для Kayo Bot с ротацией по датам
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import json
import traceback
from functools import wraps

class StructuredLogger:
    """Логгер с поддержкой структурированных данных и контекста"""
    
    def __init__(self, name: str = "kayo-bot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Форматтер для структурированных логов
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Консольный хендлер
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
        
        # Файловый хендлер с ротацией по датам
        self.setup_file_handler()
        
        # Контекст для структурированного логирования
        self.context: Dict[str, Any] = {}
    
    def setup_file_handler(self):
        """Настройка ротации логов по датам"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Файловый хендлер с ротацией по датам (новый файл каждый день)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "kayo-bot.log"),
            when="midnight",
            interval=1,
            backupCount=30,  # Храним логи за 30 дней
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
    
    def set_context(self, **kwargs):
        """Установить контекст для последующих логов"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Очистить контекст"""
        self.context.clear()
    
    def _format_message(self, message: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """Форматировать сообщение с контекстом"""
        data = {"message": message, **self.context}
        if extra:
            data.update(extra)
        return json.dumps(data, ensure_ascii=False, default=str)
    
    def debug(self, message: str, **kwargs):
        """Логирование уровня DEBUG"""
        self.logger.debug(self._format_message(message, kwargs))
    
    def info(self, message: str, **kwargs):
        """Логирование уровня INFO"""
        self.logger.info(self._format_message(message, kwargs))
    
    def warning(self, message: str, **kwargs):
        """Логирование уровня WARNING"""
        self.logger.warning(self._format_message(message, kwargs))
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Логирование уровня ERROR"""
        if exc_info:
            kwargs["traceback"] = traceback.format_exc()
        self.logger.error(self._format_message(message, kwargs))
    
    def critical(self, message: str, **kwargs):
        """Логирование уровня CRITICAL"""
        self.logger.critical(self._format_message(message, kwargs))
    
    def log_command(self, user_id: int, command: str, **kwargs):
        """Логирование команд пользователя"""
        self.info(f"Command executed", user_id=user_id, command=command, **kwargs)
    
    def log_event(self, event_type: str, **kwargs):
        """Логирование событий"""
        self.info(f"Event: {event_type}", event_type=event_type, **kwargs)

# Глобальный экземпляр логгера
logger = StructuredLogger()

def log_function_call(func):
    """Декоратор для логирования вызовов функций"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"Function called", function=func_name, args=args, kwargs=kwargs)
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function completed", function=func_name, result=result)
            return result
        except Exception as e:
            logger.error(f"Function failed", function=func_name, error=str(e))
            raise
    return wrapper

def setup_logging():
    """Настройка системы логирования для всего приложения"""
    # Уже настроено в конструкторе StructuredLogger
    logger.info("Logging system initialized")
    return logger

if __name__ == "__main__":
    # Тестирование системы логирования
    logger.info("Testing logging system")
    logger.set_context(component="test", version="0.8.0")
    logger.debug("Debug message with context", test_data={"key": "value"})
    logger.error("Error message", exc_info=False)
    logger.clear_context()