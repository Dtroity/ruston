# Полная инструкция по развертыванию бота ruston на сервере

## Быстрое развертывание (рекомендуется)

Используйте готовый скрипт:

```bash
cd /opt/ruston
chmod +x deploy-server.sh
./deploy-server.sh
```

## Ручное развертывание (пошагово)

### Шаг 1: Подготовка директории

```bash
# Перейти в директорию проекта
cd /opt/ruston

# Если проект еще не клонирован:
# git clone https://github.com/Dtroity/ruston.git /opt/ruston
# cd /opt/ruston
```

### Шаг 2: Остановка старого бота (если запущен)

```bash
# Остановка systemd сервиса (если использовался)
sudo systemctl stop telegram-video-bot 2>/dev/null || true
sudo systemctl disable telegram-video-bot 2>/dev/null || true

# Остановка Docker контейнера (если запущен)
docker-compose -f docker-compose.ruston.yml stop 2>/dev/null || true
```

### Шаг 3: Обновление кода

```bash
# Получение последних изменений
git pull origin main
# или
git pull origin master
```

### Шаг 4: Создание .env файла

```bash
# Создать файл .env (если его нет)
nano .env
```

Содержимое `.env`:

```env
# Обязательные параметры
BOT_TOKEN=your_bot_token_here
CHANNEL_ID=@your_channel

# Опциональные параметры
ADMINS=
ALLOWED_DOMAINS=youtube.com,youtu.be,tiktok.com,vm.tiktok.com,instagram.com,instagr.am
DOWNLOAD_DIR=./downloads

# Настройки защиты от спама
RATE_LIMIT_SECONDS=10
MAX_REQUESTS_PER_MINUTE=5
MAX_REQUESTS_PER_HOUR=20

# Настройки очистки
CLEANUP_DAYS=3
```

### Шаг 5: Создание директорий

```bash
mkdir -p data logs downloads
```

### Шаг 6: Установка прав на скрипты

```bash
chmod +x start-ruston-bot.sh
chmod +x stop-ruston-bot.sh
chmod +x remove-ruston-bot.sh
chmod +x cleanup_downloads.py
chmod +x deploy-server.sh
```

### Шаг 7: Сборка Docker образа

```bash
# Сборка образа (первый раз или после изменений в Dockerfile/requirements.txt)
docker-compose -f docker-compose.ruston.yml build --no-cache
```

### Шаг 8: Запуск бота

```bash
# Запуск через скрипт
./start-ruston-bot.sh

# Или напрямую через docker-compose
docker-compose -f docker-compose.ruston.yml up -d
```

### Шаг 9: Проверка статуса

```bash
# Проверка, что контейнер запущен
docker ps | grep ruston-media-bot

# Просмотр логов
docker-compose -f docker-compose.ruston.yml logs -f

# Проверка последних 50 строк логов
docker-compose -f docker-compose.ruston.yml logs --tail=50
```

### Шаг 10: Проверка изоляции

```bash
# Проверить, что сеть создана
docker network ls | grep ruston

# Проверить, что нет конфликтов с другими ботами
docker ps | grep -E "ruston|antishtraf|anomaly"

# Детальная информация о сети
docker network inspect ruston-media-network
```

## Обновление бота (после изменений в коде)

### Быстрое обновление (без пересборки образа)

```bash
cd /opt/ruston
./stop-ruston-bot.sh
git pull origin main
./start-ruston-bot.sh
```

### Полное обновление (с пересборкой образа)

```bash
cd /opt/ruston
./stop-ruston-bot.sh
git pull origin main
docker-compose -f docker-compose.ruston.yml build --no-cache
./start-ruston-bot.sh
```

## Управление ботом

### Просмотр логов в реальном времени

```bash
docker-compose -f docker-compose.ruston.yml logs -f
```

### Остановка бота

```bash
./stop-ruston-bot.sh
# или
docker-compose -f docker-compose.ruston.yml stop
```

### Перезапуск бота

```bash
# Быстрый перезапуск (после обновления .env)
./restart-ruston-bot.sh

# Или вручную
docker-compose -f docker-compose.ruston.yml restart

# Или полный перезапуск (остановка + запуск)
docker-compose -f docker-compose.ruston.yml stop
docker-compose -f docker-compose.ruston.yml up -d
```

### Обновление .env файла

После изменения `.env` файла необходимо перезагрузить бота:

```bash
# 1. Отредактировать .env
nano .env

# 2. Перезагрузить бота
./restart-ruston-bot.sh

# Или вручную
docker-compose -f docker-compose.ruston.yml restart
```

### Полное удаление бота

```bash
./remove-ruston-bot.sh
# или
docker-compose -f docker-compose.ruston.yml down -v
```

## Ручной запуск очистки

```bash
# Запуск очистки вручную (удаляет файлы старше 3 дней)
docker exec ruston-media-bot python cleanup_downloads.py
```

## Проверка работы функций

### Проверка защиты от спама

1. Отправьте боту ссылку
2. Сразу отправьте еще одну ссылку - должно появиться сообщение о rate limit
3. Отправьте ту же ссылку повторно - должно появиться предупреждение о дубликате

### Проверка автоматической очистки

```bash
# Проверить логи очистки
docker-compose -f docker-compose.ruston.yml logs | grep -i cleanup

# Запустить очистку вручную для теста
docker exec ruston-media-bot python cleanup_downloads.py
```

## Устранение проблем

### Ошибка KeyError: 'ContainerConfig'

Эта ошибка возникает при конфликте старых образов/контейнеров. Исправление:

```bash
# Быстрое исправление через скрипт
chmod +x fix-docker-error.sh
./fix-docker-error.sh
```

Или вручную:

```bash
# 1. Удалить все контейнеры и volumes
docker-compose -f docker-compose.ruston.yml down -v
docker rm -f ruston-media-bot 2>/dev/null || true

# 2. Удалить старые образы
docker images | grep ruston | awk '{print $3}' | xargs docker rmi -f
docker rmi ruston_ruston-bot 2>/dev/null || true

# 3. Очистить Docker кеш
docker system prune -f

# 4. Пересобрать и запустить
docker-compose -f docker-compose.ruston.yml build --no-cache --pull
docker-compose -f docker-compose.ruston.yml up -d
```

### Бот не запускается

```bash
# Проверить логи
docker-compose -f docker-compose.ruston.yml logs

# Проверить наличие .env
ls -la .env

# Проверить содержимое .env (убедитесь, что BOT_TOKEN установлен)
grep BOT_TOKEN .env
```

### Ошибка с токеном

```bash
# Проверить, что токен установлен
grep BOT_TOKEN .env

# Если токен пустой, отредактировать .env
nano .env
```

### Проблемы с Docker

```bash
# Проверить статус Docker
sudo systemctl status docker

# Перезапустить Docker (если нужно)
sudo systemctl restart docker
```

### Проблемы с сетью

```bash
# Удалить старую сеть и пересоздать
docker network rm ruston-media-network 2>/dev/null || true
docker-compose -f docker-compose.ruston.yml up -d
```

## Структура проекта после развертывания

```
/opt/ruston/
├── app.py                      # Основной файл бота
├── cleanup_downloads.py        # Скрипт очистки
├── requirements.txt            # Python зависимости
├── Dockerfile                  # Docker образ
├── docker-compose.ruston.yml   # Docker Compose конфигурация
├── .env                        # Переменные окружения (не в git)
├── .dockerignore              # Исключения для Docker
├── deploy-server.sh           # Скрипт полного развертывания
├── start-ruston-bot.sh        # Скрипт запуска
├── stop-ruston-bot.sh         # Скрипт остановки
├── remove-ruston-bot.sh       # Скрипт удаления
├── data/                      # Данные (volume)
├── logs/                      # Логи (volume)
└── downloads/                 # Загруженные файлы (volume, очищается каждые 3 дня)
```

## Важные замечания

1. **Изоляция**: Бот использует отдельную сеть `ruston-media-network` и не конфликтует с другими ботами
2. **Автоочистка**: Файлы в `downloads/` автоматически удаляются каждые 3 дня
3. **Защита от спама**: Ограничения: 10 сек между запросами, 5 запросов/мин, 20 запросов/час
4. **Админы**: Пользователи из списка `ADMINS` не ограничены защитой от спама
5. **Логи**: Все логи доступны через `docker-compose logs`

## Безопасность

- Файл `.env` не должен быть в git (уже в .gitignore)
- Не используйте общие volumes с другими ботами
- Регулярно обновляйте зависимости: `docker-compose build --no-cache`
- Проверяйте логи на наличие ошибок
