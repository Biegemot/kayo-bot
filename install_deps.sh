#!/usr/bin/env bash
# Скрипт для установки зависимостей Kayo Bot

set -e

echo "🔧 Установка зависимостей Kayo Bot..."

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION найден"

# Проверяем pip
if ! command -v pip3 &> /dev/null; then
    echo "⚠️  pip3 не найден, пытаемся установить..."
    
    # Пробуем установить pip через get-pip.py
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python3 /tmp/get-pip.py --user
    rm /tmp/get-pip.py
    
    # Добавляем pip в PATH если установлен в user
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v pip3 &> /dev/null; then
        echo "❌ Не удалось установить pip3"
        exit 1
    fi
fi

echo "✅ pip3 найден: $(pip3 --version)"

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости из requirements.txt..."

# Создаем виртуальное окружение альтернативным способом
VENV_DIR=".venv_kayo"
if [ ! -d "$VENV_DIR" ]; then
    echo "🏗️  Создаем виртуальное окружение..."
    python3 -m venv "$VENV_DIR" || {
        # Альтернатива если venv не работает
        echo "⚠️  venv не работает, используем virtualenv..."
        pip3 install --user virtualenv
        virtualenv "$VENV_DIR"
    }
fi

# Активируем виртуальное окружение
source "$VENV_DIR/bin/activate"

# Устанавливаем зависимости
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    
    # Проверяем установленные пакеты
    echo "📊 Установленные пакеты:"
    pip3 list | grep -E "(telegram|dotenv|blessed)"
else
    echo "❌ Файл requirements.txt не найден"
    exit 1
fi

# Создаем тестовый скрипт для проверки зависимостей
cat > test_imports.py << 'EOF'
#!/usr/bin/env python3
import sys

def test_imports():
    print("🔍 Тестирование импортов...")
    
    modules = [
        ("telegram", "python-telegram-bot"),
        ("dotenv", "python-dotenv"),
        ("blessed", "blessed"),
    ]
    
    all_ok = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError as e:
            print(f"  ❌ {display_name} - {e}")
            all_ok = False
    
    if all_ok:
        print("🎉 Все зависимости установлены успешно!")
        return 0
    else:
        print("⚠️  Некоторые зависимости не установлены")
        return 1

if __name__ == "__main__":
    sys.exit(test_imports())
EOF

# Запускаем тест
echo "🧪 Запускаем тест зависимостей..."
python3 test_imports.py
TEST_RESULT=$?

rm test_imports.py

# Деактивируем виртуальное окружение
deactivate

if [ $TEST_RESULT -eq 0 ]; then
    echo "🎉 Зависимости успешно установлены!"
    echo ""
    echo "🚀 Для запуска бота используйте:"
    echo "   source $VENV_DIR/bin/activate"
    echo "   python3 main.py"
    echo ""
    echo "📁 Виртуальное окружение создано в: $VENV_DIR"
else
    echo "❌ Не удалось установить все зависимости"
    exit 1
fi