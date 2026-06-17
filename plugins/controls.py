from pyrogram import Client
from pyrogram.types import Message
from helpers import filters as F
from helpers.decorators import admin_only, guard, safe


def register(app: Client, calls):

    # #8: الترتيب الصحيح — safe خارجي (الأقرب لـ on_message) ليلتقط أخطاء guard/admin_only
    @app.on_message(F.SKIP)
    @safe
    @guard
    @admin_only
    async def skip_h(client, message: Message):
        nxt = await calls.skip(message.chat.id)
        if nxt:
            await message.reply(f"⏭ تم تخطي الأغنية الحالية\n\nالآن يعمل:\n{nxt['title']}")
        else:
            await message.reply("⏭ تم التخطي. لا توجد أغانٍ أخرى. تم الإيقاف.")

    @app.on_message(F.STOP)
    @safe
    @guard
    @admin_only
    async def stop_h(client, message: Message):
        await calls.stop(message.chat.id)
        await message.reply("⏹ تم ايقاف التشغيل ومغادرة المكالمة الصوتية")

    @app.on_message(F.RESUME)
    @safe
    @guard
    @admin_only
    async def resume_h(client, message: Message):
        await calls.resume(message.chat.id)
        await message.reply("▶️ تم استئناف التشغيل")

    @app.on_message(F.MUTE)
    @safe
    @guard
    @admin_only
    async def mute_h(client, message: Message):
        await calls.mute(message.chat.id)
        await message.reply("🔇 تم الكتم")

    @app.on_message(F.UNMUTE)
    @safe
    @guard
    @admin_only
    async def unmute_h(client, message: Message):
        await calls.unmute(message.chat.id)
        await message.reply("🔊 تم إلغاء الكتم")
