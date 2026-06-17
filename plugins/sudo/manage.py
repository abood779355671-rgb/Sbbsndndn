from pyrogram import Client
from pyrogram.types import Message
from helpers.filters import cmd
from helpers.decorators import dev_only
from database import devs as D
from database import banned as B
from database.chats import set_enabled

ADD_DEV = cmd("اضافة_مطور")
DEL_DEV = cmd("حذف_مطور")
ADD_SUDO = cmd("اضافة_ادمن")
DEL_SUDO = cmd("حذف_ادمن")
LIST_DEVS = cmd("المطورين")
BAN_USER = cmd("حظر")
UNBAN_USER = cmd("فك_حظر")
BAN_CHAT = cmd("حظر_مجموعة")
UNBAN_CHAT = cmd("فك_حظر_مجموعة")
BANNED_LST = cmd("المحظورين")
ENABLE = cmd("تفعيل")
DISABLE = cmd("تعطيل")


def _target_id(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    parts = message.text.split()
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            return None
    return None


def register(app: Client, calls):

    @app.on_message(ADD_DEV)
    @dev_only
    async def add_dev_h(client, message: Message):
        tid = _target_id(message)
        if not tid:
            return await message.reply("✳️ رد على المستخدم أو: اضافة_مطور <ID>")
        await D.add_dev(tid)
        await message.reply(f"✅ تمت إضافة المطور: `{tid}`")

    @app.on_message(DEL_DEV)
    @dev_only
    async def del_dev_h(client, message: Message):
        tid = _target_id(message)
        if not tid:
            return await message.reply("✳️ رد على المستخدم أو: حذف_مطور <ID>")
        await D.remove_entry(tid)
        await message.reply(f"🗑 تم حذف المطور: `{tid}`")

    @app.on_message(ADD_SUDO)
    @dev_only
    async def add_sudo_h(client, message: Message):
        tid = _target_id(message)
        if not tid:
            return await message.reply("✳️ رد على المستخدم أو: اضافة_ادمن <ID>")
        await D.add_sudo(tid)
        await message.reply(f"✅ تمت إضافة أدمن عالمي: `{tid}`")

    @app.on_message(DEL_SUDO)
    @dev_only
    async def del_sudo_h(client, message: Message):
        tid = _target_id(message)
        if not tid:
            return await message.reply("✳️ رد على المستخدم أو: حذف_ادمن <ID>")
        await D.remove_entry(tid)
        await message.reply(f"🗑 تم حذف الأدمن العالمي: `{tid}`")

    @app.on_message(LIST_DEVS)
    @dev_only
    async def list_devs_h(client, message: Message):
        devs = await D.list_devs()
        if not devs:
            return await message.reply("لا يوجد مطورون/أدمنية مضافون.")
        text = "👮 **المطورون والأدمنية العالميون**\n\n"
        for d in devs:
            text += f"• `{d['user_id']}` — {d.get('role', 'dev')}\n"
        await message.reply(text)

    @app.on_message(BAN_USER)
    @dev_only
    async def ban_user_h(client, message: Message):
        tid = _target_id(message)
        if not tid:
            return await message.reply("✳️ رد على المستخدم أو: حظر <ID>")
        await B.ban(tid, "user")
        await message.reply(f"🚫 تم حظر المستخدم: `{tid}`")

    @app.on_message(UNBAN_USER)
    @dev_only
    async def unban_user_h(client, message: Message):
        tid = _target_id(message)
        if not tid:
            return await message.reply("✳️ رد على المستخدم أو: فك_حظر <ID>")
        await B.unban(tid)
        await message.reply(f"✅ تم فك حظر المستخدم: `{tid}`")

    @app.on_message(BAN_CHAT)
    @dev_only
    async def ban_chat_h(client, message: Message):
        parts = message.text.split()
        tid = int(parts[1]) if len(parts) >= 2 and parts[1].lstrip("-").isdigit() else message.chat.id
        await B.ban(tid, "chat")
        await message.reply(f"🚫 تم حظر المجموعة: `{tid}`")

    @app.on_message(UNBAN_CHAT)
    @dev_only
    async def unban_chat_h(client, message: Message):
        parts = message.text.split()
        tid = int(parts[1]) if len(parts) >= 2 and parts[1].lstrip("-").isdigit() else message.chat.id
        await B.unban(tid)
        await message.reply(f"✅ تم فك حظر المجموعة: `{tid}`")

    @app.on_message(BANNED_LST)
    @dev_only
    async def banned_list_h(client, message: Message):
        items = await B.banned_list()
        if not items:
            return await message.reply("لا يوجد محظورون.")
        users = [b for b in items if b.get("kind") == "user"]
        chats = [b for b in items if b.get("kind") == "chat"]
        text = "🚫 **قائمة المحظورين**\n\n"
        if users:
            text += "👤 المستخدمون:\n" + "\n".join(f"• `{b['target_id']}`" for b in users) + "\n\n"
        if chats:
            text += "👥 المجموعات:\n" + "\n".join(f"• `{b['target_id']}`" for b in chats)
        await message.reply(text)

    @app.on_message(ENABLE)
    @dev_only
    async def enable_h(client, message: Message):
        await set_enabled(message.chat.id, True)
        await message.reply("✅ تم تفعيل البوت في هذه المجموعة.")

    @app.on_message(DISABLE)
    @dev_only
    async def disable_h(client, message: Message):
        await set_enabled(message.chat.id, False)
        await message.reply("⛔ تم تعطيل البوت في هذه المجموعة.")
