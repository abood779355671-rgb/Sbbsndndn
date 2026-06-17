from database.mongo import chats_col
from database.redis_cache import cache_get, cache_set


async def add_chat(chat_id: int, title: str = ""):
    await chats_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"title": title}, "$setOnInsert": {"enabled": True}},
        upsert=True,
    )


async def all_chats():
    return [c["chat_id"] async for c in chats_col.find({})]


async def count_chats():
    return await chats_col.count_documents({})


async def set_enabled(chat_id: int, enabled: bool):
    await chats_col.update_one(
        {"chat_id": chat_id}, {"$set": {"enabled": enabled}}, upsert=True
    )
    await cache_set(f"enabled:{chat_id}", 1 if enabled else 0, 3600)


async def is_enabled(chat_id: int) -> bool:
    cached = await cache_get(f"enabled:{chat_id}")
    if cached is not None:
        return bool(cached)
    doc = await chats_col.find_one({"chat_id": chat_id})
    enabled = True if not doc else doc.get("enabled", True)
    await cache_set(f"enabled:{chat_id}", 1 if enabled else 0, 3600)
    return enabled
