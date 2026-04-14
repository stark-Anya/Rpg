import time
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user, get_top_killers
from utils.helpers import fmt, check_economy, get_target_user, send_with_image, get_best_weapon, is_weapon_valid
from config import *


def is_protected(data):
    return data.get("protected_until") and time.time() < data["protected_until"]


async def expire_weapons(user_id, group_id, data, context):
    inv = data.get("inventory", {})
    expired = []
    updated = False
    for key, wdata in list(inv.items()):
        if key in WEAPONS and wdata.get("expires_at") and time.time() > wdata["expires_at"]:
            expired.append(WEAPONS[key]["name"])
            del inv[key]
            updated = True
    if updated:
        await update_user(user_id, group_id, {"inventory": inv})
        for name in expired:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⏰ <b>{name}</b> expired and removed from inventory.",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    return inv


async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    killer = update.effective_user
    gid    = update.effective_chat.id
    tid, tname = await get_target_user(update, context)

    if not tid:
        await update.message.reply_text("❌ Reply to a user to kill.")
        return
    if tid == killer.id:
        await update.message.reply_text("❌ Can't kill yourself!")
        return

    kdata = await get_user(killer.id, gid, killer.first_name)
    if kdata["status"] == "dead":
        await update.message.reply_text("💀 You're dead! Use /revive.")
        return

    vdata = await get_user(tid, gid, tname)
    if vdata["status"] == "dead":
        await update.message.reply_text(f"💀 <b>{tname}</b> is already dead!", parse_mode="HTML")
        return
    if is_protected(vdata):
        await update.message.reply_text(f"🛡️ <b>{tname}</b> is protected!", parse_mode="HTML")
        return

    kinv = await expire_weapons(killer.id, gid, kdata, context)

    loot_bonus = 0.0
    best_key, best_item = get_best_weapon(kinv)
    if best_item and is_weapon_valid(kinv.get(best_key, {})):
        loot_bonus = best_item["kill_loot_bonus"]

    wallet_loot = int(vdata["balance"] * KILL_LOOT_PERCENT)
    bank_loot   = int(vdata["bank_balance"] * KILL_BANK_PERCENT)
    base_loot   = wallet_loot + bank_loot
    bonus_loot  = int(base_loot * loot_bonus)
    total_loot  = base_loot + bonus_loot

    vinv  = vdata.get("inventory", {})
    kinv2 = kdata.get("inventory", {})
    for key, val in vinv.items():
        if key in FLEX_ITEMS:
            existing = kinv2.get(key, {"qty": 0, "expires_at": None})
            kinv2[key] = {"qty": existing["qty"] + val.get("qty", 0), "expires_at": None}
        elif key in WEAPONS and is_weapon_valid(val):
            kinv2[key] = val

    from database import db
    wanted_col = db["wanted"]
    today = int(time.time() // 86400)
    wanted_rec = await wanted_col.find_one({
        "user_id": tid, "group_id": gid, "day": today,
        "kills": {"$gte": WANTED_KILLS_THRESHOLD}
    })
    bounty = WANTED_BOUNTY if wanted_rec else 0
    if wanted_rec:
        await wanted_col.delete_one({"_id": wanted_rec["_id"]})

    final_loot = total_loot + bounty
    new_kbal   = kdata["balance"] + final_loot

    rec = await wanted_col.find_one({"user_id": killer.id, "group_id": gid, "day": today})
    if rec:
        nk = rec["kills"] + 1
        await wanted_col.update_one({"_id": rec["_id"]}, {"$set": {"kills": nk}})
    else:
        nk = 1
        await wanted_col.insert_one({
            "user_id": killer.id, "group_id": gid, "day": today,
            "username": killer.first_name, "kills": 1
        })

    await update_user(killer.id, gid, {"balance": new_kbal, "kills": kdata["kills"] + 1, "inventory": kinv2})
    await update_user(tid, gid, {
        "balance": 0,
        "bank_balance": vdata["bank_balance"] - bank_loot,
        "status": "dead",
        "deaths": vdata["deaths"] + 1,
        "inventory": {}
    })

    weapon_line = f"\n🗡️ Weapon Bonus: +{fmt(bonus_loot)} ({int(loot_bonus*100)}%)" if loot_bonus > 0 else ""
    bounty_line = f"\n🚨 Bounty: +{fmt(bounty)}" if bounty else ""
    wanted_line = f"\n\n🚨 <b>{killer.first_name} is now WANTED!</b>" if nk == WANTED_KILLS_THRESHOLD else ""

    caption = f"""⚔️ <b>{killer.first_name}</b> killed <b>{tname}</b>!
◈ ━━━━━━ ⸙ ━━━━━━ ◈
💰 Wallet loot: {fmt(wallet_loot)}
🏦 Bank loot: {fmt(bank_loot)}{weapon_line}{bounty_line}
◈ ━━━━━━ ⸙ ━━━━━━ ◈
💸 Total: {fmt(final_loot)}
👛 Balance: {fmt(new_kbal)}{wanted_line}"""

    await send_with_image(update, gid, IMG_KILL, caption)


async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    tid, tname = await get_target_user(update, context)

    try:
        amount = int(context.args[0]) if update.message.reply_to_message else int(context.args[1]) if len(context.args) >= 2 else None
    except (IndexError, ValueError, TypeError):
        amount = None

    if not tid or not amount:
        await update.message.reply_text("❌ Reply to user + <code>/rob [amount]</code>", parse_mode="HTML")
        return
    if tid == u.id:
        await update.message.reply_text("❌ Can't rob yourself!")
        return

    udata = await get_user(u.id, gid, u.first_name)
    vdata = await get_user(tid, gid, tname)

    if udata["status"] == "dead":
        await update.message.reply_text("💀 Dead! Use /revive.")
        return
    if vdata["status"] == "dead":
        await update.message.reply_text(f"💀 {tname} is dead!")
        return
    if is_protected(vdata):
        await update.message.reply_text(f"🛡️ {tname} is protected!")
        return
    if vdata["balance"] < amount:
        await update.message.reply_text(f"❌ {tname} only has {fmt(vdata['balance'])}!")
        return

    await update_user(u.id, gid, {"balance": udata["balance"] + amount})
    await update_user(tid, gid, {"balance": vdata["balance"] - amount})

    await send_with_image(update, gid, IMG_ROB,
        f"""🦹 <b>{u.first_name}</b> robbed <b>{tname}</b>!
◈ ━━━━━━ ⸙ ━━━━━━ ◈
💰 Stolen: {fmt(amount)}
👛 Your balance: {fmt(udata['balance'] + amount)}""")


async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    if is_protected(data):
        rem = int(data["protected_until"] - time.time())
        await update.message.reply_text(
            f"🛡️ Already protected! <b>{rem//3600}h {(rem%3600)//60}m</b> left.",
            parse_mode="HTML"
        )
        return

    arg = context.args[0].lower() if context.args else "1d"
    costs     = {"1d": PROTECT_COST_1D, "2d": PROTECT_COST_2D, "3d": PROTECT_COST_3D}
    durations = {"1d": 86400, "2d": 172800, "3d": 259200}

    if arg not in costs:
        await update.message.reply_text(
            f"❌ Usage: <code>/protect 1d / 2d / 3d</code>\n"
            f"💰 1d: {fmt(PROTECT_COST_1D)} | 2d: {fmt(PROTECT_COST_2D)} | 3d: {fmt(PROTECT_COST_3D)}",
            parse_mode="HTML"
        )
        return

    cost = costs[arg]
    if data["balance"] < PROTECT_MIN_BALANCE:
        await update.message.reply_text(f"❌ Need at least {fmt(PROTECT_MIN_BALANCE)} in wallet.", parse_mode="HTML")
        return
    if data["balance"] < cost:
        await update.message.reply_text(f"❌ Need {fmt(cost)} for {arg} protection.", parse_mode="HTML")
        return

    prot_until = time.time() + durations[arg]
    await update_user(u.id, gid, {"balance": data["balance"] - cost, "protected_until": prot_until})

    await send_with_image(update, gid, IMG_PROTECT,
        f"""🛡️ <b>Protected!</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
⏰ Duration: {arg}
💸 Cost: {fmt(cost)}
👛 Balance: {fmt(data['balance'] - cost)}""")


async def revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    if data["status"] == "alive":
        await update.message.reply_text("✅ You're already alive!")
        return

    await update_user(u.id, gid, {"status": "alive"})
    await send_with_image(update, gid, IMG_REVIVE,
        f"""💫 <b>{u.first_name} Revived!</b>
⚔️ Back in the game!""")


async def heal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)

    if data["status"] == "dead":
        await update.message.reply_text("💀 You're dead! Use /revive first.")
        return

    hp = data.get("hp", DEFAULT_HP)
    if hp >= DEFAULT_HP:
        await update.message.reply_text(f"✅ Already at full HP ({DEFAULT_HP})!")
        return
    if data["balance"] < HEAL_COST:
        await update.message.reply_text(f"❌ Need {fmt(HEAL_COST)} to heal.")
        return

    new_hp  = min(DEFAULT_HP, hp + HEAL_AMOUNT)
    new_bal = data["balance"] - HEAL_COST
    await update_user(u.id, gid, {"hp": new_hp, "balance": new_bal})

    await send_with_image(update, gid, IMG_HEAL,
        f"""💊 <b>Healed!</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
🧬 HP: {hp} → {new_hp}
💸 Cost: {fmt(HEAL_COST)}
👛 Balance: {fmt(new_bal)}""")


async def hp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id

    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        data = await get_user(t.id, gid, t.first_name)
        name = t.first_name
    else:
        u = update.effective_user
        data = await get_user(u.id, gid, u.first_name)
        name = u.first_name

    shield = " 🛡️" if is_protected(data) else ""
    status = "🧬 Alive" if data["status"] == "alive" else "💀 Dead"
    hp_val = data.get("hp", DEFAULT_HP)

    await update.message.reply_text(
        f"❤️ <b>{name}</b>{shield}\n{status} — HP: {hp_val}/{DEFAULT_HP}",
        parse_mode="HTML"
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    from models.war import get_war_stats

    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        data = await get_user(t.id, gid, t.first_name)
        name = t.first_name
        uid  = t.id
    else:
        u = update.effective_user
        data = await get_user(u.id, gid, u.first_name)
        name = u.first_name
        uid  = u.id

    ws  = await get_war_stats(uid, gid)
    inv = data.get("inventory", {})

    best_w = "None"
    for key, wdata in inv.items():
        if key in WEAPONS and wdata.get("qty", 0) > 0 and is_weapon_valid(wdata):
            best_w = WEAPONS[key]["name"]
            break

    flex_owned = [FLEX_ITEMS[k]["name"] for k, v in inv.items() if k in FLEX_ITEMS and v.get("qty", 0) > 0]
    flex_str   = ", ".join(flex_owned[:3]) if flex_owned else "None"

    prot_str = "None"
    if is_protected(data):
        rem = int(data["protected_until"] - time.time())
        prot_str = f"{rem//3600}h {(rem%3600)//60}m left"

    streak = data.get("war_streak", 0)
    stag   = " 👑" if streak >= 10 else " 🔥🔥" if streak >= 5 else " 🔥" if streak >= 3 else ""
    nw     = data["balance"] + data["bank_balance"] - data["loan"]
    hp_val = data.get("hp", DEFAULT_HP)

    await update.message.reply_text(
        f"""👤 <b>{name}'s Profile</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
{'🟢 Alive' if data['status'] == 'alive' else '💀 Dead'}  ❤️ {hp_val}/{DEFAULT_HP} HP
💰 Wallet: {fmt(data['balance'])}
🏦 Bank: {fmt(data['bank_balance'])}
📊 Net Worth: {fmt(nw)}
◈ ━━━━━━ ⸙ ━━━━━━ ◈
⚔️ Kills: {data['kills']}  💀 Deaths: {data['deaths']}
🏆 Wars: {ws['wins']}W / {ws['losses']}L{stag}
◈ ━━━━━━ ⸙ ━━━━━━ ◈
🗡️ Weapon: {best_w}
🛡️ Shield: {prot_str}
💎 Flex: {flex_str}
{'💍 Married' if data.get('married_to') else '💔 Single'}""",
        parse_mode="HTML"
    )


async def topkill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    users = await get_top_killers(gid)

    if not users:
        await update.message.reply_text("No killers yet!")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = "\n".join(
        f"{medals[i] if i < 3 else f'{i+1}.'} <b>{u['username']}</b> — {u['kills']} kills"
        for i, u in enumerate(users)
    )
    await update.message.reply_text(
        f"☠️ <b>Top Killers</b>\n◈ ━━━━━━ ⸙ ━━━━━━ ◈\n{lines}",
        parse_mode="HTML"
    )


async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from models.user import get_all_users
    gid = update.effective_chat.id
    users = await get_all_users(gid)

    if not users:
        await update.message.reply_text("No users yet!")
        return

    sorted_u = sorted(users, key=lambda x: (x["kills"], x["balance"]), reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"]
    lines = "\n".join(
        f"{medals[i] if i < 3 else f'{i+1}.'} <b>{u['username']}</b> | ⚔️{u['kills']} | {fmt(u['balance'])}"
        for i, u in enumerate(sorted_u)
    )
    await update.message.reply_text(
        f"🏆 <b>Leaderboard</b>\n━━━━━━━━━━━━━━━\n{lines}",
        parse_mode="HTML"
    )
