from database.mongo import devs_col
from config import config


async def add_dev(user_id: int):
    await devs_col.update_one({"user_id": user_id}, {"$set": {"role": "dev"}}, upsert=True)


async def add_sudo(user_id: int):
    await devs_col.update_one({"user_id": user_id}, {"$set": {"role": "sudo"}}, upsert=True)


async def remove_entry(user_id: int):
    await devs_col.delete_one({"user_id": user_id})


async def is_dev(user_id: int):
    if user_id == config.OWNER_ID:
        return True
    return bool(await devs_col.find_one({"user_id": user_id}))


async def list_devs():
    return [d async for d in devs_col.find({})]
