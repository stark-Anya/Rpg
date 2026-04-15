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
<b>━━━━━━━━━━━━━━━━</b>
<code>/bal</code> ➻ <b>𝐂ʜᴇᴄᴋ ᴡᴀʟʟᴇᴛ, ʙᴀɴᴋ & sᴛᴀᴛs</b>  
<code>/daily</code> ➻ <b>𝐂ʟᴀɪᴍ {DAILY_REWARD} ᴄᴏɪɴs ᴇᴠᴇʀʏ 24ʜ</b>  
<code>/claim</code> ➻ <b>𝐑ᴀɴᴅᴏᴍ 100–500 ɢʀᴏᴜᴘ ʙᴏɴᴜs (ᴅᴀɪʟʏ)</b>  
<code>/mine</code> ➻ <b>𝐄ᴀʀɴ {MINE_MIN}–{MINE_MAX} ᴄᴏɪɴs (1ʜ ᴄᴏᴏʟᴅᴏᴡɴ)</b>  
<code>/farm</code> ➻ <b>𝐄ᴀʀɴ {FARM_MIN}–{FARM_MAX} ᴄᴏɪɴs (1ʜ ᴄᴏᴏʟᴅᴏᴡɴ)</b>  
<code>/crime</code> ➻ <b>60% ᴄʜᴀɴᴄᴇ {CRIME_MIN_REWARD}–{CRIME_MAX_REWARD} ᴄᴏɪɴs (1ʜ ᴄᴏᴏʟᴅᴏᴡɴ)</b>  
<code>/give [amount]</code> ➻ <b>𝐒ᴇɴᴅ ᴄᴏɪɴs ({int(GIVE_TAX*100)}% ᴛᴀx)</b>  
<code>/toprich</code> ➻ <b>𝐓ᴏᴘ 10 ʀɪᴄʜᴇsᴛ ᴘʟᴀʏᴇʀs</b>"""

BANK_TEXT = f"""<blockquote expandable>🏦 <b>𝐁ᴀɴᴋ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
━━━━━━━━━━━━━━━
<code>/bank</code> ➻ <b>𝐕ɪᴇᴡ ʙᴀɴᴋ & ʟᴏᴀɴ ɪɴꜰᴏ</b>  
<code>/deposit [amount]</code> ➻ <b>𝐃ᴇᴘᴏsɪᴛ ᴄᴏɪɴs (+{int(BANK_INTEREST_RATE*100)}%/ᴅᴀʏ ɪɴᴛᴇʀᴇsᴛ)</b>  
<code>/withdraw [amount]</code> ➻ <b>𝐖ɪᴛʜᴅʀᴀᴡ ꜰʀᴏᴍ ʙᴀɴᴋ</b>  
<code>/loan [amount]</code> ➻ <b>𝐁ᴏʀʀᴏᴡ ᴜᴘ ᴛᴏ {LOAN_MAX} ᴄᴏɪɴs ({int(LOAN_INTEREST_RATE*100)}%/ᴅᴀʏ ɪɴᴛᴇʀᴇsᴛ)</b>  
<code>/repay [amount]</code> ➻ <b>𝐑ᴇᴘᴀʏ ᴀᴄᴛɪᴠᴇ ʟᴏᴀɴ</b>
<blockquote>💡 <b>𝐊ᴇᴇᴘ ᴄᴏɪɴs ɪɴ ʙᴀɴᴋ ᴛᴏ ᴇᴀʀɴ ɪɴᴛᴇʀᴇsᴛ ᴅᴀɪʟʏ!</b>  
⚠️ <b>𝐋ᴏᴀɴs ɢʀᴏᴡ {int(LOAN_INTEREST_RATE*100)}% ᴘᴇʀ ᴅᴀʏ — ʀᴇᴘᴀʏ ꜰᴀsᴛ!</b></blockquote>"""

RPG_TEXT = f"""<blockquote expandable>⚔️ <b>𝐑𝐏𝐆 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
━━━━━━━━━━━━━━━
<code>/kill @user</code> ➻ <b>𝐊ɪʟʟ & ʟᴏᴏᴛ 90% ᴡᴀʟʟᴇᴛ + 10% ʙᴀɴᴋ</b>  
<code>/rob [amount] @user</code> ➻ <b>𝐒ᴛᴇᴀʟ ᴇxᴀᴄᴛ ᴀᴍᴏᴜɴᴛ</b>  
<code>/protect 1d/2d/3d</code> ➻ <b>𝐒ʜɪᴇʟᴅ ꜰʀᴏᴍ ᴀᴛᴛᴀᴄᴋs ({PROTECT_COST_1D}/{PROTECT_COST_2D}/{PROTECT_COST_3D} ᴄᴏɪɴs)</b>  
<code>/revive</code> ➻ <b>𝐂ᴏᴍᴇ ʙᴀᴄᴋ ᴛᴏ ʟɪꜰᴇ (ꜰʀᴇᴇ)</b>  
<code>/heal</code> ➻ <b>𝐑ᴇsᴛᴏʀᴇ 50 𝐇𝐏 ꜰᴏʀ 100 ᴄᴏɪɴs</b>  
<code>/hp</code> ➻ <b>𝐂ʜᴇᴄᴋ 𝐇𝐏 sᴛᴀᴛᴜs</b>  
<code>/profile</code> ➻ <b>𝐅ᴜʟʟ 𝐑𝐏𝐆 ᴘʀᴏꜰɪʟᴇ</b>  
<code>/topkill</code> ➻ <b>𝐓ᴏᴘ 10 ᴋɪʟʟᴇʀs</b>  
<code>/ranking</code> ➻ <b>𝐅ᴜʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>  
<code>/wanted</code> ➻ <b>𝐓ᴏᴅᴀʏ'𝐬 ᴍᴏsᴛ ᴅᴀɴɢᴇʀᴏᴜs ᴘʟᴀʏᴇʀs</b>"""

SHOP_TEXT = f"""<blockquote expandable>🏪 <b>𝐒ʜᴏᴘ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
━━━━━━━━━━━━━━━
<code>/shop</code> ➻ <b>𝐁ʀᴏᴡsᴇ ᴡᴇᴀᴘᴏɴs & ꜰʟᴇx ɪᴛᴇᴍs</b>  
<code>/sell [item]</code> ➻ <b>𝐒ᴇʟʟ ꜰʟᴇx ɪᴛᴇᴍs ({int(SELL_RETURN_PERCENT*100)}% ʀᴇᴛᴜʀɴ)</b>  
<code>/items</code> ➻ <b>𝐕ɪᴇᴡ ʏᴏᴜʀ ɪɴᴠᴇɴᴛᴏʀʏ</b>
<blockquote>⚔️ <b>𝐖ᴇᴀᴘᴏɴs</b> ➻ <b>𝐋ᴀsᴛ 24ʜ, ʙᴏᴏsᴛ ᴋɪʟʟ ʟᴏᴏᴛ</b>  
💎 <b>𝐅ʟᴇx & 𝐕𝐈𝐏</b> ➻ <b>𝐏ᴇʀᴍᴀɴᴇɴᴛ ᴄᴏʟʟᴇᴄᴛɪʙʟᴇs</b></blockquote>"""

WAR_TEXT = """<blockquote expandable>🥊 <b>𝐖ᴀʀ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
━━━━━━━━━━━━━━━
<code>/war @user [amount]</code> ➻ <b>𝐂ʜᴀʟʟᴇɴɢᴇ ᴛᴏ ᴀ sᴛᴀᴋᴇᴅ ᴡᴀʀ</b>  
<code>/warlog</code> ➻ <b>𝐘ᴏᴜʀ ᴡᴀʀ ʜɪsᴛᴏʀʏ & sᴛᴀᴛs</b>
<blockquote>⚔️ <b>𝐇ɪɢʜᴇʀ ᴡᴇᴀᴘᴏɴ ᴘʀɪᴄᴇ = ʙᴇᴛᴛᴇʀ ᴄʜᴀɴᴄᴇ ᴏꜰ ᴡɪɴɴɪɴɢ</b>  
🪙 <b>𝐃ʀᴀᴡ = ᴄᴏɪɴ ꜰʟɪᴘ ᴅᴇᴄɪᴅᴇs ᴡɪɴɴᴇʀ</b>  
🏆 <b>𝐖ɪɴɴᴇʀ ᴛᴀᴋᴇs 90% ᴏꜰ ᴘᴏᴛ</b></blockquote>"""

SOCIAL_TEXT = """<blockquote expandable>💍 <b>𝐒ᴏᴄɪᴀʟ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
━━━━━━━━━━━━━━━
<code>/propose @user</code> ➻ <b>𝐒ᴇɴᴅ ᴀ ᴍᴀʀʀɪᴀɢᴇ ᴘʀᴏᴘᴏsᴀʟ (5% ᴛᴀx)</b>  
<code>/marry</code> ➻ <b>𝐂ʜᴇᴄᴋ ᴍᴀʀʀɪᴀɢᴇ sᴛᴀᴛᴜs</b>  
<code>/divorce</code> ➻ <b>𝐄ɴᴅ ᴍᴀʀʀɪᴀɢᴇ (ᴄᴏsᴛs 2000 ᴄᴏɪɴs)</b>  
<code>/couple</code> ➻ <b>𝐑ᴀɴᴅᴏᴍ ɢʀᴏᴜᴘ ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ</b>  
<code>/crush @user</code> ➻ <b>𝐒ᴇɴᴅ ᴀ ꜰᴜɴ ᴄʀᴜsʜ ᴍᴇssᴀɢᴇ</b>  
<code>/love @user</code> ➻ <b>𝐒ᴇɴᴅ ᴀ ʟᴏᴠᴇ ᴍᴇssᴀɢᴇ</b>"""

GROUP_TEXT = """<blockquote expandable>⛩️ <b>𝐆ʀᴏᴜᴘ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
━━━━━━━━━━━━━━━
<code>/ping</code> ➻ <b>𝐁ᴏᴛ sᴛᴀᴛᴜs & ʟᴀᴛᴇɴᴄʏ</b>  
<code>/open</code> ➻ <b>𝐄ɴᴀʙʟᴇ ᴇᴄᴏɴᴏᴍʏ <i>(ᴀᴅᴍɪɴs)</i></b>  
<code>/close</code> ➻ <b>𝐃ɪsᴀʙʟᴇ ᴇᴄᴏɴᴏᴍʏ <i>(ᴀᴅᴍɪɴs)</i></b>  
<code>/toprich</code> ➻ <b>𝐓ᴏᴘ 10 ʀɪᴄʜᴇsᴛ</b>  
<code>/topkill</code> ➻ <b>𝐓ᴏᴘ 10 ᴋɪʟʟᴇʀs</b>  
<code>/ranking</code> ➻ <b>𝐅ᴜʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>"""

OWNER_TEXT = """<blockquote expandable>👑 <b>𝐎ᴡɴᴇʀ 𝐂ᴏᴍᴍᴀɴᴅs</b></blockquote>
━━━━━━━━━━━━━━━
<code>/transfer @user [amount]</code> ➻ <b>𝐀ᴅᴅ ᴄᴏɪɴs ᴛᴏ ᴀɴʏ ᴜsᴇʀ (ɴᴏ ᴛᴀx)</b>  
<code>/open</code> / <code>/close</code> ➻ <b>𝐂ᴏɴᴛʀᴏʟ ᴇᴄᴏɴᴏᴍʏ ɪɴ ᴀɴʏ ɢʀᴏᴜᴘ</b>

<i><b>𝐑ᴇsᴛʀɪᴄᴛᴇᴅ ᴛᴏ ʙᴏᴛ ᴏᴡɴᴇʀ ᴏɴʟʏ.</b></i>"""

WELCOME_TEXT = """<blockquote><b>❖ ʜᴇʟʟᴏ {name} 💞</b>
<b>❖ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ <a href="https://t.me/KiaraGameBot">𒆜 𝑲𝑰𝑨𝑹𝑨 𒆜</a></b></blockquote>
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
