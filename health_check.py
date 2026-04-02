#!/usr/bin/env python3
"""
Простой тест работоспособности Kayo Bot без установки зависимостей.

Проверяет:
1. Структуру проекта
2. Работу системы логирования
3. Модуль базы данных
4. Основные файлы на корректность
"""

import os
import sys
import json
from pathlib import Path

def print_header(text):
    """Печатает заголовок."""
    print("\n" + "="*60)
    print(f"🔍 {text}")
    print("="*60)

def check_project_structure():
    """Проверяет структуру проекта."""
    print_header("ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")
    
    project_root = Path(__file__).parent
    required_files = [
        ("main.py", "Основная точка входа"),
        ("bot/logging.py", "Система логирования"),
        ("bot/diagnostics.py", "Диагностический инструмент"),
        ("bot/services/activity.py", "Модуль базы данных"),
        ("requirements.txt", "Зависимости"),
        (".env", "Конфигурация (создан автоматически)"),
        (".env.example", "Пример конфигурации"),
    ]
    
    all_ok = True
    for file_path, description in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {file_path:30} | {description:30} | {size:,d} байт")
        else:
            print(f"❌ {file_path:30} | {description:30} | НЕ НАЙДЕН")
            all_ok = False
    
    return all_ok

def check_logging_system():
    """Проверяет систему логирования."""
    print_header("ПРОВЕРКА СИСТЕМЫ ЛОГИРОВАНИЯ")
    
    try:
        # Импортируем модуль логирования
        sys.path.insert(0, str(Path(__file__).parent))
        from bot.logging import setup_logging
        
        # Создаем логгер
        logger = setup_logging()
        
        # Проверяем директорию логов
        logs_dir = Path(__file__).parent / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            json_files = list(logs_dir.glob("*.json"))
            
            print(f"✅ Директория логов: {logs_dir}")
            print(f"   📄 Лог-файлов: {len(log_files)}")
            print(f"   📊 JSON-файлов: {len(json_files)}")
            
            if log_files:
                # Показываем последний лог-файл
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                size = latest_log.stat().st_size
                print(f"   🕐 Последний лог: {latest_log.name} ({size:,d} байт)")
                
                # Читаем первые 3 строки
                with open(latest_log, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines()[:3]]
                print(f"   📝 Пример записей:")
                for line in lines[:2]:
                    print(f"     - {line}")
                
                return True
            else:
                print("⚠️  Файлы логов не созданы")
                return False
        else:
            print("❌ Директория логов не создана")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке логирования: {e}")
        return False

def check_database_module():
    """Проверяет модуль базы данных."""
    print_header("ПРОВЕРКА МОДУЛЯ БАЗЫ ДАННЫХ")
    
    try:
        from bot.services.activity import ActivityManager
        
        # Создаем тестовую базу
        test_db = Path(__file__).parent / "bot" / "data" / "test_check.db"
        
        # Удаляем старый тест
        if test_db.exists():
            test_db.unlink()
        
        # Инициализируем менеджер
        manager = ActivityManager(str(test_db))
        
        # Проверяем основные методы
        test_user_id = 99999
        test_username = "test_user_check"
        
        manager.increment_message(test_user_id, test_username)
        manager.store_message(test_user_id, "Тестовое сообщение для проверки")
        
        stats = manager.get_user_stats(test_user_id)
        top_users = manager.get_top_users(3)
        today_top = manager.get_today_top(3)
        
        print(f"✅ Модуль базы данных инициализирован")
        print(f"   👤 Тестовый пользователь: {test_user_id}")
        print(f"   📊 Статистика: {stats}")
        print(f"   🏆 Топ пользователей: {len(top_users)} записей")
        print(f"   📅 Топ за сегодня: {len(today_top)} записей")
        
        # Очищаем
        manager.close()
        if test_db.exists():
            test_db.unlink()
            print(f"   🗑️  Тестовая БД очищена")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в модуле базы данных: {e}")
        return False

def check_python_files():
    """Проверяет Python файлы на синтаксические ошибки."""
    print_header("ПРОВЕРКА SYNTAX PYTHON ФАЙЛОВ")
    
    import ast
    
    project_root = Path(__file__).parent
    python_files = list(project_root.rglob("*.py"))
    
    error_files = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсим AST
            ast.parse(content)
            
            # Пропускаем успешные файлы для краткости
            # print(f"✅ {py_file.relative_to(project_root)}")
            
        except SyntaxError as e:
            rel_path = py_file.relative_to(project_root)
            print(f"❌ {rel_path}: Строка {e.lineno}, Колонка {e.offset}: {e.msg}")
            error_files.append(str(rel_path))
        except Exception as e:
            rel_path = py_file.relative_to(project_root)
            print(f"⚠️  {rel_path}: {e}")
    
    if error_files:
        print(f"\n⚠️  Обнаружены синтаксические ошибки в {len(error_files)} файлах")
        return False
    else:
        print(f"✅ Все {len(python_files)} Python файлов синтаксически корректны")
        return True

def generate_health_report():
    """Генерирует отчет о состоянии здоровья проекта."""
    print_header("ОТЧЕТ О СОСТОЯНИИ ЗДОРОВЬЯ ПРОЕКТА")
    
    checks = [
        ("Структура проекта", check_project_structure()),
        ("Система логирования", check_logging_system()),
        ("Модуль базы данных", check_database_module()),
        ("Синтаксис Python файлов", check_python_files()),
    ]
    
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*60)
    
    total = len(checks)
    passed = sum(1 for _, status in checks if status)
    
    print(f"\n📈 Статистика проверок:")
    print(f"   Всего проверок: {total}")
    print(f"   Пройдено: {passed}")
    print(f"   Не пройдено: {total - passed}")
    print(f"   Успешность: {(passed/total*100):.1f}%")
    
    print(f"\n🔍 Результаты:")
    for name, status in checks:
        icon = "✅" if status else "❌"
        print(f"   {icon} {name}")
    
    print(f"\n🎯 ВЫВОД:")
    if passed == total:
        print("   🎉 ПРОЕКТ АРХИТЕКТУРНО ГОТОВ!")
        print("   📋 Все ключевые компоненты работают корректно.")
        print("   🚀 Осталось только установить зависимости и настроить токен.")
    elif passed >= total * 0.75:
        print("   ⚠️  ПРОЕКТ В ОСНОВНОМ ГОТОВ")
        print("   📋 Большинство компонентов работают, есть незначительные проблемы.")
        print("   🔧 Требуется установка зависимостей и проверка указанных ошибок.")
    else:
        print("   ❌ ТРЕБУЕТСЯ ДОРАБОТКА")
        print("   📋 Обнаружены критические проблемы в архитектуре.")
        print("   🔧 Необходимо исправить указанные ошибки перед продолжением.")
    
    print(f"\n📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("   1. Установите зависимости из requirements.txt")
    print("   2. Настройте реальный токен бота в .env")
    print("   3. Запустите полную диагностику: python3 run_diagnostics.py")
    print("   4. Запустите бота: python3 main.py")
    
    print("\n" + "="*60)
    
    return passed == total

def main():
    """Основная функция."""
    print("🚀 ТЕСТ ЗДОРОВЬЯ АРХИТЕКТУРЫ KAYO BOT")
    print("="*60)
    
    try:
        # Запускаем проверки
        all_ok = generate_health_report()
        
        # Сохраняем отчет
        report_file = Path(__file__).parent / "health_report.txt"
        import io
        import contextlib
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            generate_health_report()
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(output.getvalue())
        
        print(f"\n📄 Полный отчет сохранен в: {report_file}")
        
        return 0 if all_ok else 1
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())