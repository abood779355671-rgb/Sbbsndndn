import json
import time
import redis.asyncio as aioredis
from config import config

_redis = aioredis.from_url(config.REDIS_URL, decode_responses=True)


async def cache_get(key: str):
    val = await _redis.get(key)
    return json.loads(val) if val else None


async def cache_set(key: str, value, ttl: int):
    await _redis.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)


async def cache_del(key: str):
    await _redis.delete(key)


async def sliding_window_count(key: str, window: int) -> int:
    now = time.time()
    member = f"{now:.6f}"
    pipe = _redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {member: now})
    pipe.zcard(key)
    pipe.expire(key, window + 1)
    res = await pipe.execute()
    return res[2]
