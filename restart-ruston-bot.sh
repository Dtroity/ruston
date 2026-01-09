#!/bin/bash

# Скрипт для перезагрузки бота ruston
# Используется после обновления .env файла или изменений в коде

cd /opt/ruston

echo "🔄 Перезагрузка бота ruston..."

# Остановка контейнера
echo "Остановка контейнера..."
docker-compose -f docker-compose.ruston.yml stop

# Запуск контейнера (он автоматически подхватит новый .env)
echo "Запуск контейнера с обновленным .env..."
docker-compose -f docker-compose.ruston.yml up -d

sleep 2

# Проверка статуса
if docker ps | grep -q ruston-media-bot; then
    echo "✅ Бот успешно перезагружен!"
    echo ""
    echo "📋 Просмотр логов: docker-compose -f docker-compose.ruston.yml logs -f"
    echo "📊 Статус: docker ps | grep ruston-media-bot"
else
    echo "❌ Ошибка при перезагрузке бота!"
    echo "Проверьте логи: docker-compose -f docker-compose.ruston.yml logs"
    exit 1
fi
