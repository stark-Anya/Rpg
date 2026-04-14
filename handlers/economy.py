import time, random
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user, get_top_rich, update_user_global
from utils.helpers import fmt, check_economy, time_remaining, format_time, get_target_user, is_owner, send_with_image
from config import *


async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id if update.effective_chat.type != "private" else 0

    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        data = await get_user(t.id, group_id, t.first_name)
        name = t.first_name
    else:
        u = update.effective_user
        data = await get_user(u.id, group_id, u.first_name)
        name = u.first_name

    from utils.helpers import get_best_weapon, is_weapon_valid
    inv = data.get("inventory", {})

    best_w = "None"
    for key, wdata in inv.items():
        if key in WEAPONS and wdata.get("qty", 0) > 0 and is_weapon_valid(wdata):
            best_w = WEAPONS[key]["name"]
            break

    prot_str = "None"
    if data.get("protected_until") and time.time() < data["protected_until"]:
        rem = int(data["protected_until"] - time.time())
        prot_str = f"Active ({rem//3600}h {(rem%3600)//60}m)"

    flex_owned = [FLEX_ITEMS[k]["name"] for k, v in inv.items() if k in FLEX_ITEMS and v.get("qty", 0) > 0]
    flex_str   = ", ".join(flex_owned[:3]) if flex_owned else "Empty"

    status = "🟢 Alive" if data["status"] == "alive" else "💀 Dead"

    await update.message.reply_text(
        f"""👤 <b>{name}</b>  |  {status}
◈ ━━━━━━ ⸙ ━━━━━━ ◈
👛 <b>Wallet:</b> {fmt(data['balance'])}
🏦 <b>Bank:</b> {fmt(data['bank_balance'])}
⚔️ <b>Kills:</b> {data['kills']}
◈ ━━━━━━ ⸙ ━━━━━━ ◈
🗡️ <b>Weapon:</b> {best_w}
🛡️ <b>Shield:</b> {prot_str}
◈ ━━━━━━ ⸙ ━━━━━━ ◈
💎 <b>Flex:</b> {flex_str}""",
        parse_mode="HTML"
    )


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    rem = time_remaining(data["last_daily"], DAILY_COOLDOWN)
    if rem > 0:
        await update.message.reply_text(f"⏳ Daily cooldown: <b>{format_time(rem)}</b>", parse_mode="HTML")
        return

    nb = data["balance"] + DAILY_REWARD
    await update_user(u.id, gid, {"balance": nb, "last_daily": time.time()})
    await send_with_image(update, gid, IMG_DAILY,
        f"""🎁 <b>Daily Claimed!</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
💸 +{fmt(DAILY_REWARD)}
👛 Wallet: {fmt(nb)}
◈ ━━━━━━ ⸙ ━━━━━━ ◈""")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    rem = time_remaining(data["last_claim"], CLAIM_COOLDOWN)
    if rem > 0:
        await update.message.reply_text(f"⏳ Claim cooldown: <b>{format_time(rem)}</b>", parse_mode="HTML")
        return

    reward = random.randint(CLAIM_MIN, CLAIM_MAX)
    nb = data["balance"] + reward
    await update_user(u.id, gid, {"balance": nb, "last_claim": time.time()})
    await update.message.reply_text(
        f"""🎰 <b>Group Bonus!</b>
💸 +{fmt(reward)}
👛 Wallet: {fmt(nb)}""",
        parse_mode="HTML"
    )


async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    rem = time_remaining(data["last_mine"], MINE_COOLDOWN)
    if rem > 0:
        await update.message.reply_text(f"⛏️ Mine cooldown: <b>{format_time(rem)}</b>", parse_mode="HTML")
        return

    r = random.randint(MINE_MIN, MINE_MAX)
    nb = data["balance"] + r
    await update_user(u.id, gid, {"balance": nb, "last_mine": time.time()})
    await send_with_image(update, gid, IMG_MINE,
        f"""⛏️ <b>Mining Done!</b>
💸 +{fmt(r)}
👛 Wallet: {fmt(nb)}""")


async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    rem = time_remaining(data["last_farm"], FARM_COOLDOWN)
    if rem > 0:
        await update.message.reply_text(f"🌾 Farm cooldown: <b>{format_time(rem)}</b>", parse_mode="HTML")
        return

    r = random.randint(FARM_MIN, FARM_MAX)
    nb = data["balance"] + r
    await update_user(u.id, gid, {"balance": nb, "last_farm": time.time()})
    await send_with_image(update, gid, IMG_FARM,
        f"""🌾 <b>Harvest Done!</b>
💸 +{fmt(r)}
👛 Wallet: {fmt(nb)}""")


async def crime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    # Fixed: using CRIME_COOLDOWN instead of MINE_COOLDOWN
    rem = time_remaining(data["last_crime"], CRIME_COOLDOWN)
    if rem > 0:
        await update.message.reply_text(f"🚔 Lay low! <b>{format_time(rem)}</b>", parse_mode="HTML")
        return

    await update_user(u.id, gid, {"last_crime": time.time()})

    if random.random() < CRIME_SUCCESS_CHANCE:
        r = random.randint(CRIME_MIN_REWARD, CRIME_MAX_REWARD)
        nb = data["balance"] + r
        await update_user(u.id, gid, {"balance": nb})
        caption = f"""😈 <b>Crime Successful!</b>
💸 +{fmt(r)}
👛 Wallet: {fmt(nb)}"""
    else:
        p = random.randint(CRIME_MIN_PENALTY, CRIME_MAX_PENALTY)
        nb = max(0, data["balance"] - p)
        await update_user(u.id, gid, {"balance": nb})
        caption = f"""🚔 <b>Busted!</b>
💸 -{fmt(p)}
👛 Wallet: {fmt(nb)}"""

    await send_with_image(update, gid, IMG_CRIME, caption)


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    tid, tname = await get_target_user(update, context)

    try:
        amount = int(context.args[0]) if update.message.reply_to_message else int(context.args[1]) if len(context.args) >= 2 else None
    except (IndexError, ValueError, TypeError):
        amount = None

    if not tid or not amount:
        await update.message.reply_text("❌ Reply to user + <code>/give [amount]</code>", parse_mode="HTML")
        return
    if tid == u.id:
        await update.message.reply_text("❌ Can't send to yourself!")
        return
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    sender = await get_user(u.id, gid, u.first_name)
    tax    = int(amount * GIVE_TAX)
    total  = amount + tax

    if sender["balance"] < total:
        await update.message.reply_text(
            f"❌ Need {fmt(total)} (tax: {fmt(tax)})\nWallet: {fmt(sender['balance'])}",
            parse_mode="HTML"
        )
        return

    receiver = await get_user(tid, gid, tname)
    await update_user(u.id, gid, {"balance": sender["balance"] - total})
    await update_user(tid, gid, {"balance": receiver["balance"] + amount})

    await update.message.reply_text(
        f"""💸 <b>Sent!</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
➡️ {u.first_name} → {tname}
💰 Amount: {fmt(amount)}
🏦 Tax: {fmt(tax)} (5%)""",
        parse_mode="HTML"
    )


async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not is_owner(u.id):
        await update.message.reply_text("❌ Owner only!")
        return

    gid = update.effective_chat.id
    tid, tname = await get_target_user(update, context)

    try:
        amount = int(context.args[0]) if update.message.reply_to_message else int(context.args[1]) if len(context.args) >= 2 else None
    except (IndexError, ValueError, TypeError):
        amount = None

    if not tid or not amount:
        await update.message.reply_text("❌ Reply to user + <code>/transfer [amount]</code>", parse_mode="HTML")
        return

    receiver = await get_user(tid, gid, tname)
    nb = receiver["balance"] + amount
    await update_user_global(tid, {"balance": nb})
    await update.message.reply_text(f"✅ Transferred {fmt(amount)} to <b>{tname}</b>", parse_mode="HTML")

    try:
        await context.bot.send_message(
            chat_id=tid,
            text=f"""🎁 <b>Owner Gift!</b>
💸 +{fmt(amount)}
👛 Wallet: {fmt(nb)}""",
            parse_mode="HTML"
        )
    except Exception:
        pass


async def toprich(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    users = await get_top_rich(gid)
    if not users:
        await update.message.reply_text("No users yet!")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = "\n".join(
        f"{medals[i] if i < 3 else f'{i+1}.'} <b>{u['username']}</b> — {fmt(u['balance'])}"
        for i, u in enumerate(users)
    )
    await update.message.reply_text(
        f"💰 <b>Top Richest</b>\n◈ ━━━━━━ ⸙ ━━━━━━ ◈\n{lines}",
        parse_mode="HTML"
    )
