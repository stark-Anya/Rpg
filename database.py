#===================================================#
#=============== OWNER : MISTER STARK ==============#
#===================================================#
#============== USERS & BOT DATABASE  ==========={==#
#===================================================#

import motor.motor_asyncio
from config import MONGO_URI, DB_NAME

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# ── Collections ────────────────────────────────────────────────
users_col      = db["users"]        # Global — keyed by user_id only
groups_col     = db["groups"]       # Per-group settings
memberships_col = db["memberships"] # Tracks which users are in which groups (for leaderboards)


async def ensure_indexes():
    # Users — unique per user globally
    await users_col.create_index("user_id", unique=True)

    # Groups
    await groups_col.create_index("group_id", unique=True)

    # Memberships — user_id + group_id combo
    await memberships_col.create_index(
        [("user_id", 1), ("group_id", 1)], unique=True
    )


#===================================================#
#=============== OWNER : MISTER STARK ==============#
#===================================================#
#============== CREDIT NA LENA BACHHO 🤣 ===========#
#===================================================#
