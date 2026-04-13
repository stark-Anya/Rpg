import time
import random
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user, get_top_rich
from utils.helpers import (
    check_economy, time_remaining, format_time,
    format_coins, get_target_user, is_owner, send_with_image
)
from config import *


async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        uid, name = target.id, target.first_name
    else:
        user = update.effective_user
        uid, name = user.id, user.first_name

    # Use group_id for groups, uid for private (but store under group_id=uid for private)
    lookup_group = group_id if chat_type in ["group", "supergroup"] else uid
    data = await get_user(uid, lookup_group, name)

    text = f"""👛 <b>Wallet — {name}</b>
━━━━━━━━━━━━━━━
💰 Balance: {format_coins(data['balance'])}
🏦 Bank: {format_coins(data['bank_balance'])}
💸 Loan: {format_coins(data['loan'])}
━━━━━━━━━━━━━━━
⚔️ Kills: {data['kills']}  💀 Deaths: {data['deaths']}
❤️ HP: {data['hp']}/{data['max_hp']}
📊 Status: {'🟢 Alive' if data['status'] == 'alive' else '💀 Dead'}"""

    await update.message.reply_text(text, parse_mode="HTML")


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    remaining = time_remaining(data["last_daily"], DAILY_COOLDOWN)
    if remaining > 0:
        await update.message.reply_text(
            f"⏳ Daily already claimed!\n🕐 Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    new_balance = data["balance"] + DAILY_REWARD
    await update_user(user.id, group_id, {"balance": new_balance, "last_daily": time.time()})

    text = f"""🎁 <b>Daily Reward Claimed!</b>
━━━━━━━━━━━━━━━
💰 +{format_coins(DAILY_REWARD)}
👛 New Balance: {format_coins(new_balance)}"""

    await send_with_image(context.bot, update.effective_chat.id, IMG_DAILY, text)


async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    remaining = time_remaining(data["last_claim"], CLAIM_COOLDOWN)
    if remaining > 0:
        await update.message.reply_text(
            f"⏳ Already claimed!\n🕐 Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    reward = random.randint(CLAIM_MIN, CLAIM_MAX)
    new_balance = data["balance"] + reward
    await update_user(user.id, group_id, {"balance": new_balance, "last_claim": time.time()})

    await update.message.reply_text(
        f"""🎰 <b>Group Bonus Claimed!</b>
━━━━━━━━━━━━━━━
💰 +{format_coins(reward)}
👛 New Balance: {format_coins(new_balance)}""",
        parse_mode="HTML"
    )


async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    remaining = time_remaining(data["last_mine"], MINE_COOLDOWN)
    if remaining > 0:
        await update.message.reply_text(
            f"⛏️ Mines recharging!\n🕐 Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    reward = random.randint(MINE_MIN, MINE_MAX)
    new_balance = data["balance"] + reward
    await update_user(user.id, group_id, {"balance": new_balance, "last_mine": time.time()})

    text = f"""⛏️ <b>Mining Complete!</b>
━━━━━━━━━━━━━━━
💰 +{format_coins(reward)}
👛 New Balance: {format_coins(new_balance)}"""

    await send_with_image(context.bot, update.effective_chat.id, IMG_MINE, text)


async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    remaining = time_remaining(data["last_farm"], FARM_COOLDOWN)
    if remaining > 0:
        await update.message.reply_text(
            f"🌾 Crops still growing!\n🕐 Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    reward = random.randint(FARM_MIN, FARM_MAX)
    new_balance = data["balance"] + reward
    await update_user(user.id, group_id, {"balance": new_balance, "last_farm": time.time()})

    text = f"""🌾 <b>Harvest Complete!</b>
━━━━━━━━━━━━━━━
💰 +{format_coins(reward)}
👛 New Balance: {format_coins(new_balance)}"""

    await send_with_image(context.bot, update.effective_chat.id, IMG_FARM, text)


async def crime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    remaining = time_remaining(data["last_crime"], MINE_COOLDOWN)
    if remaining > 0:
        await update.message.reply_text(
            f"🚔 Lay low!\n🕐 Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    await update_user(user.id, group_id, {"last_crime": time.time()})
    success = random.random() < CRIME_SUCCESS_CHANCE

    if success:
        reward = random.randint(CRIME_MIN_REWARD, CRIME_MAX_REWARD)
        new_balance = data["balance"] + reward
        await update_user(user.id, group_id, {"balance": new_balance})
        crimes = [
            "robbed a jewelry store 💍",
            "hacked a bank account 💻",
            "pickpocketed a rich man 🎩",
            "smuggled rare goods 📦",
            "scammed a merchant 🧾"
        ]
        text = f"""😈 <b>Crime Successful!</b>
━━━━━━━━━━━━━━━
You {random.choice(crimes)}
💰 +{format_coins(reward)}
👛 New Balance: {format_coins(new_balance)}"""
    else:
        penalty = random.randint(CRIME_MIN_PENALTY, CRIME_MAX_PENALTY)
        new_balance = max(0, data["balance"] - penalty)
        await update_user(user.id, group_id, {"balance": new_balance})
        busted = [
            "got caught by the police 🚔",
            "dropped the loot while running 💨",
            "was betrayed by your partner 🤝",
            "tripped on the way out 😂",
            "security cameras caught you 📷"
        ]
        text = f"""😬 <b>Crime Failed!</b>
━━━━━━━━━━━━━━━
You {random.choice(busted)}
💸 -{format_coins(penalty)}
👛 New Balance: {format_coins(new_balance)}"""

    await send_with_image(context.bot, update.effective_chat.id, IMG_CRIME, text)


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    try:
        amount = int(context.args[0]) if update.message.reply_to_message else int(context.args[1])
    except (IndexError, ValueError, TypeError):
        amount = None

    if not target_id or not amount:
        await update.message.reply_text(
            "❌ <b>Usage:</b>\nReply + <code>/give [amount]</code>\n"
            "Or: <code>/give [user_id] [amount]</code>",
            parse_mode="HTML"
        )
        return
    if target_id == user.id:
        await update.message.reply_text("❌ You can't give coins to yourself!")
        return
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    sender = await get_user(user.id, group_id, user.first_name)
    tax = int(amount * GIVE_TAX)
    total_deduct = amount + tax

    if sender["balance"] < total_deduct:
        await update.message.reply_text(
            f"""❌ <b>Insufficient balance!</b>
Need: {format_coins(total_deduct)} (includes 10% tax: {format_coins(tax)})
You have: {format_coins(sender['balance'])}""",
            parse_mode="HTML"
        )
        return

    receiver = await get_user(target_id, group_id, target_name)
    await update_user(user.id, group_id, {"balance": sender["balance"] - total_deduct})
    await update_user(target_id, group_id, {"balance": receiver["balance"] + amount})

    await update.message.reply_text(
        f"""✅ <b>Transfer Successful!</b>
━━━━━━━━━━━━━━━
💸 Sent: {format_coins(amount)} → <b>{target_name}</b>
🏛️ Tax (10%): {format_coins(tax)}
👛 Your Balance: {format_coins(sender['balance'] - total_deduct)}""",
        parse_mode="HTML"
    )


async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_owner(user.id):
        await update.message.reply_text("❌ Owner only command!")
        return

    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    try:
        amount = int(context.args[0]) if update.message.reply_to_message else int(context.args[1])
    except (IndexError, ValueError, TypeError):
        amount = None

    if not target_id or not amount:
        await update.message.reply_text(
            "❌ <b>Usage:</b>\nReply + <code>/transfer [amount]</code>\n"
            "Or: <code>/transfer [user_id] [amount]</code>",
            parse_mode="HTML"
        )
        return

    # Get receiver from any group they exist in — search by user_id
    from database import users_col
    receiver = await users_col.find_one({"user_id": target_id})
    if not receiver:
        # Create fresh user record
        receiver = await get_user(target_id, group_id, target_name)

    r_group = receiver.get("group_id", group_id)
    new_bal = receiver["balance"] + amount
    await update_user(target_id, r_group, {"balance": new_bal})

    # Notify receiver in private
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"""💰 <b>You received a transfer!</b>
━━━━━━━━━━━━━━━
👑 Owner sent you: {format_coins(amount)}
💰 New Balance: {format_coins(new_bal)}""",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"""✅ <b>Owner Transfer Done!</b>
━━━━━━━━━━━━━━━
💰 +{format_coins(amount)} → <b>{target_name}</b>
👛 Their Balance: {format_coins(new_bal)}""",
        parse_mode="HTML"
    )


async def toprich(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    users = await get_top_rich(group_id)
    if not users:
        await update.message.reply_text("No users found!")
        return
    text = "💰 <b>Top Richest Players</b>\n━━━━━━━━━━━━━━━\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(users):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} <b>{u['username']}</b> — {format_coins(u['balance'])}\n"
    await update.message.reply_text(text, parse_mode="HTML")
