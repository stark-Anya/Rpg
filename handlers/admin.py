from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from models.group import set_economy, is_economy_open
from utils.helpers import is_admin
from config import WELCOME_IMAGE, SUPPORT_LINK, UPDATE_LINK, OWNER_LINK
import time


ECONOMY_TEXT = (
    "👛 <b>Economy Commands</b>\n"
    "━━━━━━━━━━━━━━━\n\n"

    "💰 <code>/bal</code>\n"
    "┗ Check your wallet balance, bank balance, loan, HP, kills & death count.\n\n"

    "🎁 <code>/daily</code>\n"
    "┗ Claim your daily reward of <b>200 coins</b>. Resets every <b>24 hours</b>.\n\n"

    "🎰 <code>/claim</code>\n"
    "┗ Claim a random group bonus of <b>100–500 coins</b>. Resets every <b>24 hours</b>.\n\n"

    "⛏️ <code>/mine</code>\n"
    "┗ Go mining and earn <b>1–100 random coins</b>. Cooldown: <b>1 hour</b>.\n\n"

    "🌾 <code>/farm</code>\n"
    "┗ Harvest your farm for <b>1–100 random coins</b>. Cooldown: <b>1 hour</b>.\n\n"

    "😈 <code>/crime</code>\n"
    "┗ Commit a crime for big rewards — but risk getting caught!\n"
    "┗ Success → earn <b>50–300 coins</b>. Fail → lose <b>30–200 coins</b>.\n\n"

    "💸 <code>/give [amount] @user</code>\n"
    "┗ Transfer coins to another user. A <b>10% tax</b> is deducted from your wallet.\n"
    "┗ Example: <code>/give 500</code> (reply to user) or <code>/give 123456 500</code>\n\n"

    "🏦 <code>/bank</code>\n"
    "┗ View your bank balance, active loan, and interest details.\n\n"

    "📥 <code>/deposit [amount]</code>\n"
    "┗ Deposit coins into your bank. Earns <b>10% interest daily</b> — money grows while you sleep!\n\n"

    "📤 <code>/withdraw [amount]</code>\n"
    "┗ Withdraw coins from your bank back to your wallet.\n\n"

    "🏧 <code>/loan [amount]</code>\n"
    "┗ Take an instant loan (max <b>1,000 coins</b>). Interest: <b>5% per day</b>. Pay it back fast!\n\n"

    "💳 <code>/repay [amount]</code>\n"
    "┗ Repay your active loan. Unpaid loans grow daily with 5% interest.\n\n"

    "🏆 <code>/toprich</code>\n"
    "┗ See the top 10 richest players in this group."
)

RPG_TEXT = (
    "⚔️ <b>RPG & War Commands</b>\n"
    "━━━━━━━━━━━━━━━\n\n"

    "💀 <code>/kill @user</code>\n"
    "┗ Instantly kill a player and loot <b>75% of their balance</b>.\n"
    "┗ Target must be alive and <b>unprotected</b>. Victim loses everything.\n\n"

    "🦹 <code>/rob [amount] @user</code>\n"
    "┗ Steal an exact amount of coins from a player's wallet.\n"
    "┗ Target must be alive and unprotected.\n"
    "┗ Example: <code>/rob 200</code> (reply) or <code>/rob 123456 200</code>\n\n"

    "🛡️ <code>/protect 1d</code>\n"
    "┗ Buy a <b>24-hour protection shield</b>. No one can kill or rob you.\n"
    "┗ Cost: <b>100 coins</b>. Requires minimum <b>700 coins</b> in wallet.\n\n"

    "💫 <code>/revive</code>\n"
    "┗ Revive yourself after being killed. <b>Completely free!</b>\n"
    "┗ Restores your HP and lets you play again.\n\n"

    "💊 <code>/heal</code>\n"
    "┗ Heal yourself for <b>50 HP</b>. Cost: <b>100 coins</b>.\n"
    "┗ If HP hits 0 → you die and lose 75% coins to your attacker!\n\n"

    "🏪 <code>/shop</code>\n"
    "┗ Browse all available weapons, armor & potions with prices and stats.\n\n"

    "🛒 <code>/buy [item]</code>\n"
    "┗ Buy an item from the shop. Higher price = more damage/defense.\n"
    "┗ Example: <code>/buy iron_sword</code>\n\n"

    "💰 <code>/sell [item]</code>\n"
    "┗ Sell an item for <b>50% of its buy price</b>.\n"
    "┗ Example: <code>/sell wooden_sword</code>\n\n"

    "🎒 <code>/items</code>\n"
    "┗ View all items in your inventory with equipped status.\n\n"

    "🔍 <code>/item [name]</code>\n"
    "┗ Check full details of any item — damage, defense, HP bonus, price.\n\n"

    "☠️ <code>/topkill</code>\n"
    "┗ See the top 10 deadliest killers in this group.\n\n"

    "🏅 <code>/ranking</code>\n"
    "┗ Full leaderboard sorted by kills and coins combined.\n\n"

    "⚠️ <b>Important Rules</b>\n"
    "┗ Dead players cannot kill, rob, mine or farm until they /revive\n"
    "┗ Protected players are immune to /kill and /rob\n"
    "┗ Protection requires minimum 700 coins in wallet"
)

SOCIAL_TEXT = (
    "💍 <b>Social Commands</b>\n"
    "━━━━━━━━━━━━━━━\n\n"

    "💍 <code>/propose @user</code>\n"
    "┗ Send a marriage proposal to another player.\n"
    "┗ A <b>5% tax</b> of your balance is charged. Both must be single!\n\n"

    "💑 <code>/marry</code>\n"
    "┗ Check your current marriage status and see who you're married to.\n\n"

    "💔 <code>/divorce</code>\n"
    "┗ End your marriage. Costs <b>2,000 coins</b>.\n"
    "┗ After divorce, both players are free to remarry.\n\n"

    "💘 <code>/couple</code>\n"
    "┗ Randomly pairs two players from the group as today's couple.\n"
    "┗ Fun matchmaking — no coins needed!\n\n"

    "😍 <code>/crush @user</code>\n"
    "┗ Interact with your crush! Sends a fun random message about your feelings.\n"
    "┗ Reply to a user or just use the command for a random match.\n\n"

    "❤️ <code>/love @user</code>\n"
    "┗ Send a love interaction to another player.\n"
    "┗ Random romantic messages — spread the love! 💕"
)

GROUP_TEXT = (
    "⛩️ <b>Group Commands</b>\n"
    "━━━━━━━━━━━━━━━\n\n"

    "🏓 <code>/ping</code>\n"
    "┗ Check if the bot is online and measure response latency.\n\n"

    "✅ <code>/open</code>  <i>(Admins only)</i>\n"
    "┗ Open the economy system in this group.\n"
    "┗ All economy, RPG and bank commands become available.\n\n"

    "🔒 <code>/close</code>  <i>(Admins only)</i>\n"
    "┗ Close the economy system in this group.\n"
    "┗ All commands are disabled until reopened by an admin.\n\n"

    "💰 <code>/toprich</code>\n"
    "┗ Leaderboard of the top 10 richest players in this group.\n\n"

    "☠️ <code>/topkill</code>\n"
    "┗ Leaderboard of the top 10 most deadly killers in this group.\n\n"

    "🏅 <code>/ranking</code>\n"
    "┗ Full leaderboard combining kills and coins for overall ranking.\n\n"

    "ℹ️ <b>Note:</b> All economy commands work in groups only.\n"
    "┗ Add this bot to your group and use <code>/open</code> to start!"
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


async def smart_edit(query, text: str, keyboard):
    """Handles both photo messages (caption) and text messages."""
    try:
        await query.edit_message_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception:
        try:
            await query.edit_message_text(
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception:
            pass


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cmd_economy":
        await smart_edit(query, ECONOMY_TEXT, back_keyboard())
    elif data == "cmd_rpg":
        await smart_edit(query, RPG_TEXT, back_keyboard())
    elif data == "cmd_social":
        await smart_edit(query, SOCIAL_TEXT, back_keyboard())
    elif data == "cmd_group":
        await smart_edit(query, GROUP_TEXT, back_keyboard())
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
        await smart_edit(query, welcome_text, main_menu_keyboard())


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
