# Инструкция по развертыванию бота ruston в Docker

## Требования

- Docker и Docker Compose установлены на сервере
- Проект находится в `/opt/ruston`

## Быстрый старт

### 1. Подготовка на сервере

```bash
# Перейти в директорию проекта
cd /opt/ruston

# Убедиться, что файл .env существует
# Если нет - создать на основе примера:
# cp .env.example .env
# nano .env
```

### 2. Настройка .env файла

Создайте файл `.env` со следующим содержимым:

```env
BOT_TOKEN=your_bot_token_here
CHANNEL_ID=@your_channel
ADMINS=
ALLOWED_DOMAINS=youtube.com,youtu.be,tiktok.com,vm.tiktok.com,instagram.com,instagr.am
DOWNLOAD_DIR=./downloads
```

### 3. Установка прав на скрипты

```bash
chmod +x start-ruston-bot.sh
chmod +x stop-ruston-bot.sh
chmod +x remove-ruston-bot.sh
```

### 4. Запуск бота

```bash
./start-ruston-bot.sh
```

## Управление ботом

### Запуск
```bash
./start-ruston-bot.sh
# или
docker-compose -f docker-compose.ruston.yml up -d
```

### Остановка
```bash
./stop-ruston-bot.sh
# или
docker-compose -f docker-compose.ruston.yml stop
```

### Просмотр логов
```bash
docker-compose -f docker-compose.ruston.yml logs -f
```

### Перезапуск
```bash
docker-compose -f docker-compose.ruston.yml restart
```

### Полное удаление
```bash
./remove-ruston-bot.sh
# или
docker-compose -f docker-compose.ruston.yml down -v
```

## Проверка изоляции

После запуска проверьте, что бот изолирован от других ботов:

```bash
# Проверить сеть бота
docker network inspect ruston-media-network

# Проверить, что контейнеры не конфликтуют
docker ps | grep -E "ruston|antishtraf|anomaly"

# Проверить статус контейнера
docker ps | grep ruston-media-bot
```

## Миграция с systemd на Docker

Если бот ранее запускался через systemd:

1. Остановите systemd сервис:
```bash
sudo systemctl stop telegram-video-bot
sudo systemctl disable telegram-video-bot
```

2. Скопируйте данные (если нужно):
```bash
# Если были загруженные файлы
cp -r /opt/ruston/downloads/* ./downloads/ 2>/dev/null || true
```

3. Запустите через Docker:
```bash
./start-ruston-bot.sh
```

## Обновление бота

1. Остановите бота:
```bash
./stop-ruston-bot.sh
```

2. Обновите код:
```bash
git pull
```

3. Пересоберите образ (если изменились зависимости):
```bash
docker-compose -f docker-compose.ruston.yml build
```

4. Запустите бота:
```bash
./start-ruston-bot.sh
```

## Структура проекта

```
/opt/ruston/
├── app.py                      # Основной файл бота
├── requirements.txt            # Python зависимости
├── Dockerfile                  # Docker образ
├── docker-compose.ruston.yml   # Docker Compose конфигурация
├── .env                        # Переменные окружения (не в git)
├── .dockerignore              # Исключения для Docker
├── start-ruston-bot.sh        # Скрипт запуска
├── stop-ruston-bot.sh         # Скрипт остановки
├── remove-ruston-bot.sh       # Скрипт удаления
├── data/                      # Данные (volume)
├── logs/                      # Логи (volume)
└── downloads/                 # Загруженные файлы (volume)
```

## Особенности конфигурации

- **Изолированная сеть**: `ruston-media-network` (не конфликтует с другими ботами)
- **Уникальное имя контейнера**: `ruston-media-bot`
- **Автозапуск**: `restart: unless-stopped`
- **Volumes**: Локальные директории в проекте (легко удалить)
- **Порты**: Не используются (только Telegram API)

## Устранение проблем

### Бот не запускается

1. Проверьте логи:
```bash
docker-compose -f docker-compose.ruston.yml logs
```

2. Проверьте наличие .env файла:
```bash
ls -la /opt/ruston/.env
```

3. Проверьте права на файлы:
```bash
ls -la /opt/ruston/
```

### Ошибка с токеном

Убедитесь, что в `.env` файле указан правильный `BOT_TOKEN`.

### Проблемы с загрузкой видео

Проверьте, что `ffmpeg` установлен в контейнере:
```bash
docker exec ruston-media-bot ffmpeg -version
```

## Безопасность

- Файл `.env` не должен быть в git (уже в .gitignore)
- Не используйте общие volumes с другими ботами
- Не используйте общие сети с другими ботами
- Регулярно обновляйте зависимости
