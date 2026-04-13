from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from models.group import set_economy, is_economy_open
from utils.helpers import is_admin
from config import WELCOME_IMAGE, SUPPORT_LINK, UPDATE_LINK, OWNER_LINK
import time


ECONOMY_TEXT = (
    "👛 <b>Economy Commands</b>\n"
    "━━━━━━━━━━━━━━━\n\n"
    "/bal — Check your wallet & stats\n"
    "/daily — Claim daily reward (200 coins)\n"
    "/claim — Group bonus (random 100–500)\n"
    "/mine — Mine coins (1hr cooldown)\n"
    "/farm — Farm coins (1hr cooldown)\n"
    "/crime — Commit a crime (risk & reward)\n"
    "/give [amt] @user — Transfer coins (10% tax)\n"
    "/bank — View bank balance\n"
    "/deposit [amt] — Deposit (10% daily interest)\n"
    "/withdraw [amt] — Withdraw from bank\n"
    "/loan [amt] — Take a loan (max 1000)\n"
    "/repay [amt] — Repay your loan\n"
    "/toprich — Top 10 richest users"
)

RPG_TEXT = (
    "⚔️ <b>RPG & War Commands</b>\n"
    "━━━━━━━━━━━━━━━\n\n"
    "/kill @user — Instantly kill & loot 75%\n"
    "/rob [amt] @user — Steal exact amount\n"
    "/protect 1d — 24h shield (100 coins)\n"
    "/revive — Come back to life (free)\n"
    "/heal — Heal 50 HP (100 coins)\n"
    "/shop — Browse weapons & armor\n"
    "/buy [item] — Buy an item\n"
    "/sell [item] — Sell an item\n"
    "/items — View your inventory\n"
    "/item [name] — Item details\n"
    "/topkill — Top 10 killers\n"
    "/ranking — Full leaderboard\n\n"
    "⚠️ <b>Rules:</b>\n"
    "• Dead users can't attack until /revive\n"
    "• Protected users can't be killed or robbed\n"
    "• Protection needs min 700 coins in wallet"
)

SOCIAL_TEXT = (
    "💍 <b>Social Commands</b>\n"
    "━━━━━━━━━━━━━━━\n\n"
    "/propose @user — Marry someone (5% tax)\n"
    "/marry — Check your marriage status\n"
    "/divorce — Break up (costs 2000 coins)\n"
    "/couple — Random matchmaking fun\n"
    "/crush @user — Send a crush interaction\n"
    "/love @user — Send a love interaction"
)

GROUP_TEXT = (
    "⛩️ <b>Group Commands</b>\n"
    "━━━━━━━━━━━━━━━\n\n"
    "/ping — Check bot status & latency\n"
    "/open — Open economy (admins only)\n"
    "/close — Close economy (admins only)\n"
    "/toprich — Top richest in this group\n"
    "/topkill — Top killers in this group\n"
    "/ranking — Full group leaderboard\n\n"
    "ℹ️ Economy commands only work in groups.\n"
    "Add the bot to your group to start playing!"
)


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Economy", callback_data="cmd_economy"),
            InlineKeyboardButton("⚔️ RPG & War", callback_data="cmd_rpg"),
        ],
        [
            InlineKeyboardButton("💍 Social", callback_data="cmd_social"),
            InlineKeyboardButton("⛩️ Group", callback_data="cmd_group"),
        ],
        [
            InlineKeyboardButton("🆘 Support", url=SUPPORT_LINK),
            InlineKeyboardButton("📢 Updates", url=UPDATE_LINK),
        ],
        [
            InlineKeyboardButton("👑 Owner", url=OWNER_LINK),
        ]
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Back", callback_data="cmd_back")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    user = update.effective_user

    # In group — just show simple message
    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(
            f"⚔️ <b>RPG Economy Bot is active!</b>\n"
            f"Use /help or message me privately for commands.",
            parse_mode="HTML"
        )
        return

    # Private chat — send welcome image + buttons
    welcome_text = (
        f"👋 <b>Hey, {user.first_name}!</b>\n\n"
        f"Welcome to <b>RPG Economy Bot</b> — your ultimate Telegram RPG experience!\n\n"
        f"⚔️ Fight, rob & kill other players\n"
        f"💰 Earn coins through mining, farming & crime\n"
        f"🏦 Invest in the bank & take loans\n"
        f"🛡️ Buy weapons, armor & potions\n"
        f"💍 Get married or break hearts\n\n"
        f"<i>Add me to your group and start playing!</i>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👇 Explore commands below:"
    )

    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=WELCOME_IMAGE,
            caption=welcome_text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    except Exception:
        # Fallback if image fails
        await update.message.reply_text(
            welcome_text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cmd_economy":
        await query.edit_message_caption(
            caption=ECONOMY_TEXT,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    elif data == "cmd_rpg":
        await query.edit_message_caption(
            caption=RPG_TEXT,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    elif data == "cmd_social":
        await query.edit_message_caption(
            caption=SOCIAL_TEXT,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    elif data == "cmd_group":
        await query.edit_message_caption(
            caption=GROUP_TEXT,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    elif data == "cmd_back":
        welcome_text = (
            f"👋 <b>Hey!</b>\n\n"
            f"Welcome to <b>RPG Economy Bot</b> — your ultimate Telegram RPG experience!\n\n"
            f"⚔️ Fight, rob & kill other players\n"
            f"💰 Earn coins through mining, farming & crime\n"
            f"🏦 Invest in the bank & take loans\n"
            f"🛡️ Buy weapons, armor & potions\n"
            f"💍 Get married or break hearts\n\n"
            f"<i>Add me to your group and start playing!</i>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👇 Explore commands below:"
        )
        await query.edit_message_caption(
            caption=welcome_text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    latency = int((time.time() - start) * 1000)
    await msg.edit_text(
        f"🏓 <b>Pong!</b>\n"
        f"⚡ Latency: {latency}ms\n"
        f"🤖 Bot is online and running!",
        parse_mode="HTML"
    )


async def open_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only group admins can use this command!")
        return

    group_id = update.effective_chat.id
    already_open = await is_economy_open(group_id)
    if already_open:
        await update.message.reply_text("✅ Economy is already open!")
        return

    await set_economy(group_id, True)
    await update.message.reply_text(
        "✅ <b>Economy is now OPEN!</b>\n"
        "💰 Users can now use all economy commands.",
        parse_mode="HTML"
    )


async def close_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only group admins can use this command!")
        return

    group_id = update.effective_chat.id
    already_closed = not await is_economy_open(group_id)
    if already_closed:
        await update.message.reply_text("❌ Economy is already closed!")
        return

    await set_economy(group_id, False)
    await update.message.reply_text(
        "🔒 <b>Economy is now CLOSED!</b>\n"
        "⛔ All economy commands are disabled.",
        parse_mode="HTML"
    )
