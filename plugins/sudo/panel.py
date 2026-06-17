from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from helpers.filters import cmd
from helpers.decorators import dev_only
from database.chats import count_chats
from database.users import count_users
from database.devs import is_dev
from database.mongo import stats_col

PANEL = cmd("لوحة")

SHUTDOWN = {"flag": False}


def _kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="p_stats")],
        [InlineKeyboardButton("👮 المطورون", callback_data="p_devs"),
         InlineKeyboardButton("🚫 المحظورون", callback_data="p_banned")],
        [InlineKeyboardButton("🔄 إعادة تشغيل", callback_data="p_restart")],
    ])


def register(app: Client, calls):

    @app.on_message(PANEL)
    @dev_only
    async def panel_h(client, message: Message):
        await message.reply("🛠 **لوحة المطور**", reply_markup=_kb())

    @app.on_callback_query(filters.regex("^p_"))
    async def cb(client, query: CallbackQuery):
        if not await is_dev(query.from_user.id):
            return await query.answer("للمطور فقط", show_alert=True)
        data = query.data
        if data == "p_stats":
            doc = await stats_col.find_one({"_id": "global"}) or {}
            await query.message.edit_text(
                f"📊 **الإحصائيات**\n\n"
                f"المجموعات: {await count_chats()}\n"
                f"المستخدمون: {await count_users()}\n"
                f"الأغاني المشغّلة: {doc.get('played', 0)}",
                reply_markup=_kb(),
            )
        elif data == "p_restart":
            await query.answer("جاري إعادة التشغيل بأمان...")
            SHUTDOWN["flag"] = True
        else:
            await query.answer("استخدم الأوامر النصية لهذه الميزة.", show_alert=True)
