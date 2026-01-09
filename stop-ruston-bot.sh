#!/bin/bash

cd /opt/ruston

echo "🛑 Остановка бота ruston..."

docker-compose -f docker-compose.ruston.yml stop

if [ $? -eq 0 ]; then
    echo "✅ Бот остановлен"
else
    echo "❌ Ошибка остановки бота"
    exit 1
fi
