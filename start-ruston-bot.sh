#!/bin/bash

cd /opt/ruston

if [ ! -f .env ]; then
    echo "❌ Ошибка: файл .env не найден!"
    echo "💡 Создайте .env файл на основе .env.example"
    exit 1
fi

# Создание необходимых директорий
mkdir -p data logs downloads

echo "🚀 Запуск бота ruston..."
docker-compose -f docker-compose.ruston.yml up -d

sleep 2

if docker ps | grep -q ruston-media-bot; then
    echo "✅ Бот запущен успешно!"
    echo ""
    echo "📋 Просмотр логов: docker-compose -f docker-compose.ruston.yml logs -f"
    echo "🛑 Остановка: ./stop-ruston-bot.sh"
    echo "🗑️  Удаление: ./remove-ruston-bot.sh"
else
    echo "❌ Ошибка запуска бота!"
    echo "Проверьте логи: docker-compose -f docker-compose.ruston.yml logs"
    exit 1
fi
