import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.group import set_economy, is_economy_open
from utils.helpers import is_admin, is_owner, send_with_image
from config import (
    SUPPORT_LINK, UPDATE_LINK, OWNER_LINK,
    GUIDE_PDF_LINK, BOT_USERNAME, OWNER_ID, IMG_WELCOME,
    BANK_INTEREST_RATE, LOAN_INTEREST_RATE, DAILY_REWARD,
    MINE_MIN, MINE_MAX, FARM_MIN, FARM_MAX,
    CRIME_MIN_REWARD, CRIME_MAX_REWARD,
    PROTECT_COST_1D, PROTECT_COST_2D, PROTECT_COST_3D,
    LOAN_MAX, GIVE_TAX, SELL_RETURN_PERCENT
)


ECONOMY_TEXT = f"""💰 <b>Economy Commands</b>
━━━━━━━━━━━━━━━
<code>/bal</code> — Check wallet, bank & stats
<code>/daily</code> — Claim {DAILY_REWARD} coins every 24h
<code>/claim</code> — Random 100–500 group bonus (daily)
<code>/mine</code> — Earn {MINE_MIN}–{MINE_MAX} coins (1h cooldown)
<code>/farm</code> — Earn {FARM_MIN}–{FARM_MAX} coins (1h cooldown)
<code>/crime</code> — 60% chance {CRIME_MIN_REWARD}–{CRIME_MAX_REWARD} coins (1h cooldown)
<code>/give [amount]</code> — Send coins ({int(GIVE_TAX*100)}% tax)
<code>/toprich</code> — Top 10 richest players"""

BANK_TEXT = f"""🏦 <b>Bank Commands</b>
━━━━━━━━━━━━━━━
<code>/bank</code> — View bank & loan info
<code>/deposit [amount]</code> — Deposit coins (+{int(BANK_INTEREST_RATE*100)}%/day interest)
<code>/withdraw [amount]</code> — Withdraw from bank
<code>/loan [amount]</code> — Borrow up to {LOAN_MAX} coins ({int(LOAN_INTEREST_RATE*100)}%/day interest)
<code>/repay [amount]</code> — Repay active loan

💡 Keep coins in bank to earn interest daily!
⚠️ Loans grow {int(LOAN_INTEREST_RATE*100)}% per day — repay fast!"""

RPG_TEXT = f"""⚔️ <b>RPG Commands</b>
━━━━━━━━━━━━━━━
<code>/kill @user</code> — Kill & loot 90% wallet + 10% bank
<code>/rob [amount] @user</code> — Steal exact amount
<code>/protect 1d/2d/3d</code> — Shield from attacks ({PROTECT_COST_1D}/{PROTECT_COST_2D}/{PROTECT_COST_3D} coins)
<code>/revive</code> — Come back to life (free)
<code>/heal</code> — Restore 50 HP for 100 coins
<code>/hp</code> — Check HP status
<code>/profile</code> — Full RPG profile
<code>/topkill</code> — Top 10 killers
<code>/ranking</code> — Full leaderboard
<code>/wanted</code> — Today's most dangerous players"""

SHOP_TEXT = f"""🏪 <b>Shop Commands</b>
━━━━━━━━━━━━━━━
<code>/shop</code> — Browse weapons & flex items
<code>/sell [item]</code> — Sell flex items ({int(SELL_RETURN_PERCENT*100)}% return)
<code>/items</code> — View your inventory

⚔️ <b>Weapons</b> — Last 24h, boost kill loot
💎 <b>Flex & VIP</b> — Permanent collectibles"""

WAR_TEXT = """🥊 <b>War Commands</b>
━━━━━━━━━━━━━━━
<code>/war @user [amount]</code> — Challenge to a staked war
<code>/warlog</code> — Your war history & stats

⚔️ Higher weapon price = better chance of winning
🪙 Draw = coin flip decides winner
🏆 Winner takes 90% of pot"""

SOCIAL_TEXT = """💍 <b>Social Commands</b>
━━━━━━━━━━━━━━━
<code>/propose @user</code> — Send a marriage proposal (5% tax)
<code>/marry</code> — Check marriage status
<code>/divorce</code> — End marriage (costs 2000 coins)
<code>/couple</code> — Random group matchmaking
<code>/crush @user</code> — Send a fun crush message
<code>/love @user</code> — Send a love message"""

GROUP_TEXT = """⛩️ <b>Group Commands</b>
━━━━━━━━━━━━━━━
<code>/ping</code> — Bot status & latency
<code>/open</code> — Enable economy <i>(admins)</i>
<code>/close</code> — Disable economy <i>(admins)</i>
<code>/toprich</code> — Top 10 richest
<code>/topkill</code> — Top 10 killers
<code>/ranking</code> — Full leaderboard"""

OWNER_TEXT = """👑 <b>Owner Commands</b>
━━━━━━━━━━━━━━━
<code>/transfer @user [amount]</code> — Add coins to any user (no tax)
<code>/open</code> / <code>/close</code> — Control economy in any group

<i>Restricted to bot owner only.</i>"""

WELCOME_TEXT = """<blockquote><b>❖ ʜᴇʟʟᴏ {name} 💞</b>
<b>❖ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ <a href="https://t.me/KiaraGameBot">𒆜 𝑲𝑰𝑨𝑹𝑨 𒆜</a></b>
<blockquote expandable><b>⚔️ 𝐊ɪʟʟ, ʀᴏʙ & ᴡᴀʀ ᴘʟᴀʏᴇʀs</b>
<b>💰 𝐌ɪɴᴇ, ғᴀʀᴍ & ᴄᴏᴍᴍɪᴛ ᴄʀɪᴍᴇs</b>
<b>🏦 𝐄ᴀʀɴ ɪɴᴛᴇʀᴇsᴛ & ᴛᴀᴋᴇ ʟᴏᴀɴs</b>
<b>🛡️ 𝐁ᴜʏ ᴡᴇᴀᴘᴏɴs & ᴀʀᴍᴏʀ</b>
<b>💍 𝐌ᴀʀʀʏ ᴏʀ ʙʀᴇᴀᴋ ʜᴇᴀʀᴛ</b></blockquote>
<blockquote expandable><b>✦ 𝐀ᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴇɴᴊᴏʏ.</b></blockquote>"""

HELP_INTRO = f"""<b>❍ ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴄᴀᴛᴇɢᴏʀʏ ғᴏʀ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴɴᴀ ɢᴇᴛ ʜᴇʟᴘ.</b>
<b>❍ ғᴏʀ ᴀɴʏ ǫᴜᴇʀɪᴇs, ᴀsᴋ ɪɴ <a href="https://t.me/CarelessxWorld">sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a></b>

<b>❍ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ:</b><code> /</code>
"""


# ── Keyboards ───────────────────────────────────────────────────────────────

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✙ 𝐀ᴅᴅ 𝐌є 𝐈η 𝐘συʀ 𝐆ʀσυᴘ ✙", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("⌯ 𝐇єʟᴘ 𝐀ηᴅ 𝐂ᴏᴍᴍᴧηᴅ𝐬 ⌯", callback_data="menu_help")],
        [
            InlineKeyboardButton("⌯ 𝐒ᴜᴘᴘσʀᴛ ⌯", url=SUPPORT_LINK),
            InlineKeyboardButton("⌯ 𝐔ᴘᴅᴀᴛᴇ ⌯", url=UPDATE_LINK),
        ],
        [InlineKeyboardButton("⌯ 𝐌ʏ 𝐌ᴧsᴛᴇʀ ⌯", user_id=config.OWNER_ID)]
    ])


def help_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton("💰 Economy", callback_data="cmd_economy"),
            InlineKeyboardButton("🏦 Bank", callback_data="cmd_bank"),
        ],
        [
            InlineKeyboardButton("⚔️ RPG", callback_data="cmd_rpg"),
            InlineKeyboardButton("🥊 War", callback_data="cmd_war"),
        ],
        [
            InlineKeyboardButton("🏪 Shop", callback_data="cmd_shop"),
            InlineKeyboardButton("💍 Social", callback_data="cmd_social"),
        ],
        [InlineKeyboardButton("⛩️ Group", callback_data="cmd_group")],
    ]
    if user_id == OWNER_ID:
        buttons.append([InlineKeyboardButton("👑 Owner", callback_data="cmd_owner")])
    buttons.append([InlineKeyboardButton("◀️ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(buttons)


def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="menu_help")]])


# ── Handlers ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(
            "⚔️ <b>RPG Economy Bot is Active!</b>\nUse /open to enable economy (admins only).",
            parse_mode="HTML"
        )
        return

    text = WELCOME_TEXT.format(name=f"👋 <b>Hey, {user.first_name}!</b>")
    await send_with_image(update, update.effective_chat.id, IMG_WELCOME, text, reply_markup=main_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    await query.answer()
    data  = query.data

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
        await smart_edit(ECONOMY_TEXT, back_kb())
    elif data == "cmd_bank":
        await smart_edit(BANK_TEXT, back_kb())
    elif data == "cmd_rpg":
        await smart_edit(RPG_TEXT, back_kb())
    elif data == "cmd_war":
        await smart_edit(WAR_TEXT, back_kb())
    elif data == "cmd_shop":
        await smart_edit(SHOP_TEXT, back_kb())
    elif data == "cmd_social":
        await smart_edit(SOCIAL_TEXT, back_kb())
    elif data == "cmd_group":
        await smart_edit(GROUP_TEXT, back_kb())
    elif data == "cmd_owner":
        if user.id != OWNER_ID:
            await query.answer("❌ Owner only!", show_alert=True)
            return
        await smart_edit(OWNER_TEXT, back_kb())


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_t = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    latency = int((time.time() - start_t) * 1000)
    await msg.edit_text(
        f"🏓 <b>Pong!</b>  ⚡ {latency}ms  🟢 Online",
        parse_mode="HTML"
    )


async def open_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Admins only!")
        return
    group_id = update.effective_chat.id
    if await is_economy_open(group_id):
        await update.message.reply_text("✅ Economy is already open!")
        return
    await set_economy(group_id, True)
    await update.message.reply_text(
        "✅ <b>Economy opened!</b> All commands are now active.",
        parse_mode="HTML"
    )


async def close_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Admins only!")
        return
    group_id = update.effective_chat.id
    if not await is_economy_open(group_id):
        await update.message.reply_text("🔒 Economy is already closed!")
        return
    await set_economy(group_id, False)
    await update.message.reply_text(
        "🔒 <b>Economy closed!</b> All commands are disabled.",
        parse_mode="HTML"
    )
