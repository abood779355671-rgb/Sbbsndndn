from motor.motor_asyncio import AsyncIOMotorClient
from config import config
from helpers.logger import LOGGER

_client = AsyncIOMotorClient(config.MONGO_URI)
db = _client[config.DB_NAME]

chats_col = db.chats
users_col = db.users
queue_col = db.queue
banned_col = db.banned
devs_col = db.devs
stats_col = db.stats


async def init_db():
    await chats_col.create_index("chat_id", unique=True)
    await users_col.create_index("user_id", unique=True)
    await queue_col.create_index("chat_id")
    try:
        await queue_col.create_index([("chat_id", 1), ("video_id", 1)], unique=True)
    except Exception:
        # الفهرس الفريد فشل بسبب تكرارات قديمة — نحذف المكررات أولاً ثم نُعيد الإنشاء
        LOGGER.warning("فهرس queue الفريد فشل — جارٍ حذف التكرارات وإعادة الإنشاء...")
        pipeline = [
            {"$group": {"_id": {"chat_id": "$chat_id", "video_id": "$video_id"},
                        "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
        ]
        async for doc in queue_col.aggregate(pipeline):
            # احتفظ بأول وثيقة واحذف الباقي
            await queue_col.delete_many({"_id": {"$in": doc["ids"][1:]}})
        # أسقط الفهرس القديم غير الفريد إن وُجد ثم أنشئ الفريد
        try:
            await queue_col.drop_index("chat_id_1_video_id_1")
        except Exception:
            pass
        await queue_col.create_index([("chat_id", 1), ("video_id", 1)], unique=True)
        LOGGER.info("✅ تم إنشاء فهرس queue الفريد بعد تنظيف التكرارات.")
    try:
        await banned_col.create_index("target_id", unique=True)
    except Exception:
        await banned_col.create_index("target_id")


def close_db():
    _client.close()
