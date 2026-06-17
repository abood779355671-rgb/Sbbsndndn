from pymongo.errors import DuplicateKeyError
from database.mongo import queue_col


class DuplicateTrack(Exception):
    """تُرفع عند محاولة إضافة أغنية موجودة مسبقاً."""
    pass


async def save_track(chat_id: int, track: dict):
    clean = {k: v for k, v in track.items() if not k.startswith("_")}
    clean["chat_id"] = chat_id
    try:
        await queue_col.insert_one(clean)
    except DuplicateKeyError:
        raise DuplicateTrack()


async def load_queue(chat_id: int):
    return [t async for t in queue_col.find({"chat_id": chat_id}).sort("_id", 1)]


async def pop_first(chat_id: int):
    return await queue_col.find_one_and_delete({"chat_id": chat_id}, sort=[("_id", 1)])


async def remove_index(chat_id: int, index: int):
    items = await load_queue(chat_id)
    if 0 <= index < len(items):
        await queue_col.delete_one({"_id": items[index]["_id"]})
        return items[index]
    return None


async def clear_queue(chat_id: int):
    await queue_col.delete_many({"chat_id": chat_id})


async def exists(chat_id: int, video_id: str) -> bool:
    doc = await queue_col.find_one({"chat_id": chat_id, "video_id": video_id})
    return doc is not None


async def all_active_chats():
    return await queue_col.distinct("chat_id")
