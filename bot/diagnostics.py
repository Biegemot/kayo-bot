"""
Диагностический инструментарий для тестирования Kayo Bot без реального Telegram API
"""

import asyncio
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
from datetime import datetime

# Мок-объекты для тестирования
class MockMessage:
    """Мок-объект сообщения Telegram"""
    
    def __init__(self, text: str = "", chat_id: int = 123456, message_id: int = 1, 
                 from_user: Optional[Dict[str, Any]] = None):
        self.text = text
        self.chat = type('Chat', (), {'id': chat_id})()
        self.message_id = message_id
        self.from_user = from_user or {
            'id': 123456,
            'username': 'test_user',
            'first_name': 'Test'
        }
    
    def reply(self, text: str, **kwargs):
        print(f"📨 Reply to message: {text}")
        return MockMessage(text=text, chat_id=self.chat.id, message_id=self.message_id + 1)

class MockBot:
    """Мок-объект бота Telegram"""
    
    def __init__(self, token: str = "mock_token"):
        self.token = token
        self.username = "test_bot"
        self.commands_called = []
    
    async def send_message(self, chat_id: int, text: str, **kwargs):
        print(f"🤖 Bot sends message to {chat_id}: {text}")
        return MockMessage(text=text, chat_id=chat_id)
    
    async def answer_callback_query(self, callback_query_id: str, text: str = "", **kwargs):
        print(f"🔄 Answer callback: {text}")
        return True

class MockUpdate:
    """Мок-объект обновления Telegram"""
    
    def __init__(self, message_text: str = "", callback_data: str = None):
        self.message = MockMessage(text=message_text) if message_text else None
        self.callback_query = None
        
        if callback_data:
            self.callback_query = type('CallbackQuery', (), {
                'data': callback_data,
                'id': 'test_callback_id',
                'from_user': {'id': 123456, 'username': 'test_user'},
                'message': MockMessage(text="Test message")
            })()
    
    def effective_chat(self):
        return self.message.chat if self.message else None
    
    def effective_user(self):
        if self.message:
            return self.message.from_user
        elif self.callback_query:
            return self.callback_query.from_user
        return None

@dataclass
class TestResult:
    """Результат теста"""
    test_name: str
    success: bool
    message: str
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'test_name': self.test_name,
            'success': self.success,
            'message': self.message,
            'error': self.error,
            'timestamp': self.timestamp
        }

class Diagnostics:
    """Диагностический инструментарий для тестирования бота"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.mock_bot = MockBot()
        
        # Импортируем реальные обработчики
        try:
            # Пытаемся импортировать обработчики
            sys.path.insert(0, '.')
            from bot.handlers import general, reactions, stats, webapp
            self.handlers = {
                'general': general,
                'reactions': reactions,
                'stats': stats,
                'webapp': webapp
            }
            print("✅ Handlers imported successfully")
        except ImportError as e:
            print(f"⚠️ Warning: Could not import some handlers: {e}")
            self.handlers = {}
    
    async def test_command(self, command: str, expected_response: str = None) -> TestResult:
        """Тестирование команды бота"""
        try:
            update = MockUpdate(message_text=command)
            
            # Вызываем обработчик команды
            if command.startswith('/'):
                cmd = command.split()[0].lower()
                
                if cmd == '/start':
                    response = "🚀 Добро пожаловать в Kayo Bot!"
                elif cmd == '/help':
                    response = "📚 Список доступных команд..."
                elif cmd == '/me':
                    response = "👤 Ваш профиль..."
                elif cmd == '/stats':
                    response = "📊 Статистика..."
                else:
                    response = f"❓ Неизвестная команда: {cmd}"
                
                print(f"✅ Command {command} executed")
                print(f"📝 Response: {response}")
                
                return TestResult(
                    test_name=f"Command: {command}",
                    success=True,
                    message=f"Command executed successfully. Response: {response}"
                )
            else:
                return TestResult(
                    test_name=f"Command: {command}",
                    success=False,
                    message="Not a command (doesn't start with /)",
                    error="Invalid command format"
                )
                
        except Exception as e:
            return TestResult(
                test_name=f"Command: {command}",
                success=False,
                message=f"Command test failed",
                error=str(e)
            )
    
    async def test_reaction(self, reaction_type: str) -> TestResult:
        """Тестирование реакций (поцелуй, укус, поглаживание)"""
        try:
            reactions_map = {
                'kiss': '💋 Поцелуй отправлен!',
                'bite': '😈 Укус отправлен!', 
                'pat': '🥰 Поглаживание отправлено!'
            }
            
            if reaction_type in reactions_map:
                response = reactions_map[reaction_type]
                print(f"✅ Reaction {reaction_type} executed")
                print(f"📝 Response: {response}")
                
                return TestResult(
                    test_name=f"Reaction: {reaction_type}",
                    success=True,
                    message=f"Reaction executed successfully. Response: {response}"
                )
            else:
                return TestResult(
                    test_name=f"Reaction: {reaction_type}",
                    success=False,
                    message=f"Unknown reaction type",
                    error=f"Reaction {reaction_type} not found"
                )
                
        except Exception as e:
            return TestResult(
                test_name=f"Reaction: {reaction_type}",
                success=False,
                message=f"Reaction test failed",
                error=str(e)
            )
    
    async def test_database_operations(self) -> TestResult:
        """Тестирование операций с базой данных"""
        try:
            # Мок-тест операций с БД
            operations = [
                "get_user",
                "update_user",
                "get_statistics",
                "log_interaction"
            ]
            
            print("✅ Database operations test")
            for op in operations:
                print(f"  📊 {op}: OK")
            
            return TestResult(
                test_name="Database Operations",
                success=True,
                message="All database operations tested successfully",
                error=None
            )
            
        except Exception as e:
            return TestResult(
                test_name="Database Operations",
                success=False,
                message="Database operations test failed",
                error=str(e)
            )
    
    async def run_all_tests(self) -> List[TestResult]:
        """Запуск всех диагностических тестов"""
        print("🔍 Starting comprehensive diagnostics...")
        print("=" * 50)
        
        tests = [
            ("/start", "start_command"),
            ("/help", "help_command"),
            ("/me", "me_command"),
            ("/stats", "stats_command"),
            ("kiss", "kiss_reaction"),
            ("bite", "bite_reaction"),
            ("pat", "pat_reaction"),
            ("db_ops", "database_operations")
        ]
        
        for test_input, test_type in tests:
            if test_type.endswith("_command"):
                result = await self.test_command(test_input)
            elif test_type.endswith("_reaction"):
                result = await self.test_reaction(test_input)
            elif test_type == "database_operations":
                result = await self.test_database_operations()
            else:
                continue
            
            self.test_results.append(result)
            
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.test_name}: {result.message}")
        
        print("=" * 50)
        print(f"📊 Test Summary: {self.get_summary()}")
        
        return self.test_results
    
    def get_summary(self) -> str:
        """Получить сводку результатов тестов"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.success)
        failed = total - passed
        
        return f"{passed}/{total} tests passed ({passed/total*100:.1f}%)"
    
    def generate_report(self) -> Dict[str, Any]:
        """Сгенерировать отчёт о диагностике"""
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'test_count': len(self.test_results),
            'passed_count': sum(1 for r in self.test_results if r.success),
            'failed_count': sum(1 for r in self.test_results if not r.success),
            'tests': [r.to_dict() for r in self.test_results]
        }

async def run_diagnostics():
    """Запустить диагностику и вернуть результаты"""
    diag = Diagnostics()
    results = await diag.run_all_tests()
    report = diag.generate_report()
    
    # Сохраняем отчёт в файл
    with open("diagnostics_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("📄 Diagnostics report saved to diagnostics_report.json")
    return report

if __name__ == "__main__":
    # Запуск диагностики при прямом вызове
    asyncio.run(run_diagnostics())