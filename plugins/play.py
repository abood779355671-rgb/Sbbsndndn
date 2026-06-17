from pyrogram import Client
from pyrogram.types import Message
from helpers import filters as F
from helpers.decorators import guard, safe
from helpers.anti_spam import is_spam
from helpers.youtube import search
from helpers.call import VoiceChatClosed
from helpers.logger import LOGGER
from database.chats import add_chat
from database.users import add_user


def register(app: Client, calls):

    @app.on_message(F.PLAY)
    @safe
    @guard
    async def play_handler(client, message: Message):
        uid = message.from_user.id
        if await is_spam(uid):
            return await message.reply("⏳ أبطئ قليلاً، طلبات كثيرة.")
        await add_chat(message.chat.id, message.chat.title or "")
        await add_user(uid, message.from_user.first_name or "")

        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            return await message.reply("✳️ اكتب: تشغيل اسم الأغنية أو الرابط")
        query = parts[1]

        m = await message.reply("🔎 جاري البحث...")
        track = await search(query)
        if not track:
            return await m.edit("❌ لم يتم العثور على نتائج.")
        track["requester"] = message.from_user.first_name

        try:
            order = await calls.play_or_queue(message.chat.id, track)
        except VoiceChatClosed:
            return await m.edit(
                "❌ لا يمكن التشغيل.\n\n"
                "المكالمة الصوتية مقفلة أو غير مفتوحة.\n"
                "افتح المكالمة الصوتية في المجموعة ثم أعد المحاولة."
            )
        except Exception as e:
            LOGGER.exception("play error")
            return await m.edit(f"⚠️ خطأ أثناء التشغيل: {e}")

        if order == -1:
            return await m.edit("⚠️ هذه الأغنية موجودة بالفعل في قائمة الانتظار.")

        if order == 0:
            caption = (
                f"🎵 **تم بدء التشغيل**\n\n"
                f"الاغنية: {track['title']}\n"
                f"المدة: {track['duration']}\n"
                f"بواسطة: {track['requester']}"
            )
        else:
            caption = (
                f"📥 **تمت إضافة الأغنية إلى قائمة الانتظار**\n\n"
                f"الاغنية: {track['title']}\n"
                f"الترتيب: #{order}"
            )

        await m.delete()
        if track.get("thumb"):
            try:
                return await message.reply_photo(track["thumb"], caption=caption)
            except Exception:
                pass
        await message.reply(caption)
