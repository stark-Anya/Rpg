import os
from dotenv import load_dotenv
load_dotenv()

# ── Bot ────────────────────────────────────────────────────────
BOT_TOKEN     = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID      = int(os.getenv("OWNER_ID", "123456789"))
BOT_USERNAME  = os.getenv("BOT_USERNAME", "your_bot")

# ── Links ──────────────────────────────────────────────────────
SUPPORT_LINK     = os.getenv("SUPPORT_LINK", "https://t.me/support")
UPDATE_LINK      = os.getenv("UPDATE_LINK",  "https://t.me/updates")
OWNER_LINK       = os.getenv("OWNER_LINK",   "https://t.me/owner")
GUIDE_PDF_LINK   = os.getenv("GUIDE_PDF_LINK","https://your-guide.com")

# ── MongoDB ────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = "rpg_bot"

# ── Currency ───────────────────────────────────────────────────
CURRENCY_SYMBOL = "$"

# ── Economy ────────────────────────────────────────────────────
STARTING_BALANCE    = 500
DAILY_REWARD        = 200
DAILY_COOLDOWN      = 86400
CLAIM_MIN           = 100
CLAIM_MAX           = 500
CLAIM_COOLDOWN      = 86400
MINE_MIN            = 10
MINE_MAX            = 100
MINE_COOLDOWN       = 3600
FARM_MIN            = 10
FARM_MAX            = 100
FARM_COOLDOWN       = 3600
GIVE_TAX            = 0.05        # 5%
CRIME_SUCCESS_CHANCE= 0.60
CRIME_MIN_REWARD    = 50
CRIME_MAX_REWARD    = 300
CRIME_MIN_PENALTY   = 30
CRIME_MAX_PENALTY   = 200

# ── RPG ────────────────────────────────────────────────────────
KILL_LOOT_PERCENT      = 0.90     # 90% wallet + 10% bank
KILL_BANK_PERCENT      = 0.10     # 10% of bank goes to killer
PROTECT_COST_1D        = 100
PROTECT_COST_2D        = 180
PROTECT_COST_3D        = 250
PROTECT_MIN_BALANCE    = 700
BANK_MIN_DEPOSIT       = 2000
WANTED_KILLS_THRESHOLD = 10
WANTED_BOUNTY          = 500
SELL_RETURN_PERCENT    = 0.85     # 85% of buy price

# ── War ────────────────────────────────────────────────────────
WAR_TIMEOUT              = 60
WAR_WINNER_PERCENT       = 0.90
WAR_DRAW_PERCENT         = 0.45   # each gets 45% on draw

# ── Bank ───────────────────────────────────────────────────────
BANK_INTEREST_RATE  = 0.10
LOAN_MAX            = 1000
LOAN_INTEREST_RATE  = 0.05

# ── Marriage ───────────────────────────────────────────────────
PROPOSE_TAX   = 0.05
DIVORCE_COST  = 2000

# ── Images ─────────────────────────────────────────────────────
IMG_WELCOME  = os.getenv("IMG_WELCOME",  "")
IMG_KILL     = os.getenv("IMG_KILL",     "")
IMG_ROB      = os.getenv("IMG_ROB",      "")
IMG_WAR_WIN  = os.getenv("IMG_WAR_WIN",  "")
IMG_WAR_DRAW = os.getenv("IMG_WAR_DRAW", "")
IMG_PROPOSE  = os.getenv("IMG_PROPOSE",  "")
IMG_MARRY    = os.getenv("IMG_MARRY",    "")
IMG_DIVORCE  = os.getenv("IMG_DIVORCE",  "")
IMG_DAILY    = os.getenv("IMG_DAILY",    "")
IMG_CRIME    = os.getenv("IMG_CRIME",    "")
IMG_MINE     = os.getenv("IMG_MINE",     "")
IMG_FARM     = os.getenv("IMG_FARM",     "")
IMG_PROTECT  = os.getenv("IMG_PROTECT",  "")
IMG_REVIVE   = os.getenv("IMG_REVIVE",   "")
IMG_WANTED   = os.getenv("IMG_WANTED",   "")
IMG_SHOP     = os.getenv("IMG_SHOP",     "")

# ── Rarity by price ────────────────────────────────────────────
def get_rarity(price: int) -> str:
    if price >= 50000: return "🔴 GODLY"
    if price >= 10000: return "🟡 Legendary"
    if price >= 5000:  return "🔵 Rare"
    if price >= 1000:  return "🟣 Epic"
    if price >= 300:   return "🟢 Uncommon"
    return "⚪ Common"

# ── Weapons ────────────────────────────────────────────────────
# kill_loot_bonus = extra % on kill loot (0.01 = +1%)
# lifetime_hours  = how long weapon lasts
WEAPONS = {
    "stick":       {"name":"🪵 Stick",        "emoji":"🪵","price":500,   "kill_loot_bonus":0.01,"lifetime_hours":24, "desc":"A tree branch. Surprisingly deadly."},
    "brick":       {"name":"🧱 Brick",        "emoji":"🧱","price":800,   "kill_loot_bonus":0.02,"lifetime_hours":24, "desc":"A solid brick to the face."},
    "slingshot":   {"name":"🏹 Slingshot",    "emoji":"🏹","price":1200,  "kill_loot_bonus":0.03,"lifetime_hours":24, "desc":"Old but deadly."},
    "knife":       {"name":"🔪 Knife",        "emoji":"🔪","price":2000,  "kill_loot_bonus":0.05,"lifetime_hours":24, "desc":"Sharp and quick."},
    "bat":         {"name":"🏏 Bat",          "emoji":"🏏","price":2500,  "kill_loot_bonus":0.06,"lifetime_hours":24, "desc":"Home run or head run?"},
    "axe":         {"name":"🪓 Axe",          "emoji":"🪓","price":3500,  "kill_loot_bonus":0.08,"lifetime_hours":24, "desc":"Woodcutting... people."},
    "hammer":      {"name":"🔨 Hammer",       "emoji":"🔨","price":4000,  "kill_loot_bonus":0.09,"lifetime_hours":24, "desc":"Thor's budget version."},
    "pistol":      {"name":"🔫 Pistol",       "emoji":"🔫","price":5000,  "kill_loot_bonus":0.11,"lifetime_hours":24, "desc":"A classic sidearm."},
    "chainsaw":    {"name":"⛏️ Chainsaw",     "emoji":"⛏️","price":7000,  "kill_loot_bonus":0.14,"lifetime_hours":24, "desc":"Vroom vroom. RIP."},
    "shotgun":     {"name":"💥 Shotgun",      "emoji":"💥","price":9000,  "kill_loot_bonus":0.17,"lifetime_hours":24, "desc":"One shot, many problems."},
    "ak47":        {"name":"🔰 AK-47",        "emoji":"🔰","price":12000, "kill_loot_bonus":0.22,"lifetime_hours":24, "desc":"The people's weapon."},
    "katana":      {"name":"⚔️ Katana",       "emoji":"⚔️","price":15000, "kill_loot_bonus":0.27,"lifetime_hours":24, "desc":"Slice and dice."},
    "minigun":     {"name":"🌀 Minigun",      "emoji":"🌀","price":20000, "kill_loot_bonus":0.33,"lifetime_hours":24, "desc":"Spray and pray."},
    "sniper":      {"name":"🎯 Sniper",       "emoji":"🎯","price":25000, "kill_loot_bonus":0.40,"lifetime_hours":24, "desc":"One shot, one kill."},
    "rpg":         {"name":"🚀 RPG",          "emoji":"🚀","price":35000, "kill_loot_bonus":0.50,"lifetime_hours":24, "desc":"Rocket-powered chaos."},
    "tank":        {"name":"🛡️ Tank",         "emoji":"🛡️","price":50000, "kill_loot_bonus":0.65,"lifetime_hours":24, "desc":"Roll over everything."},
    "missile":     {"name":"💣 Missile",      "emoji":"💣","price":75000, "kill_loot_bonus":0.80,"lifetime_hours":24, "desc":"Tactical destruction."},
    "laser":       {"name":"🔆 Laser",        "emoji":"🔆","price":100000,"kill_loot_bonus":1.00,"lifetime_hours":24, "desc":"Zap. Gone."},
    "death_note":  {"name":"📓 Death Note",   "emoji":"📓","price":150000,"kill_loot_bonus":1.50,"lifetime_hours":24, "desc":"Write a name. They vanish."},
}

# ── Flex & VIP Items ───────────────────────────────────────────
FLEX_ITEMS = {
    "cookie":      {"name":"🍪 Cookie",       "emoji":"🍪","price":100,   "desc":"A useless item for rich people."},
    "starbucks":   {"name":"☕ Starbucks",    "emoji":"☕","price":300,   "desc":"Overpriced coffee. Flex it."},
    "rose":        {"name":"🌹 Rose",         "emoji":"🌹","price":500,   "desc":"Romantic and expensive."},
    "vodka":       {"name":"🍾 Vodka",        "emoji":"🍾","price":800,   "desc":"Premium Russian water."},
    "diamond_ring":{"name":"💍 Diamond Ring", "emoji":"💍","price":2000,  "desc":"Shine on you crazy diamond."},
    "ps5":         {"name":"🎮 PS5",          "emoji":"🎮","price":5000,  "desc":"Next-gen gaming. Pure flex."},
    "computer":    {"name":"🖥️ Computer",     "emoji":"🖥️","price":7000,  "desc":"RGB everything."},
    "macbook":     {"name":"💻 MacBook",      "emoji":"💻","price":10000, "desc":"For the elite."},
    "iphone":      {"name":"📱 iPhone",       "emoji":"📱","price":12000, "desc":"Latest model. Obviously."},
    "rolex":       {"name":"⌚ Rolex",         "emoji":"⌚","price":20000, "desc":"Time is money, literally."},
    "suzuki":      {"name":"🚗 Suzuki",       "emoji":"🚗","price":30000, "desc":"Entry-level baller."},
    "tesla":       {"name":"🚘 Tesla",        "emoji":"🚘","price":60000, "desc":"Electric flex."},
    "lamborghini": {"name":"🏎️ Lamborghini",  "emoji":"🏎️","price":150000,"desc":"Vroom at the speed of rich."},
    "formula":     {"name":"🏁 Formula 1",    "emoji":"🏁","price":300000,"desc":"You don't race, you just own it."},
    "helicopter":  {"name":"🚁 Helicopter",   "emoji":"🚁","price":500000,"desc":"Above traffic, above problems."},
    "ship":        {"name":"🚢 Ship",         "emoji":"🚢","price":1000000,"desc":"Sail the seas of wealth."},
    "mansion":     {"name":"🏩 Mansion",      "emoji":"🏩","price":2000000,"desc":"50 rooms, all empty."},
    "ufo":         {"name":"🛸 UFO",          "emoji":"🛸","price":5000000,"desc":"Out of this world flex."},
    "island":      {"name":"🏝️ Island",       "emoji":"🏝️","price":10000000,"desc":"Your own country basically."},
}
