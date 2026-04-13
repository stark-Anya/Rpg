import time
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user, get_top_killers
from utils.helpers import (
    check_economy, format_coins, get_target_user
)
from config import *


def is_protected(user_data: dict) -> bool:
    if not user_data.get("protected_until"):
        return False
    return time.time() < user_data["protected_until"]


async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    killer = update.effective_user
    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    if not target_id:
        await update.message.reply_text("❌ Reply to a user or provide user ID to kill.")
        return
    if target_id == killer.id:
        await update.message.reply_text("❌ You can't kill yourself!")
        return

    killer_data = await get_user(killer.id, group_id, killer.first_name)
    if killer_data["status"] == "dead":
        await update.message.reply_text(
            "💀 You are dead! Use /revive to come back to life."
        )
        return

    victim_data = await get_user(target_id, group_id, target_name)
    if victim_data["status"] == "dead":
        await update.message.reply_text(f"💀 <b>{target_name}</b> is already dead!", parse_mode="HTML")
        return

    if is_protected(victim_data):
        await update.message.reply_text(
            f"🛡️ <b>{target_name}</b> is protected! You can't kill them right now.",
            parse_mode="HTML"
        )
        return

    loot = int(victim_data["balance"] * KILL_LOOT_PERCENT)
    new_killer_balance = killer_data["balance"] + loot

    await update_user(killer.id, group_id, {
        "balance": new_killer_balance,
        "kills": killer_data["kills"] + 1
    })
    await update_user(target_id, group_id, {
        "balance": 0,
        "status": "dead",
        "deaths": victim_data["deaths"] + 1
    })

    await update.message.reply_text(
        f"⚔️ <b>{killer.first_name}</b> killed <b>{target_name}</b>!\n"
        f"💀 {target_name} is now dead and lost everything.\n"
        f"💰 Looted: {format_coins(loot)}\n"
        f"👛 {killer.first_name}'s balance: {format_coins(new_killer_balance)}",
        parse_mode="HTML"
    )


async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    robber = update.effective_user
    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    try:
        if update.message.reply_to_message:
            amount = int(context.args[0])
        else:
            amount = int(context.args[1]) if len(context.args) >= 2 else None
    except (IndexError, ValueError, TypeError):
        amount = None

    if not target_id or not amount:
        await update.message.reply_text(
            "❌ Usage: Reply + <code>/rob [amount]</code>\n"
            "Or: <code>/rob [user_id] [amount]</code>",
            parse_mode="HTML"
        )
        return

    if target_id == robber.id:
        await update.message.reply_text("❌ You can't rob yourself!")
        return
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    robber_data = await get_user(robber.id, group_id, robber.first_name)
    if robber_data["status"] == "dead":
        await update.message.reply_text("💀 You are dead! Use /revive first.")
        return

    victim_data = await get_user(target_id, group_id, target_name)
    if victim_data["status"] == "dead":
        await update.message.reply_text(f"💀 <b>{target_name}</b> is already dead!", parse_mode="HTML")
        return

    if is_protected(victim_data):
        await update.message.reply_text(
            f"🛡️ <b>{target_name}</b> is protected! You can't rob them.",
            parse_mode="HTML"
        )
        return

    if victim_data["balance"] < amount:
        await update.message.reply_text(
            f"❌ <b>{target_name}</b> only has {format_coins(victim_data['balance'])}!",
            parse_mode="HTML"
        )
        return

    new_robber_balance = robber_data["balance"] + amount
    new_victim_balance = victim_data["balance"] - amount

    await update_user(robber.id, group_id, {"balance": new_robber_balance})
    await update_user(target_id, group_id, {"balance": new_victim_balance})

    await update.message.reply_text(
        f"🦹 <b>{robber.first_name}</b> robbed <b>{target_name}</b>!\n"
        f"💰 Stolen: {format_coins(amount)}\n"
        f"👛 Your balance: {format_coins(new_robber_balance)}\n"
        f"😢 {target_name}'s balance: {format_coins(new_victim_balance)}",
        parse_mode="HTML"
    )


async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if data["status"] == "dead":
        await update.message.reply_text("💀 You are dead! Use /revive first.")
        return

    if is_protected(data):
        remaining = int(data["protected_until"] - time.time())
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        await update.message.reply_text(
            f"🛡️ You are already protected!\n"
            f"⏳ Expires in: {hours}h {mins}m"
        )
        return

    if data["balance"] < PROTECT_MIN_BALANCE:
        await update.message.reply_text(
            f"❌ You need at least {format_coins(PROTECT_MIN_BALANCE)} to buy protection.\n"
            f"💰 You have: {format_coins(data['balance'])}",
            parse_mode="HTML"
        )
        return

    new_balance = data["balance"] - PROTECT_COST
    protected_until = time.time() + PROTECT_DURATION

    await update_user(user.id, group_id, {
        "balance": new_balance,
        "protected_until": protected_until
    })
    await update.message.reply_text(
        f"🛡️ Protection activated for 24 hours!\n"
        f"💸 Cost: {format_coins(PROTECT_COST)}\n"
        f"👛 Balance: {format_coins(new_balance)}\n"
        f"🔒 No one can kill or rob you for 24h!",
        parse_mode="HTML"
    )


async def revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if data["status"] == "alive":
        await update.message.reply_text("✅ You are already alive!")
        return

    await update_user(user.id, group_id, {
        "status": "alive",
        "hp": data["max_hp"]
    })
    await update.message.reply_text(
        f"💫 <b>{user.first_name}</b> has been revived!\n"
        f"❤️ HP restored to {data['max_hp']}\n"
        f"⚔️ You can now play again!",
        parse_mode="HTML"
    )


async def heal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if data["status"] == "dead":
        await update.message.reply_text("💀 You are dead! Use /revive first.")
        return

    if data["hp"] >= data["max_hp"]:
        await update.message.reply_text(f"❤️ You are already at full HP ({data['max_hp']})!")
        return

    if data["balance"] < HEAL_COST:
        await update.message.reply_text(
            f"❌ Not enough coins to heal!\n"
            f"💸 Cost: {format_coins(HEAL_COST)}\n"
            f"💰 You have: {format_coins(data['balance'])}",
            parse_mode="HTML"
        )
        return

    heal_amount = min(50, data["max_hp"] - data["hp"])
    new_hp = data["hp"] + heal_amount
    new_balance = data["balance"] - HEAL_COST

    await update_user(user.id, group_id, {
        "hp": new_hp,
        "balance": new_balance
    })
    await update.message.reply_text(
        f"💊 <b>{user.first_name}</b> healed!\n"
        f"❤️ HP: {data['hp']} → {new_hp}/{data['max_hp']}\n"
        f"💸 Cost: {format_coins(HEAL_COST)}\n"
        f"👛 Balance: {format_coins(new_balance)}",
        parse_mode="HTML"
    )


async def topkill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    users = await get_top_killers(group_id)
    if not users:
        await update.message.reply_text("No killers found!")
        return

    text = "☠️ <b>Top Killers</b>\n━━━━━━━━━━━━━━━\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(users):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} <b>{u['username']}</b> — {u['kills']} kills\n"

    await update.message.reply_text(text, parse_mode="HTML")


async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from models.user import get_all_users
    group_id = update.effective_chat.id
    users = await get_all_users(group_id)
    if not users:
        await update.message.reply_text("No users found!")
        return

    sorted_users = sorted(users, key=lambda x: (x["kills"], x["balance"]), reverse=True)[:10]
    text = "🏆 <b>Leaderboard</b>\n━━━━━━━━━━━━━━━\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(sorted_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} <b>{u['username']}</b> | ⚔️ {u['kills']} kills | 💰 {format_coins(u['balance'])}\n"

    await update.message.reply_text(text, parse_mode="HTML")
