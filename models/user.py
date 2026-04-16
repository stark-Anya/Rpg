from database import users_col, memberships_col
from config import STARTING_BALANCE, DEFAULT_HP
import time


def default_user(user_id: int, username: str = "Unknown") -> dict:
    return {
        "user_id":          user_id,
        "username":         username,
        "balance":          STARTING_BALANCE,
        "bank_balance":     0,
        "loan":             0,
        "loan_taken_at":    None,
        "bank_deposited_at": None,
        "hp":               DEFAULT_HP,
        "status":           "alive",
        "kills":            0,
        "deaths":           0,
        "inventory":        {},
        "protected_until":  None,
        "last_daily":       None,
        "last_claim":       None,
        "last_mine":        None,
        "last_farm":        None,
        "last_crime":       None,
        "married_to":       None,
        "war_streak":       0,
        "created_at":       time.time(),
    }


async def get_user(user_id: int, group_id: int = 0, username: str = "Unknown") -> dict:
    """
    Fetch global user record.
    group_id is accepted for backward compat but NOT used as a key.
    Also registers the user as a member of that group (for leaderboards).
    """
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        user = default_user(user_id, username)
        await users_col.insert_one(user)
    elif username and username != "Unknown" and user.get("username") != username:
        # Keep username fresh
        await users_col.update_one(
            {"user_id": user_id},
            {"$set": {"username": username}}
        )
        user["username"] = username

    # Track group membership for leaderboard queries
    if group_id and group_id != 0:
        await memberships_col.update_one(
            {"user_id": user_id, "group_id": group_id},
            {"$set": {"user_id": user_id, "group_id": group_id, "username": user.get("username", username)}},
            upsert=True
        )

    return user


async def update_user(user_id: int, group_id: int = 0, updates: dict = None) -> None:
    """
    Update global user record. group_id ignored — all updates are global.
    """
    if not updates:
        return
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": updates}
    )

    # Keep membership username in sync if username updated
    if "username" in updates and group_id:
        await memberships_col.update_many(
            {"user_id": user_id},
            {"$set": {"username": updates["username"]}}
        )


async def update_user_global(user_id: int, updates: dict) -> None:
    """Alias — same as update_user, kept for compatibility."""
    await update_user(user_id, 0, updates)


async def get_top_rich(group_id: int, limit: int = 10) -> list:
    """Top richest users who have interacted in this group."""
    member_ids = await _get_group_member_ids(group_id)
    return await users_col.find(
        {"user_id": {"$in": member_ids}}
    ).sort("balance", -1).limit(limit).to_list(limit)


async def get_top_killers(group_id: int, limit: int = 10) -> list:
    """Top killers among users in this group."""
    member_ids = await _get_group_member_ids(group_id)
    return await users_col.find(
        {"user_id": {"$in": member_ids}}
    ).sort("kills", -1).limit(limit).to_list(limit)


async def get_all_users(group_id: int) -> list:
    """All users who have interacted in this group."""
    member_ids = await _get_group_member_ids(group_id)
    return await users_col.find({"user_id": {"$in": member_ids}}).to_list(None)


async def _get_group_member_ids(group_id: int) -> list:
    """Return list of user_ids who have been seen in this group."""
    docs = await memberships_col.find(
        {"group_id": group_id}, {"user_id": 1}
    ).to_list(None)
    return [d["user_id"] for d in docs]
