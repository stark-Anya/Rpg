#===================================================#
#=============== OWNER : MISTER STARK ==============#
#===================================================#
#============== CREDIT NA LENA BACHHO 🤣 ===========#
#===================================================

import time, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user import get_user, update_user, get_top_rich, update_user_global
from utils.helpers import fmt, check_economy, time_remaining, format_time, get_target_user, is_owner, send_with_image
from config import *


async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id if update.effective_chat.type != "private" else 0

    if update.message.reply_to_message:
        t    = update.message.reply_to_message.from_user
        data = await get_user(t.id, group_id, t.first_name)
        name = t.first_name
    else:
        u    = update.effective_user
        data = await get_user(u.id, group_id, u.first_name)
        name = u.first_name

    from utils.helpers import get_best_weapon, is_weapon_valid
    inv = data.get("inventory", {})

    # Best weapon
    best_w = "None"
    for key, wdata in inv.items():
        if key in WEAPONS and wdata.get("qty", 0) > 0 and is_weapon_valid(wdata):
            best_w = WEAPONS[key]["name"]
            break

    status = "🟢 Alive" if data["status"] == "alive" else "💀 Dead"

    # Flex items as inline buttons
    flex_keys = [k for k, v in inv.items() if k in FLEX_ITEMS and v.get("qty", 0) > 0]

    text = f"""👤 User: <b>{name}</b>
👛 Balance: <b>{fmt(data['balance'])}</b>
❤️ Status: <b>{status}</b>
⚔️ Kills: <b>{data['kills']}</b>
━━━━━━━━━━━━━━━
🎒 <b>𝐀𝐜𝐭𝐢𝐯𝐞 𝐆𝐞𝐚𝐫:</b>
🗡️ Weapon: {best_w}
━━━━━━━━━━━━━━━
💎 <b>𝐅𝐥𝐞𝐱 𝐂𝐨𝐥𝐥𝐞𝐜𝐭𝐢𝐨𝐧:</b>"""

    if flex_keys:
        text += "\n<i>(Click buttons to view details)</i>"
    else:
        text += "\nEmpty..."

    # Build flex inline buttons (2 per row)
    kb = None
    if flex_keys:
        rows = []
        for i in range(0, len(flex_keys), 2):
            row = []
            for k in flex_keys[i:i+2]:
                item = FLEX_ITEMS[k]
                row.append(InlineKeyboardButton(
                    f"{item['emoji']} {item['name'].split(' ',1)[1]}",
                    callback_data=f"bal_flex_{k}"
                ))
            rows.append(row)
        kb = InlineKeyboardMarkup(rows)

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def bal_flex_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Popup for flex item details from /bal."""
    query    = update.callback_query
    user     = update.effective_user
    group_id = update.effective_chat.id
    key      = query.data[len("bal_flex_"):]
    item     = FLEX_ITEMS.get(key)

    if not item:
        await query.answer("❌ Item not found!", show_alert=True)
        return

    udata = await get_user(user.id, group_id, user.first_name)
    qty   = udata.get("inventory", {}).get(key, {}).get("qty", 0)

    await query.answer(
        f"💎 Flex Item: {item['name']}\n"
        f"💰 Value: {fmt(item['price'])}\n"
        f"🌟 Rarity: {get_rarity(item['price'])}\n"
        f"🛡️ Status: Safe (unless you die)\n"
        f"🎒 Owned: {qty}x",
        show_alert=True
    )


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u   = update.effective_user
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
━━━━━━━━━━━━━━━
💸 +{fmt(DAILY_REWARD)}
👛 Wallet: {fmt(nb)}""")


async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u   = update.effective_user
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
👛 Wallet: {fmt(nb)}""", parse_mode="HTML")


async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u   = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    rem = time_remaining(data["last_mine"], MINE_COOLDOWN)
    if rem > 0:
        await update.message.reply_text(f"⛏️ Mine cooldown: <b>{format_time(rem)}</b>", parse_mode="HTML")
        return

    r  = random.randint(MINE_MIN, MINE_MAX)
    nb = data["balance"] + r
    await update_user(u.id, gid, {"balance": nb, "last_mine": time.time()})
    await send_with_image(update, gid, IMG_MINE,
        f"""⛏️ <b>Mining Done!</b>
💸 +{fmt(r)}
👛 Wallet: {fmt(nb)}""")


async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u   = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    rem = time_remaining(data["last_farm"], FARM_COOLDOWN)
    if rem > 0:
        await update.message.reply_text(f"🌾 Farm cooldown: <b>{format_time(rem)}</b>", parse_mode="HTML")
        return

    r  = random.randint(FARM_MIN, FARM_MAX)
    nb = data["balance"] + r
    await update_user(u.id, gid, {"balance": nb, "last_farm": time.time()})
    await send_with_image(update, gid, IMG_FARM,
        f"""🌾 <b>Harvest Done!</b>
💸 +{fmt(r)}
👛 Wallet: {fmt(nb)}""")


async def crime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u   = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    rem = time_remaining(data["last_crime"], CRIME_COOLDOWN)
    if rem > 0:
        await update.message.reply_text(f"🚔 Lay low! <b>{format_time(rem)}</b>", parse_mode="HTML")
        return

    await update_user(u.id, gid, {"last_crime": time.time()})

    if random.random() < CRIME_SUCCESS_CHANCE:
        r  = random.randint(CRIME_MIN_REWARD, CRIME_MAX_REWARD)
        nb = data["balance"] + r
        await update_user(u.id, gid, {"balance": nb})
        caption = f"""😈 <b>Crime Successful!</b>
💸 +{fmt(r)}
👛 Wallet: {fmt(nb)}"""
    else:
        p  = random.randint(CRIME_MIN_PENALTY, CRIME_MAX_PENALTY)
        nb = max(0, data["balance"] - p)
        await update_user(u.id, gid, {"balance": nb})
        caption = f"""🚔 <b>Busted!</b>
💸 -{fmt(p)}
👛 Wallet: {fmt(nb)}"""

    await send_with_image(update, gid, IMG_CRIME, caption)


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u   = update.effective_user
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
━━━━━━━━━━━━━━━
➡️ {u.first_name} → {tname}
💰 Amount: {fmt(amount)}
🏦 Tax: {fmt(tax)} (5%)""", parse_mode="HTML")


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
👛 Wallet: {fmt(nb)}""", parse_mode="HTML")
    except Exception:
        pass


async def toprich(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    users = await get_top_rich(gid)
    if not users:
        await update.message.reply_text("No users yet!")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines  = "\n".join(
        f"{medals[i] if i < 3 else f'{i+1}.'} <b>{u['username']}</b> — {fmt(u['balance'])}"
        for i, u in enumerate(users)
    )
    await update.message.reply_text(
        f"💰 <b>Top Richest</b>\n━━━━━━━━━━━━━━━\n{lines}",
        parse_mode="HTML"
    )


async def deduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner/Sudo: /deduct {userid} {amount}"""
    u = update.effective_user
    from utils.helpers import is_sudo_or_owner
    if not await is_sudo_or_owner(u.id):
        await update.message.reply_text("❌ Owner/Sudo only!")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: <code>/deduct {userid} {amount}</code>", parse_mode="HTML")
        return

    try:
        tid    = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID or amount!")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    gid   = update.effective_chat.id
    tdata = await get_user(tid, gid)
    tname = tdata.get("username", str(tid))

    total_assets = tdata["balance"] + tdata["bank_balance"]
    if total_assets < amount:
        await update.message.reply_text(
            f"❌ <b>{tname}</b> doesn't have enough!\n"
            f"💰 Wallet: {fmt(tdata['balance'])}\n"
            f"🏦 Bank: {fmt(tdata['bank_balance'])}\n"
            f"📊 Total: {fmt(total_assets)}",
            parse_mode="HTML"
        )
        return

    wallet_deduct = min(amount, tdata["balance"])
    bank_deduct   = amount - wallet_deduct
    new_wallet    = tdata["balance"] - wallet_deduct
    new_bank      = tdata["bank_balance"] - bank_deduct

    await update_user(tid, gid, {"balance": new_wallet, "bank_balance": new_bank})

    bank_line = f"\n🏦 Bank deducted: {fmt(bank_deduct)}" if bank_deduct > 0 else ""
    await update.message.reply_text(
        f"""🔻 <b>Deduction Done!</b>
━━━━━━━━━━━━━━━
👤 User: <b>{tname}</b> (<code>{tid}</code>)
💸 Total: {fmt(amount)}
💰 Wallet deducted: {fmt(wallet_deduct)}{bank_line}
━━━━━━━━━━━━━━━
👛 New Wallet: {fmt(new_wallet)}
🏦 New Bank: {fmt(new_bank)}""",
        parse_mode="HTML"
    )

    try:
        await context.bot.send_message(
            chat_id=tid,
            text=f"""⚠️ <b>Balance Deducted!</b>
━━━━━━━━━━━━━━━
💸 -{fmt(amount)} deducted by admin.
👛 Wallet: {fmt(new_wallet)}
🏦 Bank: {fmt(new_bank)}""",
            parse_mode="HTML"
        )
    except Exception:
        pass
