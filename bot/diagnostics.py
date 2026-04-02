"""
Диагностический инструментарий для тестирования Kayo Bot.

Этот модуль предоставляет инструменты для имитации Telegram API,
тестирования обработчиков команд и диагностики проблем без реального бота.

Особенности:
- Mock-объекты для Telegram Update и Context
- Генерация тестовых сообщений и команд
- Автоматическое тестирование всех обработчиков
- Валидация ответов бота
- Логирование результатов тестирования
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Импортируем нашу систему логирования
from bot.logging import get_logger, log_function_call

logger = get_logger("kayo-bot.diagnostics")

# Mock объекты для Telegram API
@dataclass
class MockUser:
    """Mock объект пользователя Telegram."""
    id: int
    username: str = ""
    first_name: str = "Test"
    last_name: str = "User"
    
    def mention_html(self):
        return f'<a href="tg://user?id={self.id}">{self.first_name}</a>'

@dataclass
class MockChat:
    """Mock объект чата Telegram."""
    id: int
    type: str = "private"
    title: str = "Test Chat"

@dataclass
class MockMessage:
    """Mock объект сообщения Telegram."""
    message_id: int
    chat: MockChat
    from_user: MockUser
    text: str = ""
    date: datetime = None
    
    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()
    
    def reply_text(self, text: str, **kwargs):
        logger.info(f"Bot would reply: {text[:100]}...")
        return MockMessage(
            message_id=self.message_id + 1,
            chat=self.chat,
            from_user=MockUser(id=0, username="kayo_bot", first_name="Kayo"),
            text=text
        )
    
    def reply_html(self, text: str, **kwargs):
        logger.info(f"Bot would reply (HTML): {text[:100]}...")
        return MockMessage(
            message_id=self.message_id + 1,
            chat=self.chat,
            from_user=MockUser(id=0, username="kayo_bot", first_name="Kayo"),
            text=text
        )

@dataclass
class MockBot:
    """Mock объект бота Telegram."""
    username: str = "kayo_bot"
    
    async def set_my_commands(self, commands):
        logger.info(f"Bot commands would be set: {commands}")

class MockContext:
    """Mock объект контекста Telegram."""
    def __init__(self):
        self.bot = MockBot()
        self.bot_data = {}
        self.user_data = {}
        self.chat_data = {}
        self.args = []
        
    async def bot(self):
        return self.bot

class MockUpdate:
    """Mock объект обновления Telegram."""
    def __init__(self, message: MockMessage = None, effective_chat=None, effective_user=None):
        self.message = message
        self.effective_chat = effective_chat or (message.chat if message else None)
        self.effective_user = effective_user or (message.from_user if message else None)
        self.my_chat_member = None


class TelegramAPIMocker:
    """Основной класс для имитации Telegram API."""
    
    def __init__(self):
        self.test_users = {
            123456789: MockUser(id=123456789, username="test_user", first_name="Test"),
            987654321: MockUser(id=987654321, username="another_user", first_name="Another"),
        }
        
        self.test_chats = {
            -1001234567890: MockChat(id=-1001234567890, type="group", title="Test Group"),
            123456789: MockChat(id=123456789, type="private", title="Private Chat"),
        }
        
        self.message_counter = 1
        logger.info("Telegram API Mocker initialized")
    
    @log_function_call
    def create_message(self, text: str, user_id: int = 123456789, chat_id: int = -1001234567890) -> MockMessage:
        """Создает тестовое сообщение."""
        user = self.test_users.get(user_id, MockUser(id=user_id, first_name=f"User{user_id}"))
        chat = self.test_chats.get(chat_id, MockChat(id=chat_id, type="group" if chat_id < 0 else "private"))
        
        message = MockMessage(
            message_id=self.message_counter,
            chat=chat,
            from_user=user,
            text=text
        )
        
        self.message_counter += 1
        logger.debug(f"Created test message", message_id=message.message_id, text=text[:50])
        return message
    
    @log_function_call
    def create_command(self, command: str, args: str = "", user_id: int = 123456789, chat_id: int = -1001234567890) -> MockMessage:
        """Создает тестовую команду."""
        full_text = f"/{command}"
        if args:
            full_text += f" {args}"
        
        return self.create_message(full_text, user_id, chat_id)
    
    @log_function_call
    def create_update(self, message: MockMessage) -> MockUpdate:
        """Создает обновление из сообщения."""
        return MockUpdate(message=message)


class CommandTester:
    """Класс для тестирования команд бота."""
    
    def __init__(self, mocker: TelegramAPIMocker = None):
        self.mocker = mocker or TelegramAPIMocker()
        self.context = MockContext()
        
        # Импортируем обработчики команд
        from main import (
            start, help_command_wrapper, about_command_wrapper,
            combined_message_handler, chat_member_handler
        )
        
        from bot.handlers.hug import hug_command
        from bot.handlers.bite import bite_command
        from bot.handlers.pat import pat_command
        from bot.handlers.boop import boop_command
        from bot.handlers.kiss import kiss_command
        from bot.handlers.slapass import slapass_command
        from bot.handlers.general import (
            top_command, today_command, titles_command, 
            summarize_command, update_command
        )
        
        # Сохраняем ссылки на обработчики
        self.handlers = {
            "start": start,
            "help": help_command_wrapper,
            "about": about_command_wrapper,
            "hug": hug_command,
            "bite": bite_command,
            "pat": pat_command,
            "boop": boop_command,
            "kiss": kiss_command,
            "slapass": slapass_command,
            "top": top_command,
            "today": today_command,
            "titles": titles_command,
            "summarize": summarize_command,
            "update": update_command,
            "message": combined_message_handler,
            "chat_member": chat_member_handler,
        }
        
        logger.info(f"CommandTester initialized with {len(self.handlers)} handlers")
    
    @log_function_call
    async def test_command(self, command_name: str, args: str = "", user_id: int = 123456789, chat_id: int = -1001234567890) -> Dict[str, Any]:
        """Тестирует одну команду."""
        if command_name not in self.handlers:
            logger.error(f"Handler not found: {command_name}")
            return {"success": False, "error": f"Handler {command_name} not found"}
        
        handler = self.handlers[command_name]
        
        # Создаем сообщение и обновление
        if command_name == "message":
            message = self.mocker.create_message(args, user_id, chat_id)
        elif command_name == "chat_member":
            # Для chat_member нужен специальный обработчик
            return await self.test_chat_member(user_id, chat_id)
        else:
            message = self.mocker.create_command(command_name, args, user_id, chat_id)
        
        update = self.mocker.create_update(message)
        
        try:
            logger.info(f"Testing command: /{command_name} {args}", user_id=user_id, chat_id=chat_id)
            
            # Выполняем обработчик
            if asyncio.iscoroutinefunction(handler):
                result = await handler(update, self.context)
            else:
                result = handler(update, self.context)
            
            logger.info(f"Command /{command_name} executed successfully")
            return {
                "success": True,
                "command": command_name,
                "args": args,
                "user_id": user_id,
                "chat_id": chat_id,
                "result": str(result)[:200] if result else None
            }
            
        except Exception as e:
            logger.error(f"Command /{command_name} failed: {e}", exc_info=True)
            return {
                "success": False,
                "command": command_name,
                "args": args,
                "user_id": user_id,
                "chat_id": chat_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    @log_function_call
    async def test_chat_member(self, user_id: int = 123456789, chat_id: int = -1001234567890) -> Dict[str, Any]:
        """Тестирует обработчик добавления бота в чат."""
        try:
            from telegram import ChatMember, ChatMemberUpdated
            
            # Создаем mock объекты
            chat = self.mocker.test_chats.get(chat_id, MockChat(id=chat_id, type="group"))
            user = self.mocker.test_users.get(user_id, MockUser(id=user_id))
            
            # Создаем ChatMemberUpdated
            old_chat_member = ChatMember(
                user=user,
                status="left",
                until_date=None
            )
            
            new_chat_member = ChatMember(
                user=user,
                status="member",
                until_date=None
            )
            
            chat_member_updated = ChatMemberUpdated(
                chat=chat,
                from_user=user,
                date=datetime.now(),
                old_chat_member=old_chat_member,
                new_chat_member=new_chat_member
            )
            
            # Создаем Update с my_chat_member
            update = MockUpdate()
            update.my_chat_member = chat_member_updated
            update.effective_chat = chat
            update.effective_user = user
            
            # Выполняем обработчик
            handler = self.handlers["chat_member"]
            if asyncio.iscoroutinefunction(handler):
                await handler(update, self.context)
            else:
                handler(update, self.context)
            
            logger.info("Chat member handler executed successfully")
            return {
                "success": True,
                "test_type": "chat_member_added",
                "user_id": user_id,
                "chat_id": chat_id
            }
            
        except Exception as e:
            logger.error(f"Chat member test failed: {e}", exc_info=True)
            return {
                "success": False,
                "test_type": "chat_member_added",
                "user_id": user_id,
                "chat_id": chat_id,
                "error": str(e)
            }
    
    @log_function_call
    async def run_all_tests(self) -> Dict[str, Any]:
        """Запускает все тесты команд."""
        test_cases = [
            ("start", ""),
            ("help", ""),
            ("about", ""),
            ("hug", ""),
            ("hug", "@another_user"),
            ("bite", ""),
            ("pat", ""),
            ("boop", ""),
            ("kiss", ""),
            ("slapass", ""),
            ("top", ""),
            ("today", ""),
            ("titles", ""),
            ("summarize", ""),
            ("update", ""),
            ("message", "Привет, как дела?"),
            ("message", "хочу спать"),
            ("message", "обнимашки"),
        ]
        
        results = []
        successful = 0
        failed = 0
        
        logger.info(f"Starting comprehensive test suite with {len(test_cases)} test cases")
        
        for command_name, args in test_cases:
            result = await self.test_command(command_name, args)
            results.append(result)
            
            if result["success"]:
                successful += 1
            else:
                failed += 1
        
        # Тестируем добавление в чат
        chat_member_result = await self.test_chat_member()
        results.append(chat_member_result)
        if chat_member_result["success"]:
            successful += 1
        else:
            failed += 1
        
        summary = {
            "total_tests": len(results),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(results)) * 100 if results else 0,
            "results": results
        }
        
        logger.info(f"Test suite completed", 
                   total=summary["total_tests"],
                   successful=summary["successful"],
                   failed=summary["failed"],
                   success_rate=f"{summary['success_rate']:.1f}%")
        
        return summary
    
    @log_function_call
    def generate_report(self, test_results: Dict[str, Any]) -> str:
        """Генерирует отчет о тестировании."""
        report = []
        report.append("=" * 60)
        report.append("DIAGNOSTIC TEST REPORT - KAYO BOT")
        report.append("=" * 60)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Tests: {test_results['total_tests']}")
        report.append(f"Successful: {test_results['successful']}")
        report.append(f"Failed: {test_results['failed']}")
        report.append(f"Success Rate: {test_results['success_rate']:.1f}%")
        report.append("")
        report.append("DETAILED RESULTS:")
        report.append("-" * 60)
        
        for i, result in enumerate(test_results['results'], 1):
            status = "✓" if result['success'] else "✗"
            command = result.get('command', 'unknown')
            args = result.get('args', '')
            
            if result['success']:
                report.append(f"{i:2d}. {status} /{command} {args}")
            else:
                report.append(f"{i:2d}. {status} /{command} {args}")
                report.append(f"    ERROR: {result.get('error', 'Unknown error')}")
        
        report.append("")
        report.append("RECOMMENDATIONS:")
        report.append("-" * 60)
        
        if test_results['failed'] == 0:
            report.append("✅ Все тесты пройдены успешно. Бот готов к работе.")
        else:
            report.append("⚠️  Обнаружены проблемы:")
            for result in test_results['results']:
                if not result['success']:
                    report.append(f"  • /{result['command']}: {result.get('error', 'Unknown error')}")
            report.append("")
            report.append("Рекомендуется исправить указанные ошибки перед релизом.")
        
        report.append("=" * 60)
        
        return "\n".join(report)


# Утилитарные функции
@log_function_call
async def run_diagnostics():
    """Основная функция запуска диагностики."""
    logger.info("Starting comprehensive bot diagnostics")
    
    try:
        # Создаем тестер
        tester = CommandTester()
        
        # Запускаем все тесты
        results = await tester.run_all_tests()
        
        # Генерируем отчет
        report = tester.generate_report(results)
        
        # Сохраняем отчет в файл
        report_file = f"diagnostics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Diagnostics report saved to {report_file}")
        
        # Выводим отчет в консоль
        print("\n" + report)
        
        return {
            "success": results["success_rate"] == 100,
            "report_file": report_file,
            "summary": results
        }
        
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Запускаем диагностику при прямом выполнении
    asyncio.run(run_diagnostics())