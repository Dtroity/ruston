
import os
import re
import sys
import asyncio
import logging
import tempfile
import time
import threading
from collections import defaultdict, deque
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputFile
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

import yt_dlp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
ADMINS = [x.strip() for x in os.getenv("ADMINS", "").split(",") if x.strip()]
ALLOWED_DOMAINS = [x.strip().lower() for x in os.getenv("ALLOWED_DOMAINS", "youtube.com,youtu.be,tiktok.com,vm.tiktok.com,instagram.com,instagr.am").split(",")]
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Настройки защиты от спама
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "10"))  # Минимум секунд между запросами
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "5"))  # Максимум запросов в минуту
MAX_REQUESTS_PER_HOUR = int(os.getenv("MAX_REQUESTS_PER_HOUR", "20"))  # Максимум запросов в час

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("telebot")

# Структуры для защиты от спама
user_last_request: Dict[int, float] = {}  # user_id -> timestamp последнего запроса
user_request_times: Dict[int, deque] = defaultdict(lambda: deque())  # user_id -> очередь времен запросов
user_last_url: Dict[int, str] = {}  # user_id -> последний URL

URL_RE = re.compile(
    r'^(https?://)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})(/[^\s]*)?$',
    re.IGNORECASE
)

DISCLAIMER = (
    "⚠️ Используйте только для собственных материалов или с разрешения правообладателя. "
    "Бот: @ruston_bot"
)

def is_allowed_domain(url: str) -> bool:
    m = URL_RE.match(url.strip())
    if not m:
        return False
    host = m.group(2).lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)

async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning("Subscription check failed: %s", e)
        return False

def check_spam_protection(user_id: int, url: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет защиту от спама.
    Возвращает (is_spam, error_message)
    """
    current_time = time.time()
    
    # Админы не ограничены
    if user_id in ADMINS:
        user_last_request[user_id] = current_time
        user_request_times[user_id].append(current_time)
        user_last_url[user_id] = url
        return False, None
    
    # Проверка минимального интервала между запросами
    if user_id in user_last_request:
        time_since_last = current_time - user_last_request[user_id]
        if time_since_last < RATE_LIMIT_SECONDS:
            remaining = int(RATE_LIMIT_SECONDS - time_since_last) + 1
            return True, f"⏳ Слишком частые запросы. Подождите {remaining} секунд перед следующим запросом."
    
    # Проверка на повторяющиеся URL
    if user_id in user_last_url and user_last_url[user_id] == url:
        return True, "⚠️ Вы уже запрашивали этот URL. Пожалуйста, отправьте другую ссылку."
    
    # Очистка старых записей (старше часа)
    user_requests = user_request_times[user_id]
    while user_requests and current_time - user_requests[0] > 3600:
        user_requests.popleft()
    
    # Проверка лимита запросов в минуту
    recent_minute = [t for t in user_requests if current_time - t <= 60]
    if len(recent_minute) >= MAX_REQUESTS_PER_MINUTE:
        return True, f"⏳ Превышен лимит запросов ({MAX_REQUESTS_PER_MINUTE} в минуту). Подождите немного."
    
    # Проверка лимита запросов в час
    recent_hour = [t for t in user_requests if current_time - t <= 3600]
    if len(recent_hour) >= MAX_REQUESTS_PER_HOUR:
        return True, f"⏳ Превышен лимит запросов ({MAX_REQUESTS_PER_HOUR} в час). Подождите час."
    
    # Обновление данных
    user_last_request[user_id] = current_time
    user_request_times[user_id].append(current_time)
    user_last_url[user_id] = url
    
    return False, None

def ytdlp_download(url: str, tmp_dir: Path) -> Tuple[Optional[Path], Optional[str]]:
    ydl_opts = {
        "outtmpl": str(tmp_dir / "%(title).80s.%(ext)s"),
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 2,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base = Path(filename).with_suffix("")
        for f in tmp_dir.iterdir():
            if f.is_file() and f.stem.startswith(base.stem):
                return f, "video/mp4"
        return Path(filename), "video/mp4"

def build_subscribe_keyboard() -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_ID[1:]}" if CHANNEL_ID and CHANNEL_ID.startswith("@") else None)],
        [InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_sub")]
    ]
    if CHANNEL_ID and CHANNEL_ID.startswith("-100"):
        btns = [[InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_sub")]]
    return InlineKeyboardMarkup(btns)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not CHANNEL_ID:
        await update.message.reply_text("Бот не настроен: отсутствует CHANNEL_ID.")
        return

    if await is_subscribed(user.id, context):
        await update.message.reply_text(
            "✅ Доступ разрешён. Пришлите ссылку на видео (YouTube / TikTok / Instagram).\n\n" + DISCLAIMER
        )
    else:
        await update.message.reply_text(
            "Чтобы пользоваться ботом, подпишитесь на канал и затем нажмите «Проверить подписку».",
            reply_markup=build_subscribe_keyboard()
        )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправьте ссылку на видео (YouTube / TikTok / Instagram).\n"
        "Перед обработкой требуется подписка на канал.\n\n" + DISCLAIMER
    )

async def check_subscription_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await is_subscribed(user_id, context):
        await query.edit_message_text(
            "✅ Спасибо за подписку! Теперь отправьте ссылку на видео.\n\n" + DISCLAIMER
        )
    else:
        await query.edit_message_text(
            "❌ Подписка не обнаружена. Подпишитесь и нажмите «Проверить подписку».",
            reply_markup=build_subscribe_keyboard()
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (update.message.text or "").strip()

    if not await is_subscribed(user.id, context):
        await update.message.reply_text(
            "Доступ только для подписчиков. Пожалуйста, подпишитесь и нажмите «Проверить подписку».",
            reply_markup=build_subscribe_keyboard()
        )
        return

    if not text.lower().startswith(("http://", "https://")) or not is_allowed_domain(text):
        await update.message.reply_text(
            "Пришлите **прямую ссылку** на видео с поддерживаемого домена:\n"
            f"`{', '.join(ALLOWED_DOMAINS)}`\n\n" + DISCLAIMER,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Проверка защиты от спама
    is_spam, spam_message = check_spam_protection(user.id, text)
    if is_spam:
        logger.warning(f"Spam protection triggered for user {user.id}: {spam_message}")
        await update.message.reply_text(spam_message)
        return

    await update.message.reply_text("⏬ Загружаю видео, подождите...")

    try:
        with tempfile.TemporaryDirectory(dir=DOWNLOAD_DIR) as td:
            tmp_dir = Path(td)
            file_path, mime = await asyncio.to_thread(ytdlp_download, text, tmp_dir)
            if not file_path or not file_path.exists():
                await update.message.reply_text("Не удалось скачать видео. Попробуйте другую ссылку.")
                return

            size_mb = file_path.stat().st_size / (1024 * 1024)
            caption = f"Готово ✅ ({size_mb:.1f} MB)\n" + DISCLAIMER

            try:
                await update.message.reply_video(
                    video=InputFile(file_path.open("rb")),
                    caption=caption
                )
            except Exception as e:
                logger.warning("sendVideo failed, fallback to document: %s", e)
                await update.message.reply_document(
                    document=InputFile(file_path.open("rb"), filename=file_path.name),
                    caption=caption
                )

    except Exception as e:
        logger.exception("Download error: %s", e)
        await update.message.reply_text("Произошла ошибка при загрузке. Попробуйте позже или другую ссылку.")

def cleanup_task_loop_thread():
    """
    Фоновая задача для автоматической очистки старых файлов из downloads/.
    Запускается каждые 3 дня в отдельном потоке.
    """
    import subprocess
    CLEANUP_INTERVAL = 3 * 24 * 60 * 60  # 3 дня в секундах
    
    # Первый запуск через 3 дня после старта
    time.sleep(CLEANUP_INTERVAL)
    
    while True:
        try:
            logger.info("Запуск автоматической очистки старых файлов...")
            result = subprocess.run(
                [sys.executable, "cleanup_downloads.py"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            if result.returncode == 0:
                logger.info("Очистка завершена успешно")
                if result.stdout:
                    logger.info(f"Вывод очистки: {result.stdout}")
            else:
                logger.error(f"Ошибка при очистке: {result.stderr}")
            
            # Ожидание до следующей очистки
            time.sleep(CLEANUP_INTERVAL)
        except Exception as e:
            logger.exception(f"Ошибка в задаче очистки: {e}")
            # При ошибке ждем час перед повтором
            time.sleep(3600)

def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set")
    if not CHANNEL_ID:
        logger.warning("CHANNEL_ID is empty — подписочный гейт работать не будет.")

    app = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(check_subscription_cb, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запуск фоновой задачи очистки в отдельном потоке
    cleanup_thread = threading.Thread(target=cleanup_task_loop_thread, daemon=True)
    cleanup_thread.start()
    logger.info("Фоновая задача очистки запущена в отдельном потоке")

    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
