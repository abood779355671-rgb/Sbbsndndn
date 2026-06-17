from pyrogram import Client
from pyrogram.types import Message
from helpers import filters as F
from helpers.decorators import admin_only, guard, safe
from helpers.admin_cache import fetch_admins
from database.admins import invalidate_admins


def register(app: Client, calls):

    @app.on_message(F.REPORT)
    @safe
    @guard
    @admin_only
    async def report_h(client, message: Message):
        await invalidate_admins(message.chat.id)
        ids = await fetch_admins(client, message.chat.id)
        await message.reply(
            f"♻️ تم تحديث ومزامنة قائمة المشرفين.\nعدد المشرفين: {len(ids)}"
        )
