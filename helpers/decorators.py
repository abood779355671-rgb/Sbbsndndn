from functools import wraps
from pyrogram.types import Message
from helpers.admin_cache import is_user_admin
from helpers.logger import LOGGER
from database.devs import is_dev
from database.banned import is_banned
from database.chats import is_enabled


def admin_only(func):
    @wraps(func)
    async def wrapper(client, message: Message, *a, **k):
        if message.from_user is None or message.from_user.is_bot:
            return
        uid = message.from_user.id
        if not await is_user_admin(client, message.chat.id, uid) and not await is_dev(uid):
            return await message.reply("❌ هذا الأمر للمشرفين فقط.")
        return await func(client, message, *a, **k)
    return wrapper


def dev_only(func):
    @wraps(func)
    async def wrapper(client, message: Message, *a, **k):
        if not message.from_user or not await is_dev(message.from_user.id):
            return
        return await func(client, message, *a, **k)
    return wrapper


def guard(func):
    @wraps(func)
    async def wrapper(client, message: Message, *a, **k):
        u = message.from_user
        if not u or u.is_bot:
            return
        if await is_banned(u.id) or await is_banned(message.chat.id):
            return
        if not await is_enabled(message.chat.id) and not await is_dev(u.id):
            return
        return await func(client, message, *a, **k)
    return wrapper


def safe(func):
    """#14: رسالة عامة للمستخدم، التفاصيل في اللوق فقط (لا تسريب)."""
    @wraps(func)
    async def wrapper(client, message: Message, *a, **k):
        try:
            return await func(client, message, *a, **k)
        except Exception:
            LOGGER.exception(f"handler error: {func.__name__}")
            try:
                await message.reply("⚠️ حدث خطأ غير متوقع. حاول لاحقاً.")
            except Exception:
                pass
    return wrapper
