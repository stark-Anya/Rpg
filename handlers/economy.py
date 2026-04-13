import time
import random
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user, get_top_rich
from utils.helpers import (
    check_economy, time_remaining, format_time,
    format_coins, get_target_user, is_owner
)
from config import *


async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    group_id = update.effective_chat.id

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        data = await get_user(target.id, group_id, target.first_name)
        name = target.first_name
    else:
        user = update.effective_user
        data = await get_user(user.id, group_id, user.first_name)
        name = user.first_name

    text = (
        f"👛 <b>Wallet — {name}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Balance: {format_coins(data['balance'])}\n"
        f"🏦 Bank: {format_coins(data['bank_balance'])}\n"
        f"💸 Loan: {format_coins(data['loan'])}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚔️ Kills: {data['kills']}  💀 Deaths: {data['deaths']}\n"
        f"❤️ HP: {data['hp']}/{data['max_hp']}\n"
        f"📊 Status: {'🟢 Alive' if data['status'] == 'alive' else '💀 Dead'}"
    )
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
            f"⏳ Daily already claimed! Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    new_balance = data["balance"] + DAILY_REWARD
    await update_user(user.id, group_id, {
        "balance": new_balance,
        "last_daily": time.time()
    })
    await update.message.reply_text(
        f"✅ Daily reward claimed!\n"
        f"💰 +{format_coins(DAILY_REWARD)}\n"
        f"👛 New balance: {format_coins(new_balance)}",
        parse_mode="HTML"
    )


async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    remaining = time_remaining(data["last_claim"], CLAIM_COOLDOWN)
    if remaining > 0:
        await update.message.reply_text(
            f"⏳ Already claimed! Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    reward = random.randint(CLAIM_MIN, CLAIM_MAX)
    new_balance = data["balance"] + reward
    await update_user(user.id, group_id, {
        "balance": new_balance,
        "last_claim": time.time()
    })
    await update.message.reply_text(
        f"🎁 Group bonus claimed!\n"
        f"💰 +{format_coins(reward)}\n"
        f"👛 New balance: {format_coins(new_balance)}",
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
            f"⛏️ Mines are recharging! Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    reward = random.randint(MINE_MIN, MINE_MAX)
    new_balance = data["balance"] + reward
    await update_user(user.id, group_id, {
        "balance": new_balance,
        "last_mine": time.time()
    })
    await update.message.reply_text(
        f"⛏️ You went mining and found coins!\n"
        f"💰 +{format_coins(reward)}\n"
        f"👛 New balance: {format_coins(new_balance)}",
        parse_mode="HTML"
    )


async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    remaining = time_remaining(data["last_farm"], FARM_COOLDOWN)
    if remaining > 0:
        await update.message.reply_text(
            f"🌾 Crops are growing! Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    reward = random.randint(FARM_MIN, FARM_MAX)
    new_balance = data["balance"] + reward
    await update_user(user.id, group_id, {
        "balance": new_balance,
        "last_farm": time.time()
    })
    await update.message.reply_text(
        f"🌾 You harvested your farm!\n"
        f"💰 +{format_coins(reward)}\n"
        f"👛 New balance: {format_coins(new_balance)}",
        parse_mode="HTML"
    )


async def crime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    remaining = time_remaining(data["last_crime"], MINE_COOLDOWN)
    if remaining > 0:
        await update.message.reply_text(
            f"🚔 Lay low for now! Come back in <b>{format_time(remaining)}</b>.",
            parse_mode="HTML"
        )
        return

    success = random.random() < CRIME_SUCCESS_CHANCE
    await update_user(user.id, group_id, {"last_crime": time.time()})

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
        await update.message.reply_text(
            f"😈 Crime successful! You {random.choice(crimes)}\n"
            f"💰 +{format_coins(reward)}\n"
            f"👛 New balance: {format_coins(new_balance)}",
            parse_mode="HTML"
        )
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
        await update.message.reply_text(
            f"😬 Crime failed! You {random.choice(busted)}\n"
            f"💸 -{format_coins(penalty)}\n"
            f"👛 New balance: {format_coins(new_balance)}",
            parse_mode="HTML"
        )


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id

    # Parse args: /give [amt] [user] or reply + /give [amt]
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
            "❌ Usage: Reply to user + <code>/give [amount]</code>\n"
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
            f"❌ Insufficient balance!\n"
            f"You need {format_coins(total_deduct)} (includes 10% tax: {format_coins(tax)})",
            parse_mode="HTML"
        )
        return

    receiver = await get_user(target_id, group_id, target_name)
    await update_user(user.id, group_id, {"balance": sender["balance"] - total_deduct})
    await update_user(target_id, group_id, {"balance": receiver["balance"] + amount})

    await update.message.reply_text(
        f"✅ Transfer successful!\n"
        f"💸 Sent: {format_coins(amount)} to <b>{target_name}</b>\n"
        f"🏛️ Tax (10%): {format_coins(tax)}\n"
        f"👛 Your balance: {format_coins(sender['balance'] - total_deduct)}",
        parse_mode="HTML"
    )


async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner only — give any amount to any user."""
    user = update.effective_user
    if not is_owner(user.id):
        await update.message.reply_text("❌ This command is for the owner only.")
        return

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
            "❌ Usage: Reply + <code>/transfer [amount]</code>\n"
            "Or: <code>/transfer [user_id] [amount]</code>",
            parse_mode="HTML"
        )
        return

    receiver = await get_user(target_id, group_id, target_name)
    new_bal = receiver["balance"] + amount
    await update_user(target_id, group_id, {"balance": new_bal})

    await update.message.reply_text(
        f"✅ Owner transfer done!\n"
        f"💰 +{format_coins(amount)} → <b>{target_name}</b>\n"
        f"👛 Their balance: {format_coins(new_bal)}",
        parse_mode="HTML"
    )


async def toprich(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    users = await get_top_rich(group_id)
    if not users:
        await update.message.reply_text("No users found!")
        return

    text = "💰 <b>Top Richest Users</b>\n━━━━━━━━━━━━━━━\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(users):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} <b>{u['username']}</b> — {format_coins(u['balance'])}\n"

    await update.message.reply_text(text, parse_mode="HTML")
