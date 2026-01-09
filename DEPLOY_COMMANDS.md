# Команды для обновления бота на сервере

## После коммита и пуша изменений

Выполните следующие команды на сервере:

### 1. Перейти в директорию проекта
```bash
cd /opt/ruston
```

### 2. Остановить бота (если запущен)
```bash
./stop-ruston-bot.sh
# или
docker-compose -f docker-compose.ruston.yml stop
```

### 3. Обновить код из репозитория
```bash
git pull origin main
# или
git pull origin master
```

### 4. Пересобрать Docker образ (если изменились зависимости или Dockerfile)
```bash
docker-compose -f docker-compose.ruston.yml build --no-cache
```

### 5. Запустить бота
```bash
./start-ruston-bot.sh
# или
docker-compose -f docker-compose.ruston.yml up -d
```

### 6. Проверить статус
```bash
docker ps | grep ruston-media-bot
docker-compose -f docker-compose.ruston.yml logs --tail=50
```

## Быстрое обновление (одной командой)

Если нужно только обновить код без пересборки образа:

```bash
cd /opt/ruston && \
./stop-ruston-bot.sh && \
git pull && \
./start-ruston-bot.sh
```

## Полное обновление (с пересборкой)

Если изменились зависимости или Dockerfile:

```bash
cd /opt/ruston && \
./stop-ruston-bot.sh && \
git pull && \
docker-compose -f docker-compose.ruston.yml build --no-cache && \
./start-ruston-bot.sh
```

## Проверка изоляции после обновления

```bash
# Проверить, что контейнер запущен
docker ps | grep ruston-media-bot

# Проверить сеть
docker network ls | grep ruston

# Проверить, что нет конфликтов с другими ботами
docker ps | grep -E "ruston|antishtraf|anomaly"
```
