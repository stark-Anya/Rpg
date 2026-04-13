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
        await update.message.reply_text("💀 You are dead! Use /revive to come back to life.")
        return

    victim_data = await get_user(target_id, group_id, target_name)
    if victim_data["status"] == "dead":
        await update.message.reply_text(f"💀 <b>{target_name}</b> is already dead!", parse_mode="HTML")
        return

    if is_protected(victim_data):
        await update.message.reply_text(f"🛡️ <b>{target_name}</b> is protected!", parse_mode="HTML")
        return

    loot = int(victim_data["balance"] * KILL_LOOT_PERCENT)

    from database import db
    wanted_col = db["wanted"]
    today = int(time.time() // 86400)
    wanted_rec = await wanted_col.find_one({"user_id": target_id, "group_id": group_id, "day": today, "kills": {"$gte": 10}})
    bounty = 500 if wanted_rec else 0
    if wanted_rec:
        await wanted_col.delete_one({"_id": wanted_rec["_id"]})

    total_loot = loot + bounty
    new_killer_balance = killer_data["balance"] + total_loot

    rec = await wanted_col.find_one({"user_id": killer.id, "group_id": group_id, "day": today})
    if rec:
        new_kills = rec["kills"] + 1
        await wanted_col.update_one({"_id": rec["_id"]}, {"$set": {"kills": new_kills}})
    else:
        new_kills = 1
        await wanted_col.insert_one({"user_id": killer.id, "group_id": group_id, "day": today, "username": killer.first_name, "kills": 1})

    await update_user(killer.id, group_id, {"balance": new_killer_balance, "kills": killer_data["kills"] + 1})
    await update_user(target_id, group_id, {"balance": 0, "status": "dead", "deaths": victim_data["deaths"] + 1})

    text = (
        f"⚔️ <b>{killer.first_name}</b> killed <b>{target_name}</b>!\n"
        f"💀 {target_name} is now dead and lost everything.\n"
        f"💰 Looted: {format_coins(loot)}\n"
    )
    if bounty:
        text += f"🚨 Bounty collected: {format_coins(bounty)}\n"
    text += f"👛 {killer.first_name}'s balance: {format_coins(new_killer_balance)}"
    if new_kills == 10:
        text += f"\n\n🚨 <b>{killer.first_name} is now WANTED!</b>\n💰 Bounty: 500 coins on their head!"

    await update.message.reply_text(text, parse_mode="HTML")


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
        await update.message.reply_text("❌ Usage: Reply + <code>/rob [amount]</code> or <code>/rob [user_id] [amount]</code>", parse_mode="HTML")
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
        await update.message.reply_text(f"🛡️ <b>{target_name}</b> is protected!", parse_mode="HTML")
        return
    if victim_data["balance"] < amount:
        await update.message.reply_text(f"❌ {target_name} only has {format_coins(victim_data['balance'])}!", parse_mode="HTML")
        return

    await update_user(robber.id, group_id, {"balance": robber_data["balance"] + amount})
    await update_user(target_id, group_id, {"balance": victim_data["balance"] - amount})

    await update.message.reply_text(
        f"🦹 <b>{robber.first_name}</b> robbed <b>{target_name}</b>!\n"
        f"💰 Stolen: {format_coins(amount)}\n"
        f"👛 Your balance: {format_coins(robber_data['balance'] + amount)}",
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
        await update.message.reply_text(f"🛡️ Already protected! Expires in: {remaining//3600}h {(remaining%3600)//60}m")
        return
    if data["balance"] < PROTECT_MIN_BALANCE:
        await update.message.reply_text(f"❌ Need {format_coins(PROTECT_MIN_BALANCE)} minimum.\nYou have: {format_coins(data['balance'])}", parse_mode="HTML")
        return

    await update_user(user.id, group_id, {"balance": data["balance"] - PROTECT_COST, "protected_until": time.time() + PROTECT_DURATION})
    await update.message.reply_text(
        f"🛡️ Protection active for 24h!\n💸 Cost: {format_coins(PROTECT_COST)}\n👛 Balance: {format_coins(data['balance'] - PROTECT_COST)}",
        parse_mode="HTML"
    )


async def revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if data["status"] == "alive":
        await update.message.reply_text("✅ You are already alive!")
        return

    await update_user(user.id, group_id, {"status": "alive", "hp": data["max_hp"]})
    await update.message.reply_text(f"💫 <b>{user.first_name}</b> revived! ❤️ HP: {data['max_hp']}", parse_mode="HTML")


async def heal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if data["status"] == "dead":
        await update.message.reply_text("💀 Dead! Use /revive first.")
        return
    if data["hp"] >= data["max_hp"]:
        await update.message.reply_text(f"❤️ Already at full HP ({data['max_hp']})!")
        return
    if data["balance"] < HEAL_COST:
        await update.message.reply_text(f"❌ Need {format_coins(HEAL_COST)} to heal.", parse_mode="HTML")
        return

    heal_amount = min(50, data["max_hp"] - data["hp"])
    await update_user(user.id, group_id, {"hp": data["hp"] + heal_amount, "balance": data["balance"] - HEAL_COST})
    await update.message.reply_text(
        f"💊 Healed +{heal_amount} HP!\n❤️ {data['hp']} → {data['hp']+heal_amount}/{data['max_hp']}\n👛 Balance: {format_coins(data['balance']-HEAL_COST)}",
        parse_mode="HTML"
    )


async def hp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        data = await get_user(target.id, group_id, target.first_name)
        name = target.first_name
    else:
        user = update.effective_user
        data = await get_user(user.id, group_id, user.first_name)
        name = user.first_name

    shield = " 🛡️" if is_protected(data) else ""
    status = "🟢 Alive" if data["status"] == "alive" else "💀 Dead"
    await update.message.reply_text(
        f"❤️ <b>{name}'s HP</b>{shield}\n{data['hp']}/{data['max_hp']} | {status}",
        parse_mode="HTML"
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    from models.war import get_war_stats
    from config import SHOP_ITEMS

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        data = await get_user(target.id, group_id, target.first_name)
        name = target.first_name
        uid = target.id
    else:
        user = update.effective_user
        data = await get_user(user.id, group_id, user.first_name)
        name = user.first_name
        uid = user.id

    war_stats = await get_war_stats(uid, group_id)
    weapon = SHOP_ITEMS.get(data.get("equipped_weapon"), {}).get("name", "None")
    armor = SHOP_ITEMS.get(data.get("equipped_armor"), {}).get("name", "None")
    net_worth = data["balance"] + data["bank_balance"] - data["loan"]
    streak = data.get("war_streak", 0)
    streak_tag = " 👑" if streak >= 10 else " 🔥🔥" if streak >= 5 else " 🔥" if streak >= 3 else ""
    married = "💍 Married" if data.get("married_to") else "💔 Single"
    status = "🟢 Alive" if data["status"] == "alive" else "💀 Dead"
    shield = " 🛡️" if is_protected(data) else ""

    await update.message.reply_text(
        f"👤 <b>{name}'s Profile</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"❤️ HP: {data['hp']}/{data['max_hp']} | {status}{shield}\n"
        f"💰 Wallet: {format_coins(data['balance'])}\n"
        f"🏦 Bank: {format_coins(data['bank_balance'])}\n"
        f"📊 Net Worth: {format_coins(net_worth)}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚔️ Kills: {data['kills']} | 💀 Deaths: {data['deaths']}\n"
        f"🏆 Wars: {war_stats['wins']}W / {war_stats['losses']}L{streak_tag}\n"
        f"🥇 Biggest Win: {format_coins(war_stats['biggest_win'])}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🗡️ {weapon} | 🛡️ {armor}\n"
        f"{married}",
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
        text += f"{medal} <b>{u['username']}</b> | ⚔️ {u['kills']} | 💰 {format_coins(u['balance'])}\n"
    await update.message.reply_text(text, parse_mode="HTML")
