from database import db
import time

wars_col = db["wars"]
war_history_col = db["war_history"]


async def create_war(challenger_id, challenger_name, target_id, target_name, amount, group_id, message_id):
    war = {
        "challenger_id": challenger_id,
        "challenger_name": challenger_name,
        "target_id": target_id,
        "target_name": target_name,
        "amount": amount,
        "group_id": group_id,
        "message_id": message_id,
        "status": "pending",           # pending, weapon_select, coin_flip, done
        "challenger_weapon": None,
        "target_weapon": None,
        "created_at": time.time()
    }
    result = await wars_col.insert_one(war)
    return str(result.inserted_id)


async def get_war(war_id: str):
    from bson import ObjectId
    return await wars_col.find_one({"_id": ObjectId(war_id)})


async def get_active_war_by_user(user_id: int, group_id: int):
    return await wars_col.find_one({
        "group_id": group_id,
        "status": {"$in": ["pending", "weapon_select", "coin_flip"]},
        "$or": [{"challenger_id": user_id}, {"target_id": user_id}]
    })


async def update_war(war_id: str, update: dict):
    from bson import ObjectId
    await wars_col.update_one({"_id": ObjectId(war_id)}, {"$set": update})


async def delete_war(war_id: str):
    from bson import ObjectId
    await wars_col.delete_one({"_id": ObjectId(war_id)})


async def save_war_history(data: dict):
    await war_history_col.insert_one(data)


async def get_war_stats(user_id: int, group_id: int):
    wars = await war_history_col.find({
        "group_id": group_id,
        "$or": [{"winner_id": user_id}, {"loser_id": user_id}]
    }).to_list(length=None)

    wins = sum(1 for w in wars if w["winner_id"] == user_id)
    losses = sum(1 for w in wars if w["loser_id"] == user_id)
    total_earned = sum(w.get("winner_amount", 0) for w in wars if w["winner_id"] == user_id)
    total_lost = sum(w.get("amount", 0) * 2 for w in wars if w["loser_id"] == user_id)
    biggest_win = max((w.get("winner_amount", 0) for w in wars if w["winner_id"] == user_id), default=0)

    return {
        "wins": wins,
        "losses": losses,
        "total": wins + losses,
        "total_earned": total_earned,
        "total_lost": total_lost,
        "biggest_win": biggest_win
    }


async def cleanup_expired_wars():
    """Delete wars older than 60 seconds that are still pending."""
    expire_time = time.time() - 60
    expired = await wars_col.find({
        "status": "pending",
        "created_at": {"$lt": expire_time}
    }).to_list(length=None)
    if expired:
        from bson import ObjectId
        ids = [w["_id"] for w in expired]
        await wars_col.delete_many({"_id": {"$in": ids}})
    return expired
