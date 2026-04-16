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


ECONOMY_TEXT = f"""<blockquote expandable>💰 <b>𝐄ᴄᴏɴᴏᴍʏ 𝐂ᴏᴍᴍᴀɴᴅs ❖</b></blockquote>
<b>◈ ━━━━━━ ⸙ ━━━━━━ ◈</b>
/bal ➻ <b>𝐂ʜᴇᴄᴋ ᴡᴀʟʟᴇᴛ, ʙᴀɴᴋ & sᴛᴀᴛs</b>  
/daily ➻ <b>𝐂ʟᴀɪᴍ {DAILY_REWARD} ᴍᴏɴᴇʏ ᴇᴠᴇʀʏ 24ʜ</b>  
/claim ➻ <b>𝐑ᴀɴᴅᴏᴍ 100–500 ɢʀᴏᴜᴘ ʙᴏɴᴜs (ᴅᴀɪʟʏ)</b>  
/mine ➻ <b>𝐄ᴀʀɴ {MINE_MIN}–{MINE_MAX} ᴍᴏɴᴇʏ (1ʜ ᴄᴏᴏʟᴅᴏᴡɴ)</b>  
/farm ➻ <b>𝐄ᴀʀɴ {FARM_MIN}–{FARM_MAX} ᴍᴏɴᴇʏ (1ʜ ᴄᴏᴏʟᴅᴏᴡɴ)</b>  
/crime ➻ <b>60% ᴄʜᴀɴᴄᴇ {CRIME_MIN_REWARD}–{CRIME_MAX_REWARD} ᴍᴏɴᴇʏ (1ʜ ᴄᴏᴏʟᴅᴏᴡɴ)</b>  
/give [amount] ➻ <b>𝐒ᴇɴᴅ ᴍᴏɴᴇʏ ({int(GIVE_TAX*100)}% ᴛᴀx)</b>  
/toprich ➻ <b>𝐓ᴏᴘ 10 ʀɪᴄʜᴇsᴛ ᴘʟᴀʏᴇʀs</b>"""

BANK_TEXT = f"""<blockquote expandable>🏦 <b>𝐁ᴀɴᴋ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
/bank ➻ <b>𝐕ɪᴇᴡ ʙᴀɴᴋ & ʟᴏᴀɴ ɪɴꜰᴏ</b>  
/deposit [amount] ➻ <b>𝐃ᴇᴘᴏsɪᴛ ᴍᴏɴᴇʏ (+{int(BANK_INTEREST_RATE*100)}%/ᴅᴀʏ ɪɴᴛᴇʀᴇsᴛ)</b>  
/withdraw [amount] ➻ <b>𝐖ɪᴛʜᴅʀᴀᴡ ꜰʀᴏᴍ ʙᴀɴᴋ</b>  
/loan [amount] ➻ <b>𝐁ᴏʀʀᴏᴡ ᴜᴘ ᴛᴏ {LOAN_MAX} ᴍᴏɴᴇʏ ({int(LOAN_INTEREST_RATE*100)}%/ᴅᴀʏ ɪɴᴛᴇʀᴇsᴛ)</b>  
/repay [amount] ➻ <b>𝐑ᴇᴘᴀʏ ᴀᴄᴛɪᴠᴇ ʟᴏᴀɴ</b>
<blockquote>💡 <b>𝐊ᴇᴇᴘ ᴄᴏɪɴs ɪɴ ʙᴀɴᴋ ᴛᴏ ᴇᴀʀɴ ɪɴᴛᴇʀᴇsᴛ ᴅᴀɪʟʏ!</b>  
⚠️ <b>𝐋ᴏᴀɴs ɢʀᴏᴡ {int(LOAN_INTEREST_RATE*100)}% ᴘᴇʀ ᴅᴀʏ — ʀᴇᴘᴀʏ ꜰᴀsᴛ!</b></blockquote>"""

RPG_TEXT = f"""<blockquote expandable>⚔️ <b>𝐑𝐏𝐆 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
/kill @user ➻ <b>𝐊ɪʟʟ & ʟᴏᴏᴛ 90% ᴡᴀʟʟᴇᴛ + 10% ʙᴀɴᴋ</b>  
/rob [amount] @user ➻ <b>𝐒ᴛᴇᴀʟ ᴇxᴀᴄᴛ ᴀᴍᴏᴜɴᴛ</b>  
/protect 1d/2d/3d ➻ <b>𝐒ʜɪᴇʟᴅ ꜰʀᴏᴍ ᴀᴛᴛᴀᴄᴋs ({PROTECT_COST_1D}/{PROTECT_COST_2D}/{PROTECT_COST_3D} ᴄᴏɪɴs)</b>  
/revive ➻ <b>𝐂ᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏ ʟɪꜰᴇ (ꜰʀᴇᴇ)</b>  
/heal ➻ <b>𝐑ᴇsᴛᴏʀᴇ 50 𝐇𝐏 ꜰᴏʀ 100 ᴄᴏɪɴs</b>  
/hp ➻ <b>𝐂ʜᴇᴄᴋ 𝐇𝐏 sᴛᴀᴛᴜs</b>  
/profile ➻ <b>𝐅ᴜʟʟ 𝐑𝐏𝐆 ᴘʀᴏꜰɪʟᴇ</b>  
/topkill ➻ <b>𝐓ᴏᴘ 10 ᴋɪʟʟᴇʀs</b>  
/ranking ➻ <b>𝐅ᴜʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>  
/wanted ➻ <b>𝐓ᴏᴅᴀʏ'𝐬 ᴍᴏsᴛ ᴅᴀɴɢᴇʀᴏᴜs ᴘʟᴀʏᴇʀs</b>"""

SHOP_TEXT = f"""<blockquote expandable>🏪 <b>𝐒ʜᴏᴘ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
/shop< ➻ <b>𝐁ʀᴏᴡsᴇ ᴡᴇᴀᴘᴏɴs & ꜰʟᴇx ɪᴛᴇᴍs</b>  
/sell [item] ➻ <b>𝐒ᴇʟʟ ꜰʟᴇx ɪᴛᴇᴍs ({int(SELL_RETURN_PERCENT*100)}% ʀᴇᴛᴜʀɴ)</b>  
<blockquote>⚔️ <b>𝐖ᴇᴀᴘᴏɴs</b> ➻ <b>𝐋ᴀsᴛ 24ʜ, ʙᴏᴏsᴛ ᴋɪʟʟ ʟᴏᴏᴛ</b>  
💎 <b>𝐅ʟᴇx & 𝐕𝐈𝐏</b> ➻ <b>𝐏ᴇʀᴍᴀɴᴇɴᴛ ᴄᴏʟʟᴇᴄᴛɪʙʟᴇs</b></blockquote>"""

WAR_TEXT = """<blockquote expandable>🥊 <b>𝐖ᴀʀ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
/war [uid] [amount] ➻ <b>𝐂ʜᴀʟʟᴇɴɢᴇ ᴛᴏ ᴀ sᴛᴀᴋᴇᴅ ᴡᴀʀ</b>  
/warlog ➻ <b>𝐘ᴏᴜʀ ᴡᴀʀ ʜɪsᴛᴏʀʏ & sᴛᴀᴛs</b>
<blockquote>⚔️ <b>𝐇ɪɢʜᴇʀ ᴡᴇᴀᴘᴏɴ ᴘʀɪᴄᴇ = ʙᴇᴛᴛᴇʀ ᴄʜᴀɴᴄᴇ ᴏꜰ ᴡɪɴɴɪɴɢ</b>  
🪙 <b>𝐃ʀᴀᴡ = ᴄᴏɪɴ ꜰʟɪᴘ ᴅᴇᴄɪᴅᴇs ᴡɪɴɴᴇʀ</b>  
🏆 <b>𝐖ɪɴɴᴇʀ ᴛᴀᴋᴇs 90% ᴏꜰ ᴘᴏᴛ</b></blockquote>"""

SOCIAL_TEXT = """<blockquote expandable>💍 <b>𝐒ᴏᴄɪᴀʟ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
/propose ➻ <b>𝐒ᴇɴᴅ ᴀ ᴍᴀʀʀɪᴀɢᴇ ᴘʀᴏᴘᴏsᴀʟ (5% ᴛᴀx)</b>  
/marry ➻ <b>𝐂ʜᴇᴄᴋ ᴍᴀʀʀɪᴀɢᴇ sᴛᴀᴛᴜs</b>  
/divorce ➻ <b>𝐄ɴᴅ ᴍᴀʀʀɪᴀɢᴇ (ᴄᴏsᴛs 2000 ᴄᴏɪɴs)</b>  
/couple ➻ <b>𝐑ᴀɴᴅᴏᴍ ɢʀᴏᴜᴘ ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ</b>  
/crush ➻ <b>𝐒ᴇɴᴅ ᴀ ꜰᴜɴ ᴄʀᴜsʜ ᴍᴇssᴀɢᴇ</b>  
/love ➻ <b>𝐒ᴇɴᴅ ᴀ ʟᴏᴠᴇ ᴍᴇssᴀɢᴇ</b>
/gift ➻ <b>𝐒ᴇɴᴅ ᴀ ɢɪꜰᴛ ᴛᴏ ʏᴏᴜ ꜰʀᴇɪɴᴅs.</b>
<blockquote expandable><b>𝐘ᴏᴜ ᴄᴀɴ ɢɪꜰᴛ ᴏɴʟʏ 𝐅ʟᴇ𝐱 & 𝐕𝐈𝐏 ɪᴛᴇᴍs.</b></blockquote>"""

GROUP_TEXT = """<blockquote expandable>⛩️ <b>𝐆ʀᴏᴜᴘ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
/ping ➻ <b>𝐁ᴏᴛ sᴛᴀᴛᴜs & ʟᴀᴛᴇɴᴄʏ</b>  
/open ➻ <b>𝐄ɴᴀʙʟᴇ ᴇᴄᴏɴᴏᴍʏ <i>(ᴀᴅᴍɪɴs)</i></b>  
/close ➻ <b>𝐃ɪsᴀʙʟᴇ ᴇᴄᴏɴᴏᴍʏ <i>(ᴀᴅᴍɪɴs)</i></b>  
/toprich ➻ <b>𝐓ᴏᴘ 10 ʀɪᴄʜᴇsᴛ</b>  
/topkill ➻ <b>𝐓ᴏᴘ 10 ᴋɪʟʟᴇʀs</b>  
/ranking ➻ <b>𝐅ᴜʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>"""

OWNER_TEXT = """<blockquote expandable>👑 <b>𝐎ᴡɴᴇʀ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
/transfer [userid] [amount] ➻ <b>𝐀ᴅᴅ ᴍᴏɴᴇʏ ᴛᴏ ᴀɴʏ ᴜsᴇʀ (ɴᴏ ᴛᴀx)</b>  
/deduct [userid] [ammount] ➻ <b>𝐃ᴇᴅᴜᴄᴛ ᴍᴏɴᴇʏ ꜰʀᴏᴍ ᴀɴʏ ᴜsᴇʀ</b>
/open ᴀɴᴅ /close ➻ <b>𝐂ᴏɴᴛʀᴏʟ ᴇᴄᴏɴᴏᴍʏ ɪɴ ᴀɴʏ ɢʀᴏᴜᴘ</b>

<i><b>𝐑ᴇsᴛʀɪᴄᴛᴇᴅ ᴛᴏ ʙᴏᴛ ᴏᴡɴᴇʀ ᴏɴʟʏ.</b></i>"""

WELCOME_TEXT = """<blockquote><b>❖ {name} 💞</b>
<b>❖ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ <a href="https://t.me/KiaraGameBot">𒆜 𝑲𝑰𝑨𝑹𝑨 𒆜</a></b></blockquote>
<blockquote expandable><b>⚔️ 𝐊ɪʟʟ, ʀᴏʙ & ᴡᴀʀ ᴘʟᴀʏᴇʀs</b>
<b>💰 𝐌ɪɴᴇ, ғᴀʀᴍ & ᴄᴏᴍᴍɪᴛ ᴄʀɪᴍᴇs</b>
<b>🏦 𝐄ᴀʀɴ ɪɴᴛᴇʀᴇsᴛ & ᴛᴀᴋᴇ ʟᴏᴀɴs</b>
<b>🛡️ 𝐁ᴜʏ ᴡᴇᴀᴘᴏɴs & ᴀʀᴍᴏʀ</b>
<b>💍 𝐌ᴀʀʀʏ ᴏʀ ʙʀᴇᴀᴋ ʜᴇᴀʀᴛ</b></blockquote>
<blockquote expandable><b>✦ 𝐀ᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴇɴᴊᴏʏ.</b></blockquote>"""

HELP_INTRO = f"""<blockquote><b>❍ ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴄᴀᴛᴇɢᴏʀʏ ғᴏʀ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴɴᴀ ɢᴇᴛ ʜᴇʟᴘ.</b>
<b>❍ ғᴏʀ ᴀɴʏ ǫᴜᴇʀɪᴇs, ᴀsᴋ ɪɴ <a href="https://t.me/CarelessxWorld">sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a></b></blockquote>
<blockquote><b>❍ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ:</b><code> /</code></blockquote>
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
        [InlineKeyboardButton("⌯ 𝐌ʏ 𝐌ᴧsᴛᴇʀ ⌯", url="https://t.me/CarelessxOwner")]
    ])


def help_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton("💰 𝐄ᴄᴏɴᴏᴍʏ ⌯", callback_data="cmd_economy"),
            InlineKeyboardButton("🏦 𝐁ᴀɴᴋ ⌯", callback_data="cmd_bank"),
        ],
        [
            InlineKeyboardButton("⚔️ 𝐑ᴘɢ ⌯", callback_data="cmd_rpg"),
            InlineKeyboardButton("🥊 𝐖ᴀʀ ⌯", callback_data="cmd_war"),
        ],
        [
            InlineKeyboardButton("🏪 𝐒ʜᴏᴘ ⌯", callback_data="cmd_shop"),
            InlineKeyboardButton("💍 𝐒ᴏᴄɪᴀʟ ⌯", callback_data="cmd_social"),
        ],
        [
            InlineKeyboardButton("⛩️ 𝐆ʀᴏᴜᴘ ⌯", callback_data="cmd_group"),
            InlineKeyboardButton("🎵 𝐌ᴜ𝐬ɪᴄ ⌯", url="https://t.me/Kellymusicebot?start=start"),
        ],
    ]
    if user_id == OWNER_ID:
        buttons.append([InlineKeyboardButton("👑 𝐎ᴡɴᴇʀ ⌯", callback_data="cmd_owner")])
    buttons.append([InlineKeyboardButton("⌯ 𝐁ᴀᴄᴋ ⌯", callback_data="menu_back")])
    return InlineKeyboardMarkup(buttons)


def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⌯ 𝐁ᴀᴄᴋ ⌯", callback_data="menu_help")]])
    

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


# ── Sudo Commands (Owner only) ───────────────────────────────────────────────

async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_owner(u.id):
        await update.message.reply_text("❌ Only the main owner can manage sudo users!")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: <code>/addsudo {userid}</code>", parse_mode="HTML")
        return

    try:
        tid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")
        return

    if tid == OWNER_ID:
        await update.message.reply_text("👑 That's already the main owner!")
        return

    from models.sudo import add_sudo
    # Try to get their name
    tname = str(tid)
    try:
        chat = await context.bot.get_chat(tid)
        tname = chat.first_name or tname
    except Exception:
        pass

    added = await add_sudo(tid, tname)
    if not added:
        await update.message.reply_text(f"⚠️ <b>{tname}</b> is already a sudo user!", parse_mode="HTML")
        return

    await update.message.reply_text(
        f"""✅ <b>Sudo Added!</b>
━━━━━━━━━━━━━━━
👤 User: <b>{tname}</b>
🆔 ID: <code>{tid}</code>
🔑 Powers: Owner-level commands""",
        parse_mode="HTML"
    )

    try:
        await context.bot.send_message(
            chat_id=tid,
            text="""👑 <b>You've been granted Sudo access!</b>
━━━━━━━━━━━━━━━
🔑 You now have owner-level command access.
⚠️ Use it responsibly!""",
            parse_mode="HTML"
        )
    except Exception:
        pass


async def rmsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_owner(u.id):
        await update.message.reply_text("❌ Only the main owner can manage sudo users!")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: <code>/rmsudo {userid}</code>", parse_mode="HTML")
        return

    try:
        tid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")
        return

    if tid == OWNER_ID:
        await update.message.reply_text("❌ Can't remove the main owner!")
        return

    from models.sudo import remove_sudo
    removed = await remove_sudo(tid)
    if not removed:
        await update.message.reply_text(f"⚠️ User <code>{tid}</code> is not a sudo user!", parse_mode="HTML")
        return

    await update.message.reply_text(
        f"""🚫 <b>Sudo Removed!</b>
━━━━━━━━━━━━━━━
🆔 ID: <code>{tid}</code>
❌ Powers revoked — normal user now.""",
        parse_mode="HTML"
    )

    try:
        await context.bot.send_message(
            chat_id=tid,
            text="⚠️ <b>Your sudo access has been revoked.</b>\nYou are now a normal user.",
            parse_mode="HTML"
        )
    except Exception:
        pass


async def sudolist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_owner(u.id):
        await update.message.reply_text("❌ Only the main owner can view sudo list!")
        return

    from models.sudo import get_all_sudos
    sudos = await get_all_sudos()

    if not sudos:
        await update.message.reply_text("📋 No sudo users currently.")
        return

    lines = "\n".join(
        f"{i+1}. <b>{s.get('username', 'Unknown')}</b> — <code>{s['user_id']}</code>"
        for i, s in enumerate(sudos)
    )
    await update.message.reply_text(
        f"""👑 <b>Sudo Users List</b>
━━━━━━━━━━━━━━━
{lines}
━━━━━━━━━━━━━━━
📊 Total: {len(sudos)}""",
        parse_mode="HTML"
    )
