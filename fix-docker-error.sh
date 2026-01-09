#!/bin/bash

# Скрипт для исправления ошибки KeyError: 'ContainerConfig'
# Использование: ./fix-docker-error.sh

set -e

echo "🔧 Исправление ошибки Docker Compose..."

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Остановка и удаление всех контейнеров ruston
echo ""
echo -e "${YELLOW}Шаг 1: Удаление контейнеров...${NC}"
docker-compose -f docker-compose.ruston.yml down -v 2>/dev/null || true
docker rm -f ruston-media-bot 2>/dev/null || true
echo -e "${GREEN}✅ Контейнеры удалены${NC}"

# 2. Удаление образов ruston
echo ""
echo -e "${YELLOW}Шаг 2: Удаление образов...${NC}"
docker images | grep ruston | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
docker rmi ruston_ruston-bot 2>/dev/null || true
echo -e "${GREEN}✅ Образы удалены${NC}"

# 3. Очистка Docker системы (опционально)
echo ""
echo -e "${YELLOW}Шаг 3: Очистка Docker системы...${NC}"
echo "Выполнить полную очистку Docker? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    docker system prune -a -f
    echo -e "${GREEN}✅ Docker система очищена${NC}"
else
    docker system prune -f
    echo -e "${GREEN}✅ Базовая очистка выполнена${NC}"
fi

# 4. Пересборка образа
echo ""
echo -e "${YELLOW}Шаг 4: Пересборка образа...${NC}"
docker-compose -f docker-compose.ruston.yml build --no-cache --pull

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Образ успешно собран${NC}"
else
    echo -e "${RED}❌ Ошибка при сборке образа${NC}"
    exit 1
fi

# 5. Запуск контейнера
echo ""
echo -e "${YELLOW}Шаг 5: Запуск контейнера...${NC}"
docker-compose -f docker-compose.ruston.yml up -d

sleep 3

# 6. Проверка статуса
echo ""
echo -e "${YELLOW}Шаг 6: Проверка статуса...${NC}"
if docker ps | grep -q ruston-media-bot; then
    echo -e "${GREEN}✅ Бот успешно запущен!${NC}"
    echo ""
    docker ps | grep ruston-media-bot
    echo ""
    echo "Просмотр логов: docker-compose -f docker-compose.ruston.yml logs -f"
else
    echo -e "${RED}❌ Бот не запущен!${NC}"
    echo "Проверьте логи: docker-compose -f docker-compose.ruston.yml logs"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Проблема исправлена!${NC}"
