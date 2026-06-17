import asyncio
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid, ChatWriteForbidden
)
from helpers.filters import cmd
from helpers.decorators import dev_only
from helpers.logger import LOGGER
from database.chats import all_chats
from database.users import all_users

BC = cmd("اذاعة", "إذاعة")
BC_CHAT = cmd("اذاعة_مجموعات")
BC_USER = cmd("اذاعة_مستخدمين")


async def _send(client, targets, text):
    ok = failed = 0
    for t in targets:
        attempt = 0
        while True:
            try:
                await client.send_message(t, text)
                ok += 1
                await asyncio.sleep(0.3)
                break
            except FloodWait as e:
                wait = int(getattr(e, "value", getattr(e, "x", 5)))
                LOGGER.warning(f"FloodWait {wait}s أثناء الإذاعة")
                await asyncio.sleep(wait + 1)
                attempt += 1
                if attempt >= 3:
                    failed += 1
                    break
            except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid, ChatWriteForbidden):
                failed += 1
                break
            except Exception as e:
                LOGGER.warning(f"broadcast skip {t}: {e}")
                failed += 1
                break
    return ok, failed


def register(app: Client, calls):

    @app.on_message(BC)
    @dev_only
    async def bc_all(client, message: Message):
        txt = message.text.split(maxsplit=1)
        if len(txt) < 2:
            return await message.reply("اكتب نص الإذاعة بعد الأمر.")
        # #12: أرسل للمجموعات والمستخدمين بشكل منفصل وبتقرير مفصّل
        c_ok, c_failed = await _send(client, await all_chats(), txt[1])
        u_ok, u_failed = await _send(client, await all_users(), txt[1])
        await message.reply(
            f"📣 **اكتملت الإذاعة**\n\n"
            f"المجموعات: ✅ {c_ok} / ❌ {c_failed}\n"
            f"المستخدمون: ✅ {u_ok} / ❌ {u_failed}"
        )

    @app.on_message(BC_CHAT)
    @dev_only
    async def bc_chats(client, message: Message):
        txt = message.text.split(maxsplit=1)
        if len(txt) < 2:
            return
        ok, failed = await _send(client, await all_chats(), txt[1])
        await message.reply(f"📣 المجموعات: ✅ {ok} / ❌ {failed}")

    @app.on_message(BC_USER)
    @dev_only
    async def bc_users(client, message: Message):
        txt = message.text.split(maxsplit=1)
        if len(txt) < 2:
            return
        ok, failed = await _send(client, await all_users(), txt[1])
        await message.reply(f"📣 المستخدمون: ✅ {ok} / ❌ {failed}")
