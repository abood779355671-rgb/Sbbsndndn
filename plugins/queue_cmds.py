from pyrogram import Client
from pyrogram.types import Message
from helpers import filters as F
from helpers.decorators import admin_only, guard, safe
from database import queue as q


def register(app: Client, calls):

    @app.on_message(F.QUEUE)
    @safe
    @guard
    async def queue_h(client, message: Message):
        items = await q.load_queue(message.chat.id)
        if not items:
            return await message.reply("📭 قائمة الانتظار فارغة.")
        text = "🎶 **قائمة التشغيل**\n\n"
        for i, t in enumerate(items):
            tag = "▶️ الآن" if i == 0 else f"#{i}"
            text += f"{tag} — {t['title']} ({t['duration']})\n"
        await message.reply(text)

    @app.on_message(F.CLEAN)
    @safe
    @guard
    @admin_only
    async def clean_h(client, message: Message):
        await q.clear_queue(message.chat.id)
        await message.reply("🧹 تم تنظيف قائمة الانتظار.")
