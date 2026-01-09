FROM python:3.11-slim

# Установка системных зависимостей для работы с медиа
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание директорий для данных
RUN mkdir -p data logs downloads

ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "app.py"]
