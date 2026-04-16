#===================================================#
#=============== OWNER : MISTER STARK ==============#
#===================================================#
#======== CONTROL YOU BOT VALUES FROM HERE =========#
#===================================================#



import os
from dotenv import load_dotenv
load_dotenv()

# ── Bot ────────────────────────────────────────────────────────
BOT_TOKEN     = os.getenv("BOT_TOKEN", "BOT_TOKEN")
OWNER_ID      = int(os.getenv("OWNER_ID", "5864182070"))
BOT_USERNAME  = os.getenv("BOT_USERNAME", "KiaraGameBot") #WITHOUT @@@@@

# ── Links ──────────────────────────────────────────────────────
SUPPORT_LINK   = os.getenv("SUPPORT_LINK", "https://t.me/CarelessxWorld")
UPDATE_LINK    = os.getenv("UPDATE_LINK",  "https://t.me/CarelessxCoder")
OWNER_LINK     = os.getenv("OWNER_LINK",   "https://t.me/CarelessxOwner")
GUIDE_PDF_LINK = os.getenv("GUIDE_PDF_LINK","https://your-guide.com")

# ── MongoDB ────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "MONGO_URI")
DB_NAME   = "rpg_bot"

# ── Currency ───────────────────────────────────────────────────
CURRENCY_SYMBOL = "$" #in dollers

# ── Economy ────────────────────────────────────────────────────
STARTING_BALANCE     = 500
DAILY_REWARD         = 400
DAILY_COOLDOWN       = 86400   # 24h
CLAIM_MIN            = 200
CLAIM_MAX            = 500
CLAIM_COOLDOWN       = 86400   # 24h
MINE_MIN             = 100
MINE_MAX             = 200
MINE_COOLDOWN        = 3600    # 1h
FARM_MIN             = 100
FARM_MAX             = 200
FARM_COOLDOWN        = 3600    # 1h
CRIME_COOLDOWN       = 3600    # 1h — fixed (was using MINE_COOLDOWN)
CRIME_SUCCESS_CHANCE = 0.60
CRIME_MIN_REWARD     = 50
CRIME_MAX_REWARD     = 300
CRIME_MIN_PENALTY    = 30
CRIME_MAX_PENALTY    = 200
GIVE_TAX             = 0.05    # 5%

# ── Bank ───────────────────────────────────────────────────────
BANK_INTEREST_RATE  = 0.05     # 5% daily on deposits
BANK_MIN_DEPOSIT    = 100      # min deposit amount
LOAN_MAX            = 10000
LOAN_INTEREST_RATE  = 0.10     # 10% daily on loans

# ── RPG ────────────────────────────────────────────────────────
DEFAULT_HP             = 100
HEAL_COST              = 100
HEAL_AMOUNT            = 50
KILL_LOOT_PERCENT      = 0.90
KILL_BANK_PERCENT      = 0.10
PROTECT_COST_1D        = 200
PROTECT_COST_2D        = 300
PROTECT_COST_3D        = 450
PROTECT_MIN_BALANCE    = 700
WANTED_KILLS_THRESHOLD = 10
WANTED_BOUNTY          = 1000
SELL_RETURN_PERCENT    = 0.85

# ── War ────────────────────────────────────────────────────────
WAR_TIMEOUT        = 60
WAR_WINNER_PERCENT = 0.90
WAR_DRAW_PERCENT   = 0.45



#====== GIFT===================#
GIFT_SURCHARGE = 30   # Extra coins charged on top of item price for gifting

#=======KILL REWAERD===================#
KILL_REWARD_MIN = 300  # Minimum extra reward per kill
KILL_REWARD_MAX = 600  # Maximum Extra rewards per kill.


# ── Marriage ───────────────────────────────────────────────────
PROPOSE_TAX  = 0.05
DIVORCE_COST = 2000

# ── Images ─────────────────────────────────────────────────────
IMG_WELCOME  = os.getenv("IMG_WELCOME",  "https://o.uguu.se/CloZzFOg.jpg")
IMG_KILL     = os.getenv("IMG_KILL",     "https://h.uguu.se/AEcnTjiW.jpg")
IMG_ROB      = os.getenv("IMG_ROB",      "")
IMG_WAR_WIN  = os.getenv("IMG_WAR_WIN",  "https://d.uguu.se/hTRlxHjc.jpg")
IMG_WAR_DRAW = os.getenv("IMG_WAR_DRAW", "")
IMG_PROPOSE  = os.getenv("IMG_PROPOSE",  "https://o.uguu.se/tKXeGsNj.jpg")
IMG_MARRY    = os.getenv("IMG_MARRY",    "https://o.uguu.se/kzzLEkrf.jpg")
IMG_DIVORCE  = os.getenv("IMG_DIVORCE",  "https://h.uguu.se/wFuCeCPC.jpg")
IMG_DAILY    = os.getenv("IMG_DAILY",    "https://h.uguu.se/qTrVghqh.jpg")
IMG_CRIME    = os.getenv("IMG_CRIME",    "")
IMG_MINE     = os.getenv("IMG_MINE",     "https://n.uguu.se/iwdOYuiq.jpg")
IMG_FARM     = os.getenv("IMG_FARM",     "https://o.uguu.se/NPWbDeJH.jpg")
IMG_PROTECT  = os.getenv("IMG_PROTECT",  "")
IMG_REVIVE   = os.getenv("IMG_REVIVE",   "")
IMG_WANTED   = os.getenv("IMG_WANTED",   "")
IMG_SHOP     = os.getenv("IMG_SHOP",     "")
IMG_HEAL     = os.getenv("IMG_HEAL",     "")
IMG_GIFT     = os.getenv("IMG_GIFT",     "https://h.uguu.se/BWrgKcLO.jpg")


# ── Rarity ─────────────────────────────────────────────────────
def get_rarity(price: int) -> str:
    if price >= 500000:  return "🔴 Godly"
    if price >= 100000:  return "🟡 Legendary"
    if price >= 50000:   return "🔵 Rare"
    if price >= 10000:   return "🟣 Epic"
    if price >= 5000:    return "🟢 UnCommon"
    return "⚪ Common"

# ── Weapons ────────────────────────────────────────────────────
WEAPONS = {
    "stick":      {"name":"🪵 Stick",       "emoji":"🪵","price":500,    "kill_loot_bonus":0.01,"lifetime_hours":24,"desc":"A tree branch. Surprisingly deadly."},
    "brick":      {"name":"🧱 Brick",       "emoji":"🧱","price":800,    "kill_loot_bonus":0.02,"lifetime_hours":24,"desc":"A solid brick to the face."},
    "slingshot":  {"name":"🏹 Slingshot",   "emoji":"🏹","price":1200,   "kill_loot_bonus":0.03,"lifetime_hours":24,"desc":"Old but deadly."},
    "knife":      {"name":"🔪 Knife",       "emoji":"🔪","price":2000,   "kill_loot_bonus":0.05,"lifetime_hours":24,"desc":"Sharp and quick."},
    "bat":        {"name":"🏏 Bat",         "emoji":"🏏","price":3000,   "kill_loot_bonus":0.06,"lifetime_hours":24,"desc":"Home run or head run?"},
    "axe":        {"name":"🪓 Axe",         "emoji":"🪓","price":4000,   "kill_loot_bonus":0.08,"lifetime_hours":24,"desc":"Woodcutting... people."},
    "hammer":     {"name":"🔨 Hammer",      "emoji":"🔨","price":5000,   "kill_loot_bonus":0.09,"lifetime_hours":24,"desc":"Thor's budget version."},
    "pistol":     {"name":"🔫 Pistol",      "emoji":"🔫","price":6000,   "kill_loot_bonus":0.11,"lifetime_hours":24,"desc":"A classic sidearm."},
    "chainsaw":   {"name":"⛏️ Chainsaw",    "emoji":"⛏️","price":7000,   "kill_loot_bonus":0.14,"lifetime_hours":24,"desc":"Vroom vroom. RIP."},
    "shotgun":    {"name":"💥 Shotgun",     "emoji":"💥","price":10000,   "kill_loot_bonus":0.17,"lifetime_hours":24,"desc":"One shot, many problems."},
    "ak47":       {"name":"🔰 AK-47",       "emoji":"🔰","price":12000,  "kill_loot_bonus":0.22,"lifetime_hours":24,"desc":"The people's weapon."},
    "katana":     {"name":"⚔️ Katana",      "emoji":"⚔️","price":15000,  "kill_loot_bonus":0.27,"lifetime_hours":24,"desc":"Slice and dice."},
    "minigun":    {"name":"🌀 Minigun",     "emoji":"🌀","price":20000,  "kill_loot_bonus":0.33,"lifetime_hours":24,"desc":"Spray and pray."},
    "sniper":     {"name":"🎯 Sniper",      "emoji":"🎯","price":25000,  "kill_loot_bonus":0.40,"lifetime_hours":24,"desc":"One shot, one kill."},
    "rpg":        {"name":"🚀 RPG",         "emoji":"🚀","price":35000,  "kill_loot_bonus":0.50,"lifetime_hours":24,"desc":"Rocket-powered chaos."},
    "tank":       {"name":"🛡️ Tank",        "emoji":"🛡️","price":50000,  "kill_loot_bonus":0.65,"lifetime_hours":24,"desc":"Roll over everything."},
    "missile":    {"name":"💣 Missile",     "emoji":"💣","price":75000,  "kill_loot_bonus":0.80,"lifetime_hours":24,"desc":"Tactical destruction."},
    "laser":      {"name":"🔆 Laser",       "emoji":"🔆","price":100000, "kill_loot_bonus":1.00,"lifetime_hours":24,"desc":"Zap. Gone."},
    "death_note": {"name":"📓 Death Note",  "emoji":"📓","price":150000, "kill_loot_bonus":1.50,"lifetime_hours":24,"desc":"Write a name. They vanish."},
}

# ── Flex & VIP Items ───────────────────────────────────────────
FLEX_ITEMS = {
    "cookie":       {"name":"🍪 Cookie",        "emoji":"🍪","price":200,     "desc":"A useless item for rich people."},
    "starbucks":    {"name":"☕ Starbucks",     "emoji":"☕","price":1000,     "desc":"Overpriced coffee. Flex it."},
    "rose":         {"name":"🌹 Rose",          "emoji":"🌹","price":2000,     "desc":"Romantic and expensive."},
    "vodka":        {"name":"🍾 Vodka",         "emoji":"🍾","price":3000,     "desc":"Premium Russian water."},
    "diamond_ring": {"name":"💍 Diamond Ring",  "emoji":"💍","price":5000,    "desc":"Shine on you crazy diamond."},
    "ps5":          {"name":"🎮 PS5",           "emoji":"🎮","price":10000,    "desc":"Next-gen gaming. Pure flex."},
    "computer":     {"name":"🖥️ Computer",      "emoji":"🖥️","price":14000,    "desc":"RGB everything."},
    "macbook":      {"name":"💻 MacBook",       "emoji":"💻","price":18000,   "desc":"For the elite."},
    "iphone":       {"name":"📱 iPhone",        "emoji":"📱","price":20000,   "desc":"Latest model. Obviously."},
    "rolex":        {"name":"⌚ Rolex",          "emoji":"⌚","price":27000,   "desc":"Time is money, literally."},
    "suzuki":       {"name":"🚗 Suzuki",        "emoji":"🚗","price":50000,   "desc":"Entry-level baller."},
    "tesla":        {"name":"🚘 Tesla",         "emoji":"🚘","price":80000,   "desc":"Electric flex."},
    "Bus":          {"name":"🚌 Bus",           "emoji":"🚌","price":100000,  "desc":"A vehicle which can helps to earn money."},
    "formula":      {"name":"🏁 Formula 1",     "emoji":"🏎️","price":300000,  "desc":"You don't race, you just own it."},
    "helicopter":   {"name":"🚁 Helicopter",    "emoji":"🚁","price":500000,  "desc":"Above traffic, above problems."},
    "Train":        {"name":"🚆 Train",         "emoji":"🚆","price":800000,  "desc":"Fast public transport system."},
    "Privet_jet":   {"name":"✈️ Privet Jet",    "emoji":"✈️","price":1200000, "desc":"Luxury personal air travel."},
    "ship":         {"name":"🚢 Ship",          "emoji":"🚢","price":1500000, "desc":"Sail the seas of wealth."},
    "mansion":      {"name":"🏩 Mansion",       "emoji":"🏩","price":2000000, "desc":"50 rooms, all empty."},
    "ufo":          {"name":"🛸 UFO",           "emoji":"🛸","price":5000000, "desc":"Out of this world flex."},
    "island":       {"name":"🏝️ Island",        "emoji":"🏝️","price":10000000,"desc":"Your own country basically."},
}



#===================================================#
#=============== OWNER : MISTER STARK ==============#
#===================================================#
#============== CREDIT NA LENA BACHHO 🤣 ===========#
#===================================================#
