from database.mongo import users_col


async def add_user(user_id: int, name: str = ""):
    await users_col.update_one(
        {"user_id": user_id}, {"$set": {"name": name}}, upsert=True
    )


async def all_users():
    return [u["user_id"] async for u in users_col.find({})]


async def count_users():
    return await users_col.count_documents({})
