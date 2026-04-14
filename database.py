import motor.motor_asyncio
from config import MONGO_URI, DB_NAME

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
groups_col = db["groups"]
marriages_col = db["marriages"]


async def ensure_indexes():
    await users_col.create_index([("user_id", 1), ("group_id", 1)], unique=True)
    await groups_col.create_index("group_id", unique=True)
    await marriages_col.create_index("user1_id", unique=True)
