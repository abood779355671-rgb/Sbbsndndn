import io
import datetime
from bson import json_util
from pyrogram import Client
from pyrogram.types import Message
from helpers.filters import cmd
from helpers.decorators import dev_only
from helpers.logger import LOGGER
from config import config
from database.mongo import (
    db, chats_col, users_col, banned_col, devs_col, stats_col,
)

BACKUP = cmd("نسخ_احتياطي")
RESTORE = cmd("استعادة")

COLLECTIONS = {
    "chats": chats_col, "users": users_col,
    "banned": banned_col, "devs": devs_col, "stats": stats_col,
}


async def _dump() -> bytes:
    data = {}
    for name, col in COLLECTIONS.items():
        data[name] = [doc async for doc in col.find({})]
    return json_util.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


async def _restore(raw: bytes) -> dict:
    data = json_util.loads(raw.decode("utf-8"))
    for name in COLLECTIONS:
        if name not in data or not isinstance(data[name], list):
            raise ValueError(f"ملف النسخة غير صالح: '{name}' مفقودة أو تالفة.")

    report = {}
    tmp_names = {}
    try:
        for name in COLLECTIONS:
            docs = data[name]
            tmp = f"{name}_tmp_restore"
            tmp_names[name] = tmp
            await db[tmp].drop()
            if docs:
                await db[tmp].insert_many(docs)
            report[name] = len(docs)
    except Exception:
        for tmp in tmp_names.values():
            await db[tmp].drop()
        raise

    for name, tmp in tmp_names.items():
        await db[tmp].rename(name, dropTarget=True)
    return report


def register(app: Client, calls):

    @app.on_message(BACKUP)
    @dev_only
    async def backup_h(client, message: Message):
        m = await message.reply("💾 جاري إنشاء النسخة الاحتياطية...")
        try:
            blob = await _dump()
        except Exception as e:
            LOGGER.exception("backup")
            return await m.edit(f"⚠️ فشل النسخ: {e}")
        stamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file = io.BytesIO(blob)
        file.name = f"backup_{stamp}.json"
        await message.reply_document(
            file, caption=f"💾 نسخة احتياطية\nالتاريخ: {stamp} UTC\nالحجم: {len(blob)} bytes"
        )
        await m.delete()

    @app.on_message(RESTORE)
    @dev_only
    async def restore_h(client, message: Message):
        reply = message.reply_to_message
        if not reply or not reply.document:
            return await message.reply("✳️ رد على ملف النسخة (.json) بكلمة: استعادة")
        if reply.document.file_size > config.MAX_BACKUP_MB * 1024 * 1024:
            return await message.reply(f"⚠️ الملف أكبر من {config.MAX_BACKUP_MB}MB.")

        m = await message.reply("🔄 جاري الاستعادة...")
        try:
            safety = await _dump()
            stamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            sfile = io.BytesIO(safety)
            sfile.name = f"pre_restore_{stamp}.json"
            await message.reply_document(sfile, caption="🛟 نسخة أمان تلقائية قبل الاستعادة")
        except Exception as e:
            LOGGER.warning(f"safety backup failed: {e}")

        try:
            path = await reply.download(in_memory=True)
            path.seek(0)
            report = await _restore(path.read())
        except Exception as e:
            LOGGER.exception("restore")
            return await m.edit(f"⚠️ فشل الاستعادة (البيانات الأصلية سليمة): {e}")

        summary = "\n".join(f"• {k}: {v}" for k, v in report.items())
        await m.edit(f"✅ تمت الاستعادة بنجاح:\n\n{summary}")
