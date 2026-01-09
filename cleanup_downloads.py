#!/usr/bin/env python3
"""
Скрипт для очистки старых файлов из директории downloads.
Удаляет файлы старше 3 дней.
"""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cleanup")

# Директория для загрузок
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
CLEANUP_DAYS = int(os.getenv("CLEANUP_DAYS", "3"))  # Удалять файлы старше N дней

def cleanup_old_files():
    """
    Удаляет файлы из downloads/, которые старше CLEANUP_DAYS дней.
    """
    if not DOWNLOAD_DIR.exists():
        logger.warning(f"Директория {DOWNLOAD_DIR} не существует")
        return
    
    current_time = time.time()
    cutoff_time = current_time - (CLEANUP_DAYS * 24 * 60 * 60)
    
    deleted_count = 0
    deleted_size = 0
    errors = 0
    
    logger.info(f"Начало очистки файлов старше {CLEANUP_DAYS} дней в {DOWNLOAD_DIR}")
    
    try:
        for item in DOWNLOAD_DIR.rglob("*"):
            if item.is_file():
                try:
                    file_mtime = item.stat().st_mtime
                    file_size = item.stat().st_size
                    
                    if file_mtime < cutoff_time:
                        item.unlink()
                        deleted_count += 1
                        deleted_size += file_size
                        logger.debug(f"Удален файл: {item}")
                except OSError as e:
                    logger.error(f"Ошибка при удалении {item}: {e}")
                    errors += 1
        
        # Удаление пустых директорий
        for item in DOWNLOAD_DIR.rglob("*"):
            if item.is_dir():
                try:
                    if not any(item.iterdir()):
                        item.rmdir()
                        logger.debug(f"Удалена пустая директория: {item}")
                except OSError:
                    pass  # Игнорируем ошибки при удалении директорий
        
        logger.info(
            f"Очистка завершена: удалено {deleted_count} файлов "
            f"({deleted_size / (1024 * 1024):.2f} MB), ошибок: {errors}"
        )
        
    except Exception as e:
        logger.exception(f"Критическая ошибка при очистке: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cleanup_old_files()
