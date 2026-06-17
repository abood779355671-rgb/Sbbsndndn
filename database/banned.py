from database.mongo import banned_col
from database.redis_cache import cache_get, cache_set


async def ban(target_id: int, kind: str):
    await banned_col.update_one(
        {"target_id": target_id}, {"$set": {"kind": kind}}, upsert=True
    )
    await cache_set(f"ban:{target_id}", 1, 86400)


async def unban(target_id: int):
    await banned_col.delete_one({"target_id": target_id})
    await cache_set(f"ban:{target_id}", 0, 86400)


async def is_banned(target_id: int):
    cached = await cache_get(f"ban:{target_id}")
    if cached is not None:
        return bool(cached)
    found = bool(await banned_col.find_one({"target_id": target_id}))
    await cache_set(f"ban:{target_id}", 1 if found else 0, 86400)
    return found


async def banned_list():
    return [b async for b in banned_col.find({})]
