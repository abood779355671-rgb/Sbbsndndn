import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    ASSISTANT_SESSIONS = [
        s.strip() for s in os.getenv("ASSISTANT_SESSIONS", "").split(",") if s.strip()
    ]
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "music_bot")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))
    COOKIES_FILE = os.getenv("COOKIES_FILE", "")
    DEFAULT_QUALITY = os.getenv("DEFAULT_QUALITY", "high")
    MAX_QUEUE = 50
    SPAM_LIMIT = 5
    SPAM_WINDOW = 10
    SEARCH_CACHE_TTL = 3600
    ADMIN_CACHE_TTL = 3600
    MAX_BACKUP_MB = int(os.getenv("MAX_BACKUP_MB", "25"))


config = Config()
os.makedirs("logs", exist_ok=True)


def validate_config():
    errors = []
    if config.API_ID == 0:
        errors.append("API_ID مطلوب (رقم).")
    if not config.API_HASH:
        errors.append("API_HASH مطلوب.")
    if not config.BOT_TOKEN:
        errors.append("BOT_TOKEN مطلوب.")
    if not config.ASSISTANT_SESSIONS:
        errors.append("ASSISTANT_SESSIONS مطلوب (جلسة مساعد واحدة على الأقل).")
    if config.OWNER_ID == 0:
        errors.append("OWNER_ID مطلوب (معرّف المطور الأساسي).")
    if errors:
        raise SystemExit(
            "❌ إعدادات .env ناقصة:\n- " + "\n- ".join(errors)
        )
