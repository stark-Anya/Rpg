import os
from dotenv import load_dotenv

load_dotenv()

# Bot Config
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

# Links — add your own in .env
WELCOME_IMAGE = os.getenv("WELCOME_IMAGE", "https://your-image-link-here.jpg")
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/your_support_group")
UPDATE_LINK = os.getenv("UPDATE_LINK", "https://t.me/your_updates_channel")
OWNER_LINK = os.getenv("OWNER_LINK", "https://t.me/your_username")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "rpg_bot"

# Economy
STARTING_BALANCE = 200
DAILY_REWARD = 200
DAILY_COOLDOWN = 86400          # 24 hours in seconds
CLAIM_MIN = 100
CLAIM_MAX = 500
CLAIM_COOLDOWN = 86400

MINE_MIN = 1
MINE_MAX = 100
MINE_COOLDOWN = 3600            # 1 hour

FARM_MIN = 1
FARM_MAX = 100
FARM_COOLDOWN = 3600

GIVE_TAX = 0.10                 # 10%

# Crime
CRIME_SUCCESS_CHANCE = 0.60     # 60% success
CRIME_MIN_REWARD = 50
CRIME_MAX_REWARD = 300
CRIME_MIN_PENALTY = 30
CRIME_MAX_PENALTY = 200

# RPG
KILL_LOOT_PERCENT = 0.75        # 75%
ROB_LOOT_PERCENT = 1.00         # 100% of specified amount
PROTECT_COST = 100
PROTECT_MIN_BALANCE = 700
PROTECT_DURATION = 86400        # 24 hours
REVIVE_COST = 0                 # Free

HEAL_COST = 100                 # Self heal
WEAPON_REPAIR_COST = 50

# Bank
BANK_INTEREST_RATE = 0.10       # 10% daily
LOAN_MAX = 1000
LOAN_INTEREST_RATE = 0.05       # 5% daily

# Marriage
PROPOSE_TAX = 0.05              # 5%
DIVORCE_COST = 2000

# Shop Items: name, price, damage, defense, hp_bonus
SHOP_ITEMS = {
    "wooden_sword": {
        "name": "🗡️ Wooden Sword",
        "price": 100,
        "damage": 10,
        "defense": 0,
        "hp_bonus": 0,
        "type": "weapon",
        "description": "Basic weapon for beginners"
    },
    "iron_sword": {
        "name": "⚔️ Iron Sword",
        "price": 300,
        "damage": 25,
        "defense": 0,
        "hp_bonus": 0,
        "type": "weapon",
        "description": "A sharp iron blade"
    },
    "steel_sword": {
        "name": "🔱 Steel Sword",
        "price": 600,
        "damage": 45,
        "defense": 0,
        "hp_bonus": 0,
        "type": "weapon",
        "description": "High-grade steel sword"
    },
    "legendary_blade": {
        "name": "✨ Legendary Blade",
        "price": 1500,
        "damage": 90,
        "defense": 0,
        "hp_bonus": 0,
        "type": "weapon",
        "description": "Forged in dragon fire"
    },
    "leather_armor": {
        "name": "🛡️ Leather Armor",
        "price": 150,
        "damage": 0,
        "defense": 10,
        "hp_bonus": 20,
        "type": "armor",
        "description": "Basic protection"
    },
    "iron_armor": {
        "name": "🔰 Iron Armor",
        "price": 400,
        "damage": 0,
        "defense": 25,
        "hp_bonus": 40,
        "type": "armor",
        "description": "Solid iron protection"
    },
    "dragon_armor": {
        "name": "🐉 Dragon Armor",
        "price": 1200,
        "damage": 0,
        "defense": 60,
        "hp_bonus": 100,
        "type": "armor",
        "description": "Made from dragon scales"
    },
    "health_potion": {
        "name": "🧪 Health Potion",
        "price": 80,
        "damage": 0,
        "defense": 0,
        "hp_bonus": 50,
        "type": "potion",
        "description": "Restores 50 HP instantly"
    },
    "mega_potion": {
        "name": "💊 Mega Potion",
        "price": 200,
        "damage": 0,
        "defense": 0,
        "hp_bonus": 120,
        "type": "potion",
        "description": "Restores 120 HP instantly"
    },
}

# Default HP
DEFAULT_HP = 100
MAX_HP = 200
