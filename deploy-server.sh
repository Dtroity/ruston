#!/bin/bash

# Скрипт полного развертывания бота ruston на сервере
# Использование: ./deploy-server.sh

set -e  # Остановка при ошибке

echo "🚀 Начало развертывания бота ruston..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка, что скрипт запущен из правильной директории
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Ошибка: файл app.py не найден!${NC}"
    echo "Убедитесь, что вы находитесь в директории /opt/ruston"
    exit 1
fi

# 1. Остановка старого бота (если запущен через systemd)
echo ""
echo -e "${YELLOW}📋 Шаг 1: Остановка старого бота (если запущен)...${NC}"
if systemctl is-active --quiet telegram-video-bot 2>/dev/null; then
    echo "Остановка systemd сервиса..."
    sudo systemctl stop telegram-video-bot
    sudo systemctl disable telegram-video-bot
    echo -e "${GREEN}✅ Старый бот остановлен${NC}"
else
    echo "Старый бот не запущен через systemd"
fi

# Остановка и удаление Docker контейнера (если запущен)
if docker ps -a | grep -q ruston-media-bot; then
    echo "Остановка и удаление старого Docker контейнера..."
    docker-compose -f docker-compose.ruston.yml down 2>/dev/null || true
    docker rm -f ruston-media-bot 2>/dev/null || true
    echo -e "${GREEN}✅ Старый Docker контейнер удален${NC}"
fi

# Удаление старого образа (если есть) для избежания конфликтов
if docker images | grep -q ruston; then
    echo "Удаление старого Docker образа..."
    docker rmi ruston_ruston-bot 2>/dev/null || true
    docker rmi $(docker images | grep ruston | awk '{print $3}') 2>/dev/null || true
    echo -e "${GREEN}✅ Старые образы удалены${NC}"
fi

# 2. Обновление кода из репозитория
echo ""
echo -e "${YELLOW}📋 Шаг 2: Обновление кода из репозитория...${NC}"
if [ -d ".git" ]; then
    echo "Получение последних изменений..."
    git pull origin main || git pull origin master
    echo -e "${GREEN}✅ Код обновлен${NC}"
else
    echo -e "${YELLOW}⚠️  Директория .git не найдена. Пропускаем git pull.${NC}"
fi

# 3. Проверка наличия Docker и Docker Compose
echo ""
echo -e "${YELLOW}📋 Шаг 3: Проверка Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен!${NC}"
    echo "Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен!${NC}"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker установлен${NC}"

# 4. Проверка и создание .env файла
echo ""
echo -e "${YELLOW}📋 Шаг 4: Проверка .env файла...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo ""
    echo "Создайте файл .env со следующим содержимым:"
    echo ""
    echo "BOT_TOKEN=your_bot_token_here"
    echo "CHANNEL_ID=@your_channel"
    echo "ADMINS="
    echo "ALLOWED_DOMAINS=youtube.com,youtu.be,tiktok.com,vm.tiktok.com,instagram.com,instagr.am"
    echo "DOWNLOAD_DIR=./downloads"
    echo "RATE_LIMIT_SECONDS=10"
    echo "MAX_REQUESTS_PER_MINUTE=5"
    echo "MAX_REQUESTS_PER_HOUR=20"
    echo "CLEANUP_DAYS=3"
    echo ""
    echo "Создать файл сейчас? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        nano .env
    else
        echo -e "${RED}❌ Необходимо создать .env файл перед продолжением${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Файл .env найден${NC}"
fi

# Проверка обязательных переменных
if ! grep -q "BOT_TOKEN=" .env || [ -z "$(grep BOT_TOKEN .env | cut -d'=' -f2)" ]; then
    echo -e "${RED}❌ BOT_TOKEN не установлен в .env файле!${NC}"
    exit 1
fi

# 5. Создание необходимых директорий
echo ""
echo -e "${YELLOW}📋 Шаг 5: Создание директорий...${NC}"
mkdir -p data logs downloads
echo -e "${GREEN}✅ Директории созданы${NC}"

# 6. Установка прав на скрипты
echo ""
echo -e "${YELLOW}📋 Шаг 6: Установка прав на скрипты...${NC}"
chmod +x start-ruston-bot.sh stop-ruston-bot.sh remove-ruston-bot.sh cleanup_downloads.py 2>/dev/null || true
echo -e "${GREEN}✅ Права установлены${NC}"

# 7. Очистка Docker (опционально, для решения проблем)
echo ""
echo -e "${YELLOW}📋 Шаг 7: Очистка Docker кеша (опционально)...${NC}"
echo "Очистить Docker кеш? Это может помочь при ошибках сборки (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    docker system prune -f
    echo -e "${GREEN}✅ Docker кеш очищен${NC}"
fi

# 8. Сборка Docker образа
echo ""
echo -e "${YELLOW}📋 Шаг 8: Сборка Docker образа...${NC}"
echo "Это может занять несколько минут..."
docker-compose -f docker-compose.ruston.yml build --no-cache --pull

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker образ собран${NC}"
else
    echo -e "${RED}❌ Ошибка при сборке Docker образа${NC}"
    exit 1
fi

# 9. Запуск бота
echo ""
echo -e "${YELLOW}📋 Шаг 9: Запуск бота...${NC}"
# Убеждаемся, что старые контейнеры удалены перед запуском
docker-compose -f docker-compose.ruston.yml down 2>/dev/null || true
docker-compose -f docker-compose.ruston.yml up -d

sleep 3

# 10. Проверка статуса
echo ""
echo -e "${YELLOW}📋 Шаг 10: Проверка статуса...${NC}"
if docker ps | grep -q ruston-media-bot; then
    echo -e "${GREEN}✅ Бот успешно запущен!${NC}"
    echo ""
    echo "📊 Информация о контейнере:"
    docker ps | grep ruston-media-bot
    echo ""
    echo "📋 Полезные команды:"
    echo "  Просмотр логов: docker-compose -f docker-compose.ruston.yml logs -f"
    echo "  Остановка: ./stop-ruston-bot.sh"
    echo "  Перезапуск: docker-compose -f docker-compose.ruston.yml restart"
    echo "  Удаление: ./remove-ruston-bot.sh"
    echo ""
    echo "🔍 Проверка изоляции:"
    docker network ls | grep ruston || echo "  Сеть ruston-media-network создана"
    echo ""
    echo "📝 Последние логи:"
    docker-compose -f docker-compose.ruston.yml logs --tail=20
else
    echo -e "${RED}❌ Бот не запущен!${NC}"
    echo "Проверьте логи: docker-compose -f docker-compose.ruston.yml logs"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Развертывание завершено успешно!${NC}"
