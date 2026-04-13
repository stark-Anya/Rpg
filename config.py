import os
from dotenv import load_dotenv

load_dotenv()

# ─── Bot Config ───────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "5864182070"))

# ─── Links ────────────────────────────────────────────────────
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/CarelessxWorld")
UPDATE_LINK = os.getenv("UPDATE_LINK", "https://t.me/CarelessxCoder")
OWNER_LINK = os.getenv("OWNER_LINK", "https://t.me/CarelessxOwner")
GUIDE_PDF_LINK = os.getenv("GUIDE_PDF_LINK", "https://t.me/StarkFiles_Bot?start=BQADAQAD3BAAAsxe6EYP8Cy0nuHBYE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "StarkxGame_Bot")

# ─── MongoDB ──────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "rpg_bot"

# ─── Economy ──────────────────────────────────────────────────
STARTING_BALANCE = 200
DAILY_REWARD = 200
DAILY_COOLDOWN = 86400
CLAIM_MIN = 100
CLAIM_MAX = 500
CLAIM_COOLDOWN = 86400
MINE_MIN = 1
MINE_MAX = 100
MINE_COOLDOWN = 3600
FARM_MIN = 1
FARM_MAX = 100
FARM_COOLDOWN = 3600
GIVE_TAX = 0.10
CRIME_SUCCESS_CHANCE = 0.60
CRIME_MIN_REWARD = 50
CRIME_MAX_REWARD = 300
CRIME_MIN_PENALTY = 30
CRIME_MAX_PENALTY = 200

# ─── RPG ──────────────────────────────────────────────────────
KILL_LOOT_PERCENT = 0.75
PROTECT_COST = 100
PROTECT_MIN_BALANCE = 700
PROTECT_DURATION = 86400
REVIVE_COST = 0
HEAL_COST = 100
HEAL_AMOUNT = 50
WEAPON_REPAIR_COST = 50
DEFAULT_HP = 100
MAX_HP = 200
WANTED_KILLS_THRESHOLD = 10
WANTED_BOUNTY = 500

# ─── War ──────────────────────────────────────────────────────
WAR_TIMEOUT = 60
WAR_WINNER_PERCENT = 0.90
WAR_PROTECTION_DAMAGE_REDUCE = 0.40

# ─── War Streak Bonuses ───────────────────────────────────────
STREAK_3_BONUS = 0.10
STREAK_5_BONUS = 0.20

# ─── Bank ─────────────────────────────────────────────────────
BANK_INTEREST_RATE = 0.10
LOAN_MAX = 1000
LOAN_INTEREST_RATE = 0.05

# ─── Marriage ─────────────────────────────────────────────────
PROPOSE_TAX = 0.05
DIVORCE_COST = 2000

# ─── Images (catbox/direct links) ────────────────────────────
IMG_KILL     = os.getenv("IMG_KILL",     "https://n.uguu.se/WSHMjyin.jpg")
IMG_ROB      = os.getenv("IMG_ROB",      "")
IMG_WAR_WIN  = os.getenv("IMG_WAR_WIN",  "")
IMG_WAR_DRAW = os.getenv("IMG_WAR_DRAW", "")
IMG_PROPOSE  = os.getenv("IMG_PROPOSE",  "https://o.uguu.se/tKXeGsNj.jpg")
IMG_MARRY    = os.getenv("IMG_MARRY",    "https://n.uguu.se/eiouEWkD.jpg")
IMG_DIVORCE  = os.getenv("IMG_DIVORCE",  "https://h.uguu.se/wohggaDk.jpg")
IMG_DAILY    = os.getenv("IMG_DAILY",    "")
IMG_CRIME    = os.getenv("IMG_CRIME",    "")
IMG_MINE     = os.getenv("IMG_MINE",     "")
IMG_FARM     = os.getenv("IMG_FARM",     "")
IMG_PROTECT  = os.getenv("IMG_PROTECT",  "")
IMG_REVIVE   = os.getenv("IMG_REVIVE",   "")
IMG_WANTED   = os.getenv("IMG_WANTED",   "")
IMG_WELCOME  = os.getenv("IMG_WELCOME",  "https://files.catbox.moe/3rdf9a.jpg")

# ─── Shop Items ───────────────────────────────────────────────
SHOP_ITEMS = {
    "wooden_sword": {
        "name": "🗡️ Wooden Sword", "price": 100, "damage": 10,
        "defense": 0, "hp_bonus": 0, "type": "weapon",
        "description": "Basic weapon for beginners"
    },
    "iron_sword": {
        "name": "⚔️ Iron Sword", "price": 300, "damage": 25,
        "defense": 0, "hp_bonus": 0, "type": "weapon",
        "description": "A sharp iron blade"
    },
    "steel_sword": {
        "name": "🔱 Steel Sword", "price": 600, "damage": 45,
        "defense": 0, "hp_bonus": 0, "type": "weapon",
        "description": "High-grade steel sword"
    },
    "legendary_blade": {
        "name": "✨ Legendary Blade", "price": 1500, "damage": 90,
        "defense": 0, "hp_bonus": 0, "type": "weapon",
        "description": "Forged in dragon fire"
    },
    "leather_armor": {
        "name": "🛡️ Leather Armor", "price": 150, "damage": 0,
        "defense": 10, "hp_bonus": 20, "type": "armor",
        "description": "Basic protection"
    },
    "iron_armor": {
        "name": "🔰 Iron Armor", "price": 400, "damage": 0,
        "defense": 25, "hp_bonus": 40, "type": "armor",
        "description": "Solid iron protection"
    },
    "dragon_armor": {
        "name": "🐉 Dragon Armor", "price": 1200, "damage": 0,
        "defense": 60, "hp_bonus": 100, "type": "armor",
        "description": "Made from dragon scales"
    },
    "health_potion": {
        "name": "🧪 Health Potion", "price": 80, "damage": 0,
        "defense": 0, "hp_bonus": 50, "type": "potion",
        "description": "Restores 50 HP instantly"
    },
    "mega_potion": {
        "name": "💊 Mega Potion", "price": 200, "damage": 0,
        "defense": 0, "hp_bonus": 120, "type": "potion",
        "description": "Restores 120 HP instantly"
    },
}
