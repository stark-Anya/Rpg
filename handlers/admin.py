import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.group import set_economy, is_economy_open
from utils.helpers import is_admin, is_owner, send_with_image
from config import (
    SUPPORT_LINK, UPDATE_LINK, OWNER_LINK,
    GUIDE_PDF_LINK, BOT_USERNAME, OWNER_ID, IMG_WELCOME
)


# ── Command descriptions ────────────────────────────────────────────────────

ECONOMY_TEXT = f"""👛 <b>Economy Commands</b>
━━━━━━━━━━━━━━━

💰 <code>/bal</code>
<blockquote>Check wallet, bank, HP & stats. Reply to see someone else's.</blockquote>

🎁 <code>/daily</code>
<blockquote>Claim 200 coins every 24 hours.</blockquote>

🎰 <code>/claim</code>
<blockquote>Random 100–500 coin group bonus. Resets daily.</blockquote>

⛏️ <code>/mine</code>
<blockquote>Mine 1–100 random coins. 1 hour cooldown.</blockquote>

🌾 <code>/farm</code>
<blockquote>Farm 1–100 random coins. 1 hour cooldown.</blockquote>

😈 <code>/crime</code>
<blockquote>60% chance: earn 50–300 coins. Fail: lose 30–200 coins.</blockquote>

💸 <code>/give [amount]</code>
<blockquote>Send coins to a user (reply or ID). 10% tax applied.</blockquote>

🏦 <code>/bank</code> | <code>/deposit</code> | <code>/withdraw</code>
<blockquote>Bank earns 10% daily interest. Keep coins safe from robbers!</blockquote>

🏧 <code>/loan [amount]</code>
<blockquote>Borrow up to 1,000 coins. 5% daily interest — pay fast!</blockquote>

💳 <code>/repay [amount]</code>
<blockquote>Repay your active loan.</blockquote>

💎 <code>/toprich</code>
<blockquote>Top 10 richest players in the group.</blockquote>"""

RPG_TEXT = f"""⚔️ <b>RPG & War Commands</b>
━━━━━━━━━━━━━━━

💀 <code>/kill @user</code>
<blockquote>Instantly kill a player — loot 75% of their wallet. Target must be alive & unprotected.</blockquote>

🦹 <code>/rob [amount] @user</code>
<blockquote>Steal exact amount from a player's wallet.</blockquote>

🛡️ <code>/protect 1d</code>
<blockquote>24h shield — costs 100 coins, needs min 700 coins in wallet.</blockquote>

💫 <code>/revive</code>
<blockquote>Revive yourself after death. Free!</blockquote>

💊 <code>/heal</code>
<blockquote>Restore 50 HP for 100 coins.</blockquote>

❤️ <code>/hp</code>
<blockquote>Check HP. Reply to see someone else's HP.</blockquote>

👤 <code>/profile</code>
<blockquote>Full RPG profile — kills, wars, gear, net worth. Reply for others.</blockquote>

🥊 <code>/war @user [amount]</code>
<blockquote>Staked war! Both pay the amount. Winner takes 90% of pot. Draw = coin flip!</blockquote>

📜 <code>/warlog</code>
<blockquote>Your war history — wins, losses, earnings.</blockquote>

🚨 <code>/wanted</code>
<blockquote>Today's most dangerous players (10+ kills = 500 coin bounty on their head).</blockquote>

🏪 <code>/shop</code> | <code>/buy</code> | <code>/sell</code> | <code>/items</code>
<blockquote>Buy weapons & armor. Higher price = more damage. Sell for 50% back.</blockquote>

☠️ <code>/topkill</code> | 🏆 <code>/ranking</code>
<blockquote>Leaderboards — top killers and overall ranking.</blockquote>"""

SOCIAL_TEXT = f"""💍 <b>Social Commands</b>
━━━━━━━━━━━━━━━

💍 <code>/propose @user</code>
<blockquote>Send a marriage proposal. 5% tax on your balance. Recipient must accept!</blockquote>

💑 <code>/marry</code>
<blockquote>Check your marriage status.</blockquote>

💔 <code>/divorce</code>
<blockquote>End your marriage. Costs 2,000 coins.</blockquote>

💘 <code>/couple</code>
<blockquote>Randomly match two players from the group — just for fun!</blockquote>

😍 <code>/crush @user</code>
<blockquote>Send a fun crush interaction.</blockquote>

❤️ <code>/love @user</code>
<blockquote>Send a love interaction to another player.</blockquote>"""

GROUP_TEXT = f"""⛩️ <b>Group Commands</b>
━━━━━━━━━━━━━━━

🏓 <code>/ping</code>
<blockquote>Check bot status and latency.</blockquote>

✅ <code>/open</code>  <i>(Admins only)</i>
<blockquote>Open the economy — all commands become available.</blockquote>

🔒 <code>/close</code>  <i>(Admins only)</i>
<blockquote>Close the economy — all commands disabled.</blockquote>

💎 <code>/toprich</code>
<blockquote>Top 10 richest players in this group.</blockquote>

☠️ <code>/topkill</code>
<blockquote>Top 10 killers in this group.</blockquote>

🏆 <code>/ranking</code>
<blockquote>Full leaderboard by kills and coins.</blockquote>

ℹ️ <i>Add this bot to your group and use /open to start playing!</i>"""

OWNER_TEXT = f"""👑 <b>Owner Commands</b>
━━━━━━━━━━━━━━━

💰 <code>/transfer @user [amount]</code>
<blockquote>Add any amount of coins to any user. No tax. User gets notified in private.</blockquote>

✅ <code>/open</code> | 🔒 <code>/close</code>
<blockquote>Open or close the economy in any group.</blockquote>

<i>These commands are restricted to the bot owner only.</i>"""


# ── Keyboards ───────────────────────────────────────────────────────────────

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me to a Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [
            InlineKeyboardButton("📖 Help", callback_data="menu_help"),
            InlineKeyboardButton("🤖 More Bots", url=f"https://t.me/Anya_Bots"),
        ],
        [
            InlineKeyboardButton("🆘 Support", url=SUPPORT_LINK),
            InlineKeyboardButton("📢 Updates", url=UPDATE_LINK),
        ],
        [InlineKeyboardButton("👑 Owner", url=OWNER_LINK)]
    ])


def help_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton("💰 Economy", callback_data="cmd_economy"),
            InlineKeyboardButton("⚔️ RPG & War", callback_data="cmd_rpg"),
        ],
        [
            InlineKeyboardButton("💍 Social", callback_data="cmd_social"),
            InlineKeyboardButton("⛩️ Group", callback_data="cmd_group"),
        ],
        [
            InlineKeyboardButton("🎵 Music", url=f"https://t.me/Kellymusicebot?start=start"),
            InlineKeyboardButton("🛡️ Group Help", url=f"https://t.me/EdithHelpsBot?start=start"),
        ],
    ]
    if user_id == OWNER_ID:
        buttons.append([InlineKeyboardButton("👑 Owner Commands", callback_data="cmd_owner")])
    buttons.append([InlineKeyboardButton("◀️ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(buttons)


def back_to_help_keyboard(user_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Back", callback_data="menu_help")]
    ])


# ── Handlers ────────────────────────────────────────────────────────────────

WELCOME_TEXT = """{name}

<b>Welcome to RPG Economy Bot!</b>

⚔️ Fight, rob & kill players
💰 Mine, farm & commit crimes
🏦 Invest in the bank & take loans
🛡️ Buy weapons, armor & potions
💍 Get married or break hearts

<i>Add me to your group and start playing!</i>"""

HELP_INTRO = f"""📖 <b>Help & Commands</b>
━━━━━━━━━━━━━━━
📄 <a href="{GUIDE_PDF_LINK}">Download Full Guide PDF</a>

Choose a category below 👇"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(
            f"""⚔️ <b>RPG Economy Bot is Active!</b>
Use /open to enable economy (admins only).
Message me privately for commands & guide!""",
            parse_mode="HTML"
        )
        return

    text = WELCOME_TEXT.format(name=f"👋 <b>Hey, {user.first_name}!</b>")
    await send_with_image(update, update.effective_chat.id, IMG_WELCOME, text, reply_markup=main_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    data = query.data

    async def smart_edit(text, keyboard=None):
        try:
            await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
        except Exception:
            try:
                await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=keyboard)
            except Exception:
                pass

    if data == "menu_help":
        await smart_edit(HELP_INTRO, help_keyboard(user.id))

    elif data == "menu_back":
        text = WELCOME_TEXT.format(name="👋 <b>Hey!</b>")
        await smart_edit(text, main_keyboard())

    elif data == "cmd_economy":
        await smart_edit(ECONOMY_TEXT, back_to_help_keyboard(user.id))

    elif data == "cmd_rpg":
        await smart_edit(RPG_TEXT, back_to_help_keyboard(user.id))

    elif data == "cmd_social":
        await smart_edit(SOCIAL_TEXT, back_to_help_keyboard(user.id))

    elif data == "cmd_group":
        await smart_edit(GROUP_TEXT, back_to_help_keyboard(user.id))

    elif data == "cmd_owner":
        if user.id != OWNER_ID:
            await query.answer("❌ Owner only!", show_alert=True)
            return
        await smart_edit(OWNER_TEXT, back_to_help_keyboard(user.id))


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    latency = int((time.time() - start) * 1000)
    await msg.edit_text(
        f"""🏓 <b>Pong!</b>
⚡ <b>Latency:</b> {latency}ms
🤖 <b>Status:</b> Online & Running!""",
        parse_mode="HTML"
    )


async def open_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only group admins can use this!")
        return
    group_id = update.effective_chat.id
    if await is_economy_open(group_id):
        await update.message.reply_text("✅ Economy is already open!")
        return
    await set_economy(group_id, True)
    await update.message.reply_text(
        "✅ <b>Economy is now OPEN!</b>\n💰 All commands are now available.",
        parse_mode="HTML"
    )


async def close_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only group admins can use this!")
        return
    group_id = update.effective_chat.id
    if not await is_economy_open(group_id):
        await update.message.reply_text("🔒 Economy is already closed!")
        return
    await set_economy(group_id, False)
    await update.message.reply_text(
        "🔒 <b>Economy is now CLOSED!</b>\n⛔ All commands are disabled.",
        parse_mode="HTML"
    )
