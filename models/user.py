from database import users_col
from config import STARTING_BALANCE, DEFAULT_HP
import time


def default_user(user_id: int, group_id: int, username: str = "Unknown") -> dict:
    return {
        "user_id": user_id,
        "group_id": group_id,
        "username": username,
        "balance": STARTING_BALANCE,
        "bank_balance": 0,
        "loan": 0,
        "loan_taken_at": None,
        "bank_deposited_at": None,
        "hp": DEFAULT_HP,
        "max_hp": DEFAULT_HP,
        "status": "alive",           # alive / dead
        "kills": 0,
        "deaths": 0,
        "inventory": {},             # item_key: quantity
        "equipped_weapon": None,
        "equipped_armor": None,
        "protected_until": None,
        "last_daily": None,
        "last_claim": None,
        "last_mine": None,
        "last_farm": None,
        "last_crime": None,
        "married_to": None,
        "created_at": time.time(),
    }


async def get_user(user_id: int, group_id: int, username: str = "Unknown") -> dict:
    user = await users_col.find_one({"user_id": user_id, "group_id": group_id})
    if not user:
        user = default_user(user_id, group_id, username)
        await users_col.insert_one(user)
    return user


async def update_user(user_id: int, group_id: int, update: dict):
    await users_col.update_one(
        {"user_id": user_id, "group_id": group_id},
        {"$set": update}
    )


async def get_top_rich(group_id: int, limit: int = 10):
    cursor = users_col.find({"group_id": group_id}).sort("balance", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_top_killers(group_id: int, limit: int = 10):
    cursor = users_col.find({"group_id": group_id}).sort("kills", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_all_users(group_id: int):
    cursor = users_col.find({"group_id": group_id})
    return await cursor.to_list(length=None)
