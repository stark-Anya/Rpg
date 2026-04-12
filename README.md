# ⚔️ RPG Economy Bot — Telegram

A feature-rich RPG Economy Bot for Telegram groups with a full economy system, war mechanics, banking, shop, and social commands.

---

## 📋 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Commands](#-commands)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [License](#-license)

---

## ✨ Features

| Category | Details |
|---|---|
| 💰 Economy | Daily rewards, mining, farming, crime system |
| 🏦 Banking | Deposits with 10% daily interest, loans up to 1000 coins at 5% daily |
| ⚔️ RPG & War | Kill, rob, protect, revive, heal with HP system |
| 🏪 Shop | Weapons, armor, potions — damage scales with price |
| 💍 Social | Marriage, divorce, matchmaking, crush & love interactions |
| 📊 Leaderboards | Top rich, top killers, full ranking board |
| 🔒 Admin Controls | Group admins can open/close economy |

---

## 🛠 Requirements

- Python 3.10+
- MongoDB (local or Atlas)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

---

## 🚀 Installation

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/rpg-economy-bot.git
cd rpg-economy-bot
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Set up environment variables**

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_telegram_user_id
MONGO_URI=mongodb://localhost:27017
```

**4. Run the bot**

```bash
python main.py
```

---

## ⚙️ Configuration

All settings can be customized in `config.py`:

```python
STARTING_BALANCE = 200       # New user starting coins
DAILY_REWARD = 200           # /daily reward amount
MINE_COOLDOWN = 3600         # Mining cooldown (seconds)
KILL_LOOT_PERCENT = 0.75     # 75% loot on kill
PROTECT_COST = 100           # Protection shield cost
LOAN_MAX = 1000              # Maximum loan amount
BANK_INTEREST_RATE = 0.10    # 10% daily bank interest
LOAN_INTEREST_RATE = 0.05    # 5% daily loan interest
```

---

## 📖 Commands

### 👛 Economy

| Command | Description |
|---|---|
| `/bal` | Check wallet, bank & stats |
| `/daily` | Claim daily reward (200 coins, 24h cooldown) |
| `/claim` | Claim group bonus (random 100–500, 24h cooldown) |
| `/mine` | Mine coins (random 1–100, 1h cooldown) |
| `/farm` | Farm coins (random 1–100, 1h cooldown) |
| `/crime` | Commit a crime — random reward or penalty |
| `/give [amt] @user` | Transfer coins to user (10% tax) |
| `/transfer [amt] @user` | Owner only — send coins to any user |
| `/toprich` | Top 10 richest users |

### 🏦 Bank

| Command | Description |
|---|---|
| `/bank` | View bank balance, loan status |
| `/deposit [amt]` | Deposit coins — earns 10% daily interest |
| `/withdraw [amt]` | Withdraw from bank |
| `/loan [amt]` | Take a loan (max 1000 coins, 5% daily interest) |
| `/repay [amt]` | Repay your loan |

### ⚔️ RPG & War

| Command | Description |
|---|---|
| `/kill @user` | Instantly kill a user — loot 75% of their balance |
| `/rob [amt] @user` | Steal exact amount from a user |
| `/protect 1d` | Buy 24h shield (costs 100 coins, requires 700 min balance) |
| `/revive` | Revive yourself after death (free) |
| `/heal` | Heal 50 HP (costs 100 coins) |
| `/topkill` | Top 10 killers leaderboard |
| `/ranking` | Overall leaderboard (kills + coins) |

### 🏪 Shop

| Command | Description |
|---|---|
| `/shop` | Browse all weapons, armor & potions |
| `/buy [item]` | Buy an item from the shop |
| `/sell [item]` | Sell an item (50% of buy price) |
| `/items` | View your inventory |
| `/item [name]` | Check item details |

**Available Items:**

| Item | Price | Damage / Defense |
|---|---|---|
| 🗡️ Wooden Sword | 100 | 10 dmg |
| ⚔️ Iron Sword | 300 | 25 dmg |
| 🔱 Steel Sword | 600 | 45 dmg |
| ✨ Legendary Blade | 1500 | 90 dmg |
| 🛡️ Leather Armor | 150 | 10 def, +20 HP |
| 🔰 Iron Armor | 400 | 25 def, +40 HP |
| 🐉 Dragon Armor | 1200 | 60 def, +100 HP |
| 🧪 Health Potion | 80 | Restore 50 HP |
| 💊 Mega Potion | 200 | Restore 120 HP |

### 💍 Social

| Command | Description |
|---|---|
| `/propose @user` | Marry someone (5% tax on your balance) |
| `/marry` | Check your marriage status |
| `/divorce` | Break up (costs 2000 coins) |
| `/couple` | Random matchmaking in the group |
| `/crush @user` | Send a crush interaction |
| `/love @user` | Send a love interaction |

### ⛩️ Group Settings

| Command | Description | Access |
|---|---|---|
| `/ping` | Check bot status & latency | Everyone |
| `/open` | Open the economy | Admins only |
| `/close` | Close the economy | Admins only |
| `/start` | Show all commands | Everyone |

---

## ⚔️ RPG Rules

- **Kill** — Target must not have protection. Killer gets 75% of victim's balance. Victim status becomes `dead`.
- **Dead users** cannot use kill, rob, mine, farm, or crime until they `/revive`.
- **Protection** — Costs 100 coins. Requires minimum 700 coins in wallet. Lasts 24 hours.
- **Rob** — Steals exact amount from target's wallet. Target must be alive and unprotected.
- **Heal** — Restores 50 HP for 100 coins. HP depletes during combat.

---

## 📁 Project Structure

```
rpg_bot/
├── main.py              ← Entry point, all command handlers registered
├── config.py            ← All constants, economy values, shop items
├── database.py          ← MongoDB async connection (Motor)
├── requirements.txt     ← Python dependencies
├── .env.example         ← Environment variable template
│
├── models/
│   ├── user.py          ← User CRUD operations
│   └── group.py         ← Group settings (economy open/close)
│
├── utils/
│   └── helpers.py       ← Cooldown logic, admin checks, formatting
│
└── handlers/
    ├── economy.py       ← Economy commands
    ├── rpg.py           ← RPG & war commands
    ├── bank.py          ← Banking system
    ├── shop.py          ← Shop & inventory
    ├── social.py        ← Social & love commands
    └── admin.py         ← Admin & group commands
```

---

## 🌐 Deployment

### Railway (Recommended)

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) and create a new project
3. Connect your GitHub repo
4. Add environment variables (`BOT_TOKEN`, `OWNER_ID`, `MONGO_URI`)
5. Deploy — Railway auto-detects Python

### VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update && sudo apt install python3-pip -y
pip install -r requirements.txt

# Run with screen (keeps running after logout)
screen -S rpgbot
python main.py
# Press Ctrl+A then D to detach
```

### MongoDB Atlas (Free Cloud DB)

1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Create a free cluster
3. Get connection string and set as `MONGO_URI` in `.env`

---

## 🔑 Getting Your Owner ID

Send `/start` to [@userinfobot](https://t.me/userinfobot) on Telegram — it will return your user ID.

---

## 📝 License

This project is open-source. Feel free to modify and use it for your Telegram groups.

---

> Built with ❤️ using [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) & MongoDB
