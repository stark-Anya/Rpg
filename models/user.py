from database import users_col
from config import STARTING_BALANCE, DEFAULT_HP
import time

DEFAULT_HP = 100

def default_user(user_id, group_id, username="Unknown"):
    return {
        "user_id": user_id, "group_id": group_id, "username": username,
        "balance": STARTING_BALANCE, "bank_balance": 0,
        "loan": 0, "loan_taken_at": None, "bank_deposited_at": None,
        "status": "alive", "kills": 0, "deaths": 0,
        # inventory: {"stick": {"qty":1, "expires_at": 123456}, "cookie": {"qty":1, "expires_at": None}}
        "inventory": {},
        "protected_until": None,
        "last_daily": None, "last_claim": None,
        "last_mine": None, "last_farm": None, "last_crime": None,
        "married_to": None, "war_streak": 0, "created_at": time.time(),
    }


async def get_user(user_id: int, group_id: int = 0, username: str = "Unknown") -> dict:
    user = await users_col.find_one({"user_id": user_id, "group_id": group_id})
    if not user:
        user = default_user(user_id, group_id, username)
        await users_col.insert_one(user)
    return user


async def update_user(user_id: int, group_id: int, update: dict):
    await users_col.update_one({"user_id": user_id, "group_id": group_id}, {"$set": update})
    # Sync balance across all group records
    sync = {k: update[k] for k in ["balance","bank_balance","loan","inventory","married_to","war_streak"] if k in update}
    if sync:
        await users_col.update_many({"user_id": user_id}, {"$set": sync})


async def update_user_global(user_id: int, update: dict):
    await users_col.update_many({"user_id": user_id}, {"$set": update})


async def get_top_rich(group_id, limit=10):
    return await users_col.find({"group_id": group_id}).sort("balance", -1).limit(limit).to_list(limit)


async def get_top_killers(group_id, limit=10):
    return await users_col.find({"group_id": group_id}).sort("kills", -1).limit(limit).to_list(limit)


async def get_all_users(group_id):
    return await users_col.find({"group_id": group_id}).to_list(None)
