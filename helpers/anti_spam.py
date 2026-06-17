from config import config
from database.redis_cache import sliding_window_count


async def is_spam(user_id: int) -> bool:
    count = await sliding_window_count(f"spam:{user_id}", config.SPAM_WINDOW)
    return count > config.SPAM_LIMIT
