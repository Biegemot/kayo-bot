#!/bin/bash
# Скрипт для пуша через GitHub API

echo "=== ПРОБУЕМ PUSH ЧЕРЕЗ GITHUB API ==="

# Получаем информацию о репозитории
REPO_INFO=$(gh repo view --json name,owner,defaultBranchRef 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ Не удалось получить информацию о репозитории"
    echo "Проверьте gh auth status"
    gh auth status
    exit 1
fi

echo "✅ Репозиторий доступен через gh"

# Пробуем получить последний коммит
LAST_COMMIT=$(git log --oneline -1)
echo "📝 Последний коммит: $LAST_COMMIT"

# Пробуем сделать push через git с debug
echo "🔄 Пробуем git push с отладкой..."
GIT_TRACE=1 timeout 30 git push origin main 2>&1 | grep -E "(error|fatal|remote:|To:|Writing|Compressing)" | head -10

# Альтернатива: создание архива с изменениями
echo "📦 Создаем архив с изменениями..."
git diff --name-only HEAD~3 HEAD > changed_files.txt
echo "📄 Измененные файлы сохранены в changed_files.txt"

# Проверяем, есть ли доступ через gh к API
echo "🔍 Проверяем доступ к GitHub API..."
gh api user 2>&1 | head -5

echo ""
echo "=== ИНСТРУКЦИЯ ДЛЯ РУЧНОГО PUSH ==="
echo ""
echo "Если автоматический push не работает, выполните вручную:"
echo ""
echo "1. Проверьте права доступа:"
echo "   gh auth status"
echo ""
echo "2. Попробуйте push с токеном:"
echo "   git remote set-url origin https://x-access-token:\$GH_TOKEN@github.com/Biegemot/kayo-bot.git"
echo "   git push origin main"
echo ""
echo "3. Или используйте SSH:"
echo "   git remote set-url origin git@github.com:Biegemot/kayo-bot.git"
echo "   git push origin main"
echo ""
echo "4. Если ничего не помогает, создайте форк и PR:"
echo "   gh repo fork --remote"
echo "   git push fork main"
echo "   gh pr create --title 'v0.8.1 release' --body 'Automated release' --base main"