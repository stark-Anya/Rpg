<div align="center">

<!-- Animated Header -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f0c29,50:302b63,100:24243e&height=200&section=header&text=⚔️%20RPG%20Economy%20Bot&fontSize=48&fontColor=ffffff&fontAlignY=38&desc=A%20full-featured%20Telegram%20RPG%20%26%20Economy%20system&descAlignY=58&descColor=a78bfa&animation=fadeIn" width="100%"/>

<!-- Badges Row 1 -->
<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/python--telegram--bot-21.5-26A5E4?style=for-the-badge&logo=telegram&logoColor=white"/>
  <img src="https://img.shields.io/badge/MongoDB-Motor-47A248?style=for-the-badge&logo=mongodb&logoColor=white"/>
</p>

<!-- Badges Row 2 -->
<p>
  <img src="https://img.shields.io/badge/License-MIT-a78bfa?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/PRs-Welcome-f97316?style=for-the-badge"/>
</p>

<!-- Quick Links -->
<p>
  <a href="https://t.me/KiaraGameBot"><img src="https://img.shields.io/badge/🤖%20Demo%20Bot-Launch-26A5E4?style=for-the-badge&logo=telegram"/></a>
  <a href="https://github.com/stark-Anya/Rpg"><img src="https://img.shields.io/badge/⭐%20Star%20Repo-GitHub-181717?style=for-the-badge&logo=github"/></a>
  <a href="https://t.me/CarelessxWorld"><img src="https://img.shields.io/badge/💬%20Support-Join-5865F2?style=for-the-badge&logo=telegram"/></a>
</p>

</div>

---

## ✨ Features

```
⚔️  Kill, Rob & War players          💰  Mine, Farm & commit crimes
🏦  Bank with 5% daily interest       💸  Loans with 10% daily interest  
🛡️  Buy Weapons & Protection          🏪  Full Shop with Flex & VIP items
💍  Marriage System                   🏆  Leaderboards & Rankings
🚨  Wanted System with Bounties       👑  Owner Admin Controls
```

---

## 📁 Project Structure

```
RPG-Bot/
├── main.py                  # Entry point
├── config.py                # All constants & settings
├── database.py              # MongoDB connection
├── requirements.txt
│
├── handlers/
│   ├── admin.py             # /start, /open, /close, /ping
│   ├── economy.py           # /bal, /daily, /mine, /farm, /crime, /give
│   ├── bank.py              # /bank, /deposit, /withdraw, /loan, /repay
│   ├── rpg.py               # /kill, /rob, /protect, /heal, /revive
│   ├── shop.py              # /shop, /sell
│   ├── social.py            # /propose, /marry, /divorce, /couple
│   └── war.py               # /war, /warlog, /wanted
│
├── models/
│   ├── user.py              # User DB operations
│   ├── group.py             # Group DB operations
│   └── war.py               # War DB operations
│
└── utils/
    └── helpers.py           # Shared utility functions
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```env
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_telegram_user_id
BOT_USERNAME=your_bot_username
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/

SUPPORT_LINK=https://t.me/CarelessxWorld
UPDATE_LINK=https://t.me/CarelessxCoder
OWNER_LINK=https://t.me/CarelessxOwner
GUIDE_PDF_LINK=https://your-guide-link.com

# Optional image URLs (leave empty to skip images)
IMG_WELCOME=
IMG_KILL=
IMG_SHOP=
# ... etc
```

---

## 🚀 Deployment Methods

<details>
<summary><b>🖥️ VPS Deployment (Recommended)</b></summary>

<br>

> Best for: Full control, best performance, 24/7 uptime

**Step 1 — Install dependencies**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip git screen -y
```

**Step 2 — Clone the repo**
```bash
git clone https://github.com/stark-Anya/Rpg.git
cd Rpg
```

**Step 3 — Install Python packages**
```bash
pip3 install -r requirements.txt
```

**Step 4 — Setup environment**
```bash
cp .env.example .env
nano .env   # Fill in your values
```

**Step 5 — Run with Screen (stays alive after logout)**
```bash
screen -S rpgbot
python3 main.py
# Press Ctrl+A then D to detach
```

**To reattach:**
```bash
screen -r rpgbot
```

**Or use systemd service for auto-restart:**
```bash
sudo nano /etc/systemd/system/rpgbot.service
```
```ini
[Unit]
Description=RPG Economy Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/Rpg
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable rpgbot
sudo systemctl start rpgbot
sudo systemctl status rpgbot
```

</details>

---

<details>
<summary><b>🟣 Heroku Deployment</b></summary>

<br>

> Best for: Free/cheap hosting with easy setup

**Step 1 — Install Heroku CLI**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

**Step 2 — Prepare files**

Create `Procfile` in root:
```
worker: python3 main.py
```

Create `runtime.txt`:
```
python-3.11.0
```

**Step 3 — Deploy**
```bash
git init
heroku create your-rpg-bot
git add .
git commit -m "Initial deploy"
git push heroku main
```

**Step 4 — Set environment variables**
```bash
heroku config:set BOT_TOKEN=your_token
heroku config:set OWNER_ID=your_id
heroku config:set MONGO_URI=your_mongo_uri
# Add all other env vars...
```

**Step 5 — Start worker**
```bash
heroku ps:scale worker=1
heroku logs --tail
```

> ⚠️ Use a **worker** dyno, NOT web. Bot uses polling not webhooks.

</details>

---

<details>
<summary><b>🔵 Render Deployment</b></summary>

<br>

> Best for: Simple setup, free tier available

**Step 1 — Push code to GitHub**
```bash
git init
git add .
git commit -m "Deploy RPG Bot"
git remote add origin https://github.com/stark-Anya/Rpg.git
git push -u origin main
```

**Step 2 — Create Background Worker on Render**

1. Go to [render.com](https://render.com) → New → **Background Worker**
2. Connect your GitHub repo
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`

**Step 3 — Add Environment Variables**

In Render dashboard → Environment tab, add:
```
BOT_TOKEN         = your_token
OWNER_ID          = your_id
MONGO_URI         = your_mongo_uri
BOT_USERNAME      = your_bot_username
SUPPORT_LINK      = https://t.me/CarelessxWorld
UPDATE_LINK       = https://t.me/CarelessxCoder
OWNER_LINK        = https://t.me/CarelessxOwner
```

**Step 4 — Deploy**

Click **Deploy** — Render will build and start automatically.

> 💡 Free tier may spin down after inactivity. Use paid plan for 24/7.

</details>

---

<details>
<summary><b>🚂 Railway Deployment</b></summary>

<br>

> Best for: Easiest setup, great free tier, no credit card needed

**Step 1 — Install Railway CLI**
```bash
npm i -g @railway/cli
railway login
```

**Step 2 — Initialize project**
```bash
cd Rpg
railway init
```

**Step 3 — Add environment variables**
```bash
railway variables set BOT_TOKEN=your_token
railway variables set OWNER_ID=your_id
railway variables set MONGO_URI=your_mongo_uri
railway variables set BOT_USERNAME=your_bot_username
```

**Step 4 — Deploy**
```bash
railway up
```

**Or deploy via Dashboard:**
1. Go to [railway.app](https://railway.app) → New Project
2. Deploy from GitHub → Select your repo
3. Add all env variables in the Variables tab
4. Railway auto-detects Python and deploys!

**Add start command** in `railway.json` (optional):
```json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": { "startCommand": "python main.py" }
}
```

> ✅ Railway gives $5 free credit monthly — enough for a bot!

</details>

---

<details>
<summary><b>🟠 Koyeb Deployment</b></summary>

<br>

> Best for: Always-on free tier, no sleep/spin-down

**Step 1 — Prepare Procfile**

Create `Procfile` in root:
```
worker: python main.py
```

**Step 2 — Push to GitHub**
```bash
git add .
git commit -m "Deploy to Koyeb"
git push
```

**Step 3 — Deploy on Koyeb**

1. Go to [koyeb.com](https://www.koyeb.com) → Create App
2. Select **GitHub** → Choose your repo
3. Set:
   - **Service type:** Worker
   - **Build command:** `pip install -r requirements.txt`
   - **Run command:** `python main.py`

**Step 4 — Environment Variables**

In Koyeb dashboard → Environment section:
```
BOT_TOKEN      → your_token
OWNER_ID       → your_id  
MONGO_URI      → your_mongo_uri
BOT_USERNAME   → your_bot_username
SUPPORT_LINK   → https://t.me/CarelessxWorld
UPDATE_LINK    → https://t.me/CarelessxCoder
OWNER_LINK     → https://t.me/CarelessxOwner
```

**Step 5 — Deploy**

Click **Deploy** — Koyeb will build from GitHub and run 24/7.

> 🆓 Koyeb free tier includes 1 always-on worker — perfect for bots!

</details>

---

## 🗄️ MongoDB Setup (Required for all methods)

1. Go to [mongodb.com/atlas](https://mongodb.com/atlas) → Create free cluster
2. Create a database user with read/write access
3. Whitelist IP: `0.0.0.0/0` (allow all)
4. Get connection string:
```
mongodb+srv://username:password@cluster.mongodb.net/rpg_bot
```
5. Paste into `MONGO_URI` in your environment variables

---

## 📜 Commands Reference

| Command | Description |
|---|---|
| `/bal` | Check wallet, gear & flex collection |
| `/daily` | Claim $200 daily reward |
| `/mine` / `/farm` | Earn coins (1h cooldown each) |
| `/crime` | 60% chance to earn, else lose coins |
| `/give @user amount` | Send coins (5% tax) |
| `/kill @user` | Kill & loot 90% wallet + 10% bank |
| `/rob @user amount` | Steal exact amount |
| `/protect 1d/2d/3d` | Buy shield from attacks |
| `/war @user amount` | Staked battle — higher weapon wins |
| `/shop` | Browse weapons & flex items |
| `/bank` | View bank info & interest |
| `/deposit` / `/withdraw` | Manage bank balance |
| `/loan` | Borrow up to $1000 (10%/day interest) |
| `/propose @user` | Send marriage proposal |
| `/open` / `/close` | Admin: enable/disable economy |

---

## 🔗 Important Links

<div align="center">

| | Link |
|---|---|
| 👑 **Owner** | [@CarelessxOwner](https://t.me/CarelessxOwner) — Mister Stark |
| 💬 **Support** | [@CarelessxWorld](https://t.me/CarelessxWorld) |
| 📢 **Updates** | [@CarelessxCoder](https://t.me/CarelessxCoder) |
| 🤖 **Demo Bot** | [@KiaraGameBot](https://t.me/KiaraGameBot) |
| 📦 **GitHub** | [stark-Anya/Rpg](https://github.com/stark-Anya/Rpg) |
| 🤖 **More Bots** | [@Anya_Bots](https://t.me/Anya_Bots) |

</div>

---

## 🤝 Contributing

```bash
# Fork → Clone → Branch → Code → PR

git clone https://github.com/stark-Anya/Rpg.git
cd Rpg
git checkout -b feature/your-feature
# Make your changes
git commit -m "Add: your feature"
git push origin feature/your-feature
# Open a Pull Request on GitHub
```

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:24243e,50:302b63,100:0f0c29&height=120&section=footer&text=Made%20with%20❤️%20by%20Mister%20Stark&fontSize=18&fontColor=a78bfa&fontAlignY=65" width="100%"/>

**⭐ Star this repo if it helped you!**

[![Star History](https://img.shields.io/github/stars/stark-Anya/Rpg?style=social)](https://github.com/stark-Anya/Rpg)

</div>
