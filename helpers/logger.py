import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    handlers=[
        RotatingFileHandler("logs/bot.log", maxBytes=5_000_000, backupCount=3),
        logging.StreamHandler(),
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger("MusicBot")

_bot_ref = None


def set_log_bot(bot):
    global _bot_ref
    _bot_ref = bot


async def log_to_group(text: str):
    from config import config
    if _bot_ref and config.LOG_GROUP_ID:
        try:
            await _bot_ref.send_message(config.LOG_GROUP_ID, text)
        except Exception as e:
            LOGGER.warning(f"log_to_group: {e}")
