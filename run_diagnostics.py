#!/usr/bin/env python3
"""
Скрипт для запуска диагностики Kayo Bot.

Запускает комплексную проверку всех компонентов бота:
1. Проверяет импорты и зависимости
2. Тестирует систему логирования
3. Проверяет работу с базой данных
4. Тестирует обработчики команд
5. Генерирует отчет о готовности

Использование:
    python3 run_diagnostics.py
"""

import sys
import os
import asyncio
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_imports():
    """Проверяет все необходимые импорты."""
    print("🔍 Проверка импортов и зависимостей...")
    
    required_modules = [
        ("telegram", "python-telegram-bot"),
        ("dotenv", "python-dotenv"),
        ("sqlite3", "встроенный модуль"),
        ("asyncio", "встроенный модуль"),
    ]
    
    all_ok = True
    for module_name, package_name in required_modules:
        try:
            if module_name == "telegram":
                import telegram
                print(f"  ✅ {package_name} (версия: {telegram.__version__})")
            elif module_name == "dotenv":
                import dotenv
                print(f"  ✅ {package_name} (версия: {dotenv.__version__})")
            elif module_name == "sqlite3":
                import sqlite3
                print(f"  ✅ {package_name} (версия: {sqlite3.sqlite_version})")
            else:
                __import__(module_name)
                print(f"  ✅ {package_name}")
        except ImportError as e:
            print(f"  ❌ {package_name} - НЕ НАЙДЕН: {e}")
            all_ok = False
    
    return all_ok

def check_project_structure():
    """Проверяет структуру проекта."""
    print("\n📁 Проверка структуры проекта...")
    
    required_files = [
        "main.py",
        "bot/__init__.py",
        "bot/logging.py",
        "bot/services/activity.py",
        "bot/diagnostics.py",
        "version.py",
        "requirements.txt",
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - НЕ НАЙДЕН")
            all_ok = False
    
    return all_ok

def test_logging_system():
    """Тестирует систему логирования."""
    print("\n📝 Тестирование системы логирования...")
    
    try:
        from bot.logging import setup_logging, get_logger, log_function_call
        
        # Создаем логгер
        logger = setup_logging()
        
        # Тестируем логирование
        logger.info("Тестовое сообщение INFO", test=True)
        logger.debug("Тестовое сообщение DEBUG", test=True)
        logger.warning("Тестовое сообщение WARNING", test=True)
        logger.error("Тестовое сообщение ERROR", test=True)
        
        # Тестируем логирование команд
        logger.log_command("test", 123, 456, param="value")
        
        # Тестируем логирование базы данных
        logger.log_database("SELECT", "users", user_id=123)
        
        # Проверяем создание директории логов
        logs_dir = project_root / "logs"
        if logs_dir.exists():
            print(f"  ✅ Директория логов создана: {logs_dir}")
            
            # Проверяем файлы логов
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                print(f"  ✅ Созданы файлы логов: {len(log_files)} файлов")
            else:
                print(f"  ⚠️  Файлы логов не созданы (возможно, еще не записаны)")
        else:
            print(f"  ❌ Директория логов не создана")
            return False
        
        print("  ✅ Система логирования работает корректно")
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка в системе логирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_module():
    """Тестирует модуль работы с базой данных."""
    print("\n🗄️  Тестирование модуля базы данных...")
    
    try:
        from bot.services.activity import ActivityManager
        
        # Создаем тестовую базу данных
        test_db_path = project_root / "bot" / "data" / "test_chat_999.db"
        
        # Удаляем старый тестовый файл, если существует
        if test_db_path.exists():
            test_db_path.unlink()
        
        # Создаем ActivityManager
        manager = ActivityManager(str(test_db_path))
        
        # Тестируем основные методы
        manager.increment_message(999, "test_user")
        manager.store_message(999, "Тестовое сообщение для диагностики")
        
        stats = manager.get_user_stats(999)
        if stats:
            print(f"  ✅ Статистика пользователя получена: {stats}")
        else:
            print(f"  ⚠️  Статистика пользователя не найдена (новый пользователь)")
        
        top_users = manager.get_top_users(5)
        print(f"  ✅ Топ пользователей получен: {len(top_users)} записей")
        
        today_top = manager.get_today_top(5)
        print(f"  ✅ Топ за сегодня получен: {len(today_top)} записей")
        
        # Очищаем
        manager.close()
        
        # Удаляем тестовую базу
        if test_db_path.exists():
            test_db_path.unlink()
            print(f"  ✅ Тестовая база данных очищена")
        
        print("  ✅ Модуль базы данных работает корректно")
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка в модуле базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_command_handlers():
    """Тестирует обработчики команд."""
    print("\n🤖 Тестирование обработчиков команд...")
    
    try:
        from bot.diagnostics import run_diagnostics
        
        print("  🚀 Запуск комплексной диагностики...")
        result = await run_diagnostics()
        
        if result.get("success", False):
            print(f"  ✅ Диагностика завершена успешно")
            
            if "report_file" in result:
                report_path = project_root / result["report_file"]
                if report_path.exists():
                    print(f"  📄 Отчет сохранен: {report_path}")
                    
                    # Читаем и показываем краткий отчет
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_content = f.read()
                    
                    # Извлекаем итоговую статистику
                    import re
                    success_match = re.search(r"Success Rate: (\d+\.?\d*)%", report_content)
                    if success_match:
                        success_rate = float(success_match.group(1))
                        if success_rate == 100:
                            print(f"  🎉 Все тесты пройдены! ({success_rate}%)")
                        else:
                            print(f"  ⚠️  Успешность тестов: {success_rate}%")
                    
                    return True
        else:
            print(f"  ❌ Диагностика не прошла: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка при тестировании команд: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Проверяет наличие необходимых переменных окружения."""
    print("\n🌍 Проверка переменных окружения...")
    
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if env_file.exists():
        print(f"  ✅ Файл .env найден")
        
        # Читаем файл .env
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем наличие токена
            if "TELEGRAM_BOT_TOKEN" in content:
                print(f"  ✅ TELEGRAM_BOT_TOKEN определен в .env")
                
                # Маскируем токен для безопасности
                lines = content.split('\n')
                for line in lines:
                    if line.startswith("TELEGRAM_BOT_TOKEN="):
                        token_value = line.split('=', 1)[1].strip()
                        if token_value:
                            masked_token = token_value[:10] + "..." + token_value[-5:] if len(token_value) > 15 else "***"
                            print(f"  🔐 Токен (маскированный): {masked_token}")
                        else:
                            print(f"  ⚠️  Токен пустой")
                        break
            else:
                print(f"  ⚠️  TELEGRAM_BOT_TOKEN не найден в .env")
                
        except Exception as e:
            print(f"  ❌ Ошибка чтения .env: {e}")
    else:
        print(f"  ⚠️  Файл .env не найден")
        
        if env_example.exists():
            print(f"  📋 Пример файла доступен: {env_example}")
            print(f"  💡 Создайте .env на основе .env.example")
    
    return True

def generate_summary_report(results):
    """Генерирует итоговый отчет."""
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["status"])
    
    print(f"\n📈 Статистика:")
    print(f"  Всего тестов: {total_tests}")
    print(f"  Пройдено: {passed_tests}")
    print(f"  Провалено: {total_tests - passed_tests}")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"  Успешность: {success_rate:.1f}%")
    
    print(f"\n🔍 Результаты по компонентам:")
    for result in results:
        status_icon = "✅" if result["status"] else "❌"
        print(f"  {status_icon} {result['name']}: {result['message']}")
    
    print(f"\n🎯 Рекомендации:")
    
    if success_rate == 100:
        print("  🎉 Все системы работают корректно! Бот готов к запуску.")
        print(f"  🚀 Запустите бота командой: python3 main.py")
    elif success_rate >= 80:
        print("  ⚠️  Большинство систем работают, но есть проблемы.")
        print("  Проверьте указанные выше ошибки перед запуском в продакшн.")
    else:
        print("  ❌ Критические проблемы обнаружены.")
        print("  Необходимо исправить указанные ошибки перед запуском.")
    
    print("\n📋 Следующие шаги:")
    print("  1. Убедитесь, что TELEGRAM_BOT_TOKEN установлен в .env")
    print("  2. Запустите бота: python3 main.py")
    print("  3. Проверьте логи в папке logs/")
    print("  4. Используйте /help в Telegram для проверки команд")
    
    print("\n" + "="*60)
    
    return success_rate == 100

async def main():
    """Основная функция запуска диагностики."""
    print("🚀 ЗАПУСК КОМПЛЕКСНОЙ ДИАГНОСТИКИ KAYO BOT")
    print("="*60)
    
    results = []
    
    # 1. Проверка импортов
    imports_ok = check_imports()
    results.append({
        "name": "Импорты и зависимости",
        "status": imports_ok,
        "message": "Все зависимости установлены" if imports_ok else "Проблемы с зависимостями"
    })
    
    # 2. Проверка структуры проекта
    structure_ok = check_project_structure()
    results.append({
        "name": "Структура проекта",
        "status": structure_ok,
        "message": "Все файлы на месте" if structure_ok else "Отсутствуют важные файлы"
    })
    
    # 3. Проверка переменных окружения
    env_ok = check_environment()
    results.append({
        "name": "Переменные окружения",
        "status": env_ok,
        "message": "Конфигурация проверена" if env_ok else "Проблемы с конфигурацией"
    })
    
    # 4. Тестирование системы логирования
    logging_ok = test_logging_system()
    results.append({
        "name": "Система логирования",
        "status": logging_ok,
        "message": "Логирование работает" if logging_ok else "Ошибки в логировании"
    })
    
    # 5. Тестирование базы данных
    db_ok = test_database_module()
    results.append({
        "name": "База данных",
        "status": db_ok,
        "message": "БД работает корректно" if db_ok else "Проблемы с БД"
    })
    
    # 6. Тестирование обработчиков команд
    commands_ok = await test_command_handlers()
    results.append({
        "name": "Обработчики команд",
        "status": commands_ok,
        "message": "Команды работают" if commands_ok else "Ошибки в обработчиках"
    })
    
    # Генерация итогового отчета
    all_ok = generate_summary_report(results)
    
    # Сохранение отчета в файл
    report_file = project_root / f"diagnostics_summary_{asyncio.get_event_loop().time()}.txt"
    try:
        import io
        output = io.StringIO()
        sys.stdout = output
        
        # Перезапускаем отчет для сохранения
        generate_summary_report(results)
        
        sys.stdout = sys.__stdout__
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(output.getvalue())
        
        print(f"\n📄 Полный отчет сохранен в: {report_file}")
        
    except Exception as e:
        print(f"\n⚠️  Не удалось сохранить отчет: {e}")
    
    # Возвращаем код завершения
    return 0 if all_ok else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Диагностика прервана пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Критическая ошибка при запуске диагностики: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)