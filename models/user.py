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
        "status": "alive",
        "kills": 0,
        "deaths": 0,
        "inventory": {},
        "equipped_weapon": None,
        "equipped_armor": None,
        "protected_until": None,
        "last_daily": None,
        "last_claim": None,
        "last_mine": None,
        "last_farm": None,
        "last_crime": None,
        "married_to": None,
        "war_streak": 0,
        "created_at": time.time(),
    }


async def get_user(user_id: int, group_id: int = 0, username: str = "Unknown") -> dict:
    """Get user — works for both group and private (group_id=0 for global lookup)."""
    user = await users_col.find_one({"user_id": user_id, "group_id": group_id})
    if not user:
        # Try to find in any group
        user = await users_col.find_one({"user_id": user_id})
        if user and group_id != 0 and user["group_id"] != group_id:
            # Create new record for this group with same balance
            new_user = default_user(user_id, group_id, username)
            new_user["balance"] = user["balance"]
            new_user["bank_balance"] = user["bank_balance"]
            new_user["loan"] = user["loan"]
            await users_col.insert_one(new_user)
            return new_user
        if not user:
            user = default_user(user_id, group_id, username)
            await users_col.insert_one(user)
    return user


async def get_user_global(user_id: int, username: str = "Unknown") -> dict:
    """Get user record regardless of group — for balance sync."""
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        user = default_user(user_id, 0, username)
        await users_col.insert_one(user)
    return user


async def update_user(user_id: int, group_id: int, update: dict):
    """Update user in specific group AND sync balance fields globally."""
    await users_col.update_one(
        {"user_id": user_id, "group_id": group_id},
        {"$set": update}
    )
    # Sync balance-related fields across all records of this user
    sync_fields = {}
    for field in ["balance", "bank_balance", "loan", "loan_taken_at", "bank_deposited_at"]:
        if field in update:
            sync_fields[field] = update[field]
    if sync_fields:
        await users_col.update_many(
            {"user_id": user_id},
            {"$set": sync_fields}
        )


async def update_user_global(user_id: int, update: dict):
    """Update all records of a user (for transfer etc)."""
    await users_col.update_many({"user_id": user_id}, {"$set": update})


async def get_top_rich(group_id: int, limit: int = 10):
    cursor = users_col.find({"group_id": group_id}).sort("balance", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_top_killers(group_id: int, limit: int = 10):
    cursor = users_col.find({"group_id": group_id}).sort("kills", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_all_users(group_id: int):
    cursor = users_col.find({"group_id": group_id})
    return await cursor.to_list(length=None)
