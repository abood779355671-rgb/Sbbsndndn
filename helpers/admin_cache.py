from pyrogram import Client
from pyrogram.enums import ChatMembersFilter
from database.admins import get_admins, save_admins


async def fetch_admins(client: Client, chat_id: int) -> list:
    ids = []
    async for m in client.get_chat_members(
        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
    ):
        if m.user and not m.user.is_bot:
            ids.append(m.user.id)
    await save_admins(chat_id, ids)
    return ids


async def is_user_admin(client: Client, chat_id: int, user_id: int) -> bool:
    cached = await get_admins(chat_id)
    if cached is None:
        cached = await fetch_admins(client, chat_id)
    return user_id in cached
