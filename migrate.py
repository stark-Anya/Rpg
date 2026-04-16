"""
migrate.py — Run ONCE to migrate old per-group user data to global user docs.

Old schema: users collection had {user_id, group_id, balance, ...} per group
New schema: users collection has {user_id, balance, ...} globally (one doc per user)

Run: python migrate.py
"""

import asyncio
import motor.motor_asyncio
from config import MONGO_URI, DB_NAME

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db     = client[DB_NAME]

old_col  = db["users"]
new_col  = db["users_global"]
memb_col = db["memberships"]


async def migrate():
    print("🔄 Starting migration...")

    all_docs = await old_col.find({}).to_list(None)
    print(f"📦 Found {len(all_docs)} old user-group records")

    # Group docs by user_id
    by_user: dict = {}
    for doc in all_docs:
        uid = doc["user_id"]
        gid = doc.get("group_id", 0)
        if uid not in by_user:
            by_user[uid] = {"docs": [], "best": None}
        by_user[uid]["docs"].append(doc)
        # Track memberships
        if gid and gid != 0:
            await memb_col.update_one(
                {"user_id": uid, "group_id": gid},
                {"$set": {"user_id": uid, "group_id": gid, "username": doc.get("username", "Unknown")}},
                upsert=True
            )

    print(f"👥 Unique users: {len(by_user)}")

    merged = 0
    for uid, data in by_user.items():
        docs = data["docs"]

        # Merge strategy: take max balance, max kills, max bank, union inventory
        best = max(docs, key=lambda d: d.get("balance", 0) + d.get("bank_balance", 0))

        merged_inventory = {}
        for doc in docs:
            for k, v in doc.get("inventory", {}).items():
                if k not in merged_inventory:
                    merged_inventory[k] = v
                else:
                    # Take higher qty
                    if v.get("qty", 0) > merged_inventory[k].get("qty", 0):
                        merged_inventory[k] = v

        global_doc = {
            "user_id":          uid,
            "username":         best.get("username", "Unknown"),
            "balance":          max(d.get("balance", 0) for d in docs),
            "bank_balance":     max(d.get("bank_balance", 0) for d in docs),
            "loan":             best.get("loan", 0),
            "loan_taken_at":    best.get("loan_taken_at"),
            "bank_deposited_at": best.get("bank_deposited_at"),
            "hp":               best.get("hp", 100),
            "status":           best.get("status", "alive"),
            "kills":            max(d.get("kills", 0) for d in docs),
            "deaths":           max(d.get("deaths", 0) for d in docs),
            "inventory":        merged_inventory,
            "protected_until":  best.get("protected_until"),
            "last_daily":       best.get("last_daily"),
            "last_claim":       best.get("last_claim"),
            "last_mine":        best.get("last_mine"),
            "last_farm":        best.get("last_farm"),
            "last_crime":       best.get("last_crime"),
            "married_to":       best.get("married_to"),
            "war_streak":       max(d.get("war_streak", 0) for d in docs),
            "created_at":       min(d.get("created_at", 0) for d in docs),
        }

        await new_col.update_one(
            {"user_id": uid},
            {"$set": global_doc},
            upsert=True
        )
        merged += 1

    print(f"✅ Migrated {merged} users to global docs in 'users_global'")
    print()
    print("⚠️  Next steps:")
    print("   1. Verify 'users_global' collection looks correct in MongoDB Compass")
    print("   2. Rename 'users' → 'users_old' for backup")
    print("   3. Rename 'users_global' → 'users'")
    print("   4. Restart the bot")
    print()
    print("   MongoDB shell commands:")
    print("   db.users.renameCollection('users_old')")
    print("   db.users_global.renameCollection('users')")


if __name__ == "__main__":
    asyncio.run(migrate())
