from database.redis_cache import cache_get, cache_set, cache_del
from config import config


async def save_admins(chat_id: int, admin_ids: list):
    await cache_set(f"admins:{chat_id}", admin_ids, config.ADMIN_CACHE_TTL)


async def get_admins(chat_id: int):
    return await cache_get(f"admins:{chat_id}")


async def invalidate_admins(chat_id: int):
    await cache_del(f"admins:{chat_id}")
