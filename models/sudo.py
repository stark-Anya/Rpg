from database import db

sudo_col = db["sudoers"]


async def add_sudo(user_id: int, username: str = "Unknown") -> bool:
    existing = await sudo_col.find_one({"user_id": user_id})
    if existing:
        return False
    await sudo_col.insert_one({"user_id": user_id, "username": username})
    return True


async def remove_sudo(user_id: int) -> bool:
    result = await sudo_col.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def is_sudo(user_id: int) -> bool:
    doc = await sudo_col.find_one({"user_id": user_id})
    return doc is not None


async def get_all_sudos() -> list:
    return await sudo_col.find({}).to_list(None)
