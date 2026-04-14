import random, time, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from models.war import create_war, get_war, update_war, delete_war, save_war_history, get_war_stats, get_active_war_by_user, cleanup_expired_wars
from utils.helpers import fmt, get_target_user, send_with_image, get_best_weapon, is_weapon_valid
from config import WEAPONS, WAR_TIMEOUT, WAR_WINNER_PERCENT, WAR_DRAW_PERCENT, IMG_WAR_WIN, IMG_WAR_DRAW


def accept_kb(war_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Accept", callback_data=f"war_accept_{war_id}"),
        InlineKeyboardButton("❌ Decline", callback_data=f"war_decline_{war_id}")
    ]])


def coinflip_kb(war_id, side):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🪙 Heads", callback_data=f"war_flip_{war_id}_{side}_heads"),
        InlineKeyboardButton("🪙 Tails", callback_data=f"war_flip_{war_id}_{side}_tails")
    ]])


async def war_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    challenger = update.effective_user
    gid = update.effective_chat.id

    # Cleanup expired
    for w in await cleanup_expired_wars():
        cu = await get_user(w["challenger_id"], w["group_id"])
        await update_user(w["challenger_id"], w["group_id"], {"balance": cu["balance"] + w["amount"]})
        try:
            await context.bot.edit_message_text(
                chat_id=w["group_id"], message_id=w["message_id"],
                text=f"⏰ War expired. {fmt(w['amount'])} refunded to {w['challenger_name']}.")
        except Exception:
            pass

    tid, tname = await get_target_user(update, context)
    try:
        amount = int(context.args[0]) if update.message.reply_to_message else int(context.args[1]) if len(context.args)>=2 else None
    except (ValueError, IndexError):
        amount = None

    if not tid or not amount:
        await update.message.reply_text("❌ Reply + <code>/war [amount]</code>", parse_mode="HTML"); return
    if tid == challenger.id:
        await update.message.reply_text("❌ Can't war yourself!"); return
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!"); return
    if await get_active_war_by_user(challenger.id, gid):
        await update.message.reply_text("❌ You already have an active war!"); return

    cdata = await get_user(challenger.id, gid, challenger.first_name)
    tdata = await get_user(tid, gid, tname)

    if cdata["status"] == "dead":
        await update.message.reply_text("💀 Dead! Use /revive."); return
    if tdata["status"] == "dead":
        await update.message.reply_text(f"💀 {tname} is dead!"); return
    if cdata["balance"] < amount:
        await update.message.reply_text(f"❌ Need {fmt(amount)}. You have {fmt(cdata['balance'])}."); return
    if tdata["balance"] < amount:
        await update.message.reply_text(f"❌ {tname} can't afford this war!"); return

    await update_user(challenger.id, gid, {"balance": cdata["balance"] - amount})
    prize = int(amount * 2 * WAR_WINNER_PERCENT)

    msg = await update.message.reply_text(
        f"""⚔️ <b>WAR CHALLENGE!</b>
━━━━━━━━━━━━━━━
🥊 <b>{challenger.first_name}</b> vs <b>{tname}</b>
💰 <b>Stake:</b> {fmt(amount)} each
🏆 <b>Winner gets:</b> {fmt(prize)}
⏰ <b>Expires in:</b> 60s

<b>{tname}</b>, accept the challenge?""",
        parse_mode="HTML", reply_markup=accept_kb("TEMP"))

    war_id = await create_war(challenger.id, challenger.first_name, tid, tname, amount, gid, msg.message_id)
    await msg.edit_reply_markup(accept_kb(war_id))
    asyncio.create_task(_auto_cancel(war_id, gid, challenger.id, amount, msg, context))


async def _auto_cancel(war_id, gid, cid, amount, msg, context):
    await asyncio.sleep(WAR_TIMEOUT)
    w = await get_war(war_id)
    if w and w["status"] == "pending":
        await delete_war(war_id)
        u = await get_user(cid, gid)
        await update_user(cid, gid, {"balance": u["balance"] + amount})
        try:
            await msg.edit_text(f"⏰ War expired! {fmt(amount)} refunded to {w['challenger_name']}.", reply_markup=None)
        except Exception:
            pass


async def war_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    gid   = update.effective_chat.id
    data  = query.data

    if data.startswith("war_accept_"):
        war_id = data[len("war_accept_"):]
        w = await get_war(war_id)
        if not w or w["status"] != "pending":
            await query.answer("⏰ Expired!", show_alert=True); return
        if user.id != w["target_id"]:
            await query.answer("❌ Not your challenge!", show_alert=True); return

        tdata = await get_user(user.id, gid, user.first_name)
        if tdata["balance"] < w["amount"]:
            await query.answer("❌ Not enough coins!", show_alert=True); return

        await query.answer()
        await update_user(user.id, gid, {"balance": tdata["balance"] - w["amount"]})
        await update_war(war_id, {"status": "resolving"})

        # Auto pick best weapons
        cdata = await get_user(w["challenger_id"], gid)
        c_key, c_item = get_best_weapon(cdata.get("inventory", {}))
        t_key, t_item = get_best_weapon(tdata.get("inventory", {}))

        try:
            await query.edit_message_text(
                f"""⚔️ <b>WAR ACCEPTED!</b>
━━━━━━━━━━━━━━━
🥊 <b>{w['challenger_name']}</b> vs <b>{w['target_name']}</b>
💰 <b>Pot:</b> {fmt(w['amount']*2)}

🗡️ <b>{w['challenger_name']}</b> → {c_item['name'] if c_item else 'No Weapon'}
🗡️ <b>{w['target_name']}</b> → {t_item['name'] if t_item else 'No Weapon'}

⚡ <i>Resolving...</i>""",
                parse_mode="HTML", reply_markup=None)
        except Exception:
            pass

        await update_war(war_id, {"challenger_weapon": c_key, "target_weapon": t_key})
        await resolve_war(war_id, gid, context)

    elif data.startswith("war_decline_"):
        war_id = data[len("war_decline_"):]
        w = await get_war(war_id)
        if not w or w["status"] != "pending":
            await query.answer(); return
        if user.id != w["target_id"]:
            await query.answer("❌ Not yours!", show_alert=True); return
        await query.answer()
        await delete_war(war_id)
        u = await get_user(w["challenger_id"], gid)
        await update_user(w["challenger_id"], gid, {"balance": u["balance"] + w["amount"]})
        try:
            await query.edit_message_text(
                f"❌ <b>{w['target_name']}</b> declined.\n💰 {fmt(w['amount'])} refunded to {w['challenger_name']}.",
                parse_mode="HTML", reply_markup=None)
        except Exception:
            pass

    elif data.startswith("war_flip_"):
        parts  = data.split("_")
        war_id = parts[2]; side = parts[3]; choice = parts[4]
        w = await get_war(war_id)
        if not w or w["status"] != "coin_flip":
            await query.answer("⚠️ No active flip!", show_alert=True); return
        expected = w["challenger_id"] if side == "challenger" else w["target_id"]
        if user.id != expected:
            await query.answer("❌ Not your flip!", show_alert=True); return
        field = "challenger_flip" if side == "challenger" else "target_flip"
        if w.get(field):
            await query.answer("✅ Already chose!", show_alert=True); return
        await query.answer()
        await update_war(war_id, {field: choice})
        try:
            await query.edit_message_text(
                f"🪙 <b>You chose {choice.capitalize()}!</b>\n⏳ Waiting for opponent...",
                parse_mode="HTML", reply_markup=None)
        except Exception:
            pass
        w = await get_war(war_id)
        if w.get("challenger_flip") and w.get("target_flip"):
            await resolve_coin_flip(war_id, gid, context)


async def resolve_war(war_id, gid, context):
    w = await get_war(war_id)
    c_key = w.get("challenger_weapon")
    t_key = w.get("target_weapon")
    c_item = WEAPONS.get(c_key) if c_key else None
    t_item = WEAPONS.get(t_key) if t_key else None
    c_price = c_item["price"] if c_item else 0
    t_price = t_item["price"] if t_item else 0
    amount  = w["amount"]
    prize   = int(amount * 2 * WAR_WINNER_PERCENT)
    draw_each = int(amount * 2 * WAR_DRAW_PERCENT)

    # Draw: same weapon or same price
    if c_key == t_key or c_price == t_price:
        await update_war(war_id, {"status": "coin_flip"})
        cm = await context.bot.send_message(chat_id=gid,
            text=f"""🪙 <b>DRAW! Coin Flip!</b>
Both used <b>{c_item['name'] if c_item else 'No Weapon'}</b>!
<b>{w['challenger_name']}</b>, choose:""",
            parse_mode="HTML", reply_markup=coinflip_kb(war_id, "challenger"))
        tm = await context.bot.send_message(chat_id=gid,
            text=f"""🪙 <b>DRAW! Coin Flip!</b>
Both used <b>{t_item['name'] if t_item else 'No Weapon'}</b>!
<b>{w['target_name']}</b>, choose:""",
            parse_mode="HTML", reply_markup=coinflip_kb(war_id, "target"))
        await update_war(war_id, {"c_flip_msg": cm.message_id, "t_flip_msg": tm.message_id})
        return

    if c_price >= t_price:
        wid, wname, wweapon = w["challenger_id"], w["challenger_name"], c_item["name"] if c_item else "—"
        lid, lname, lweapon = w["target_id"],     w["target_name"],     t_item["name"] if t_item else "—"
    else:
        wid, wname, wweapon = w["target_id"],     w["target_name"],     t_item["name"] if t_item else "—"
        lid, lname, lweapon = w["challenger_id"], w["challenger_name"], c_item["name"] if c_item else "—"

    await _finish(war_id, gid, context, wid, wname, wweapon, lid, lname, lweapon, prize, amount, False)


async def resolve_coin_flip(war_id, gid, context):
    w = await get_war(war_id)
    result    = random.choice(["heads", "tails"])
    amount    = w["amount"]
    prize     = int(amount * 2 * WAR_WINNER_PERCENT)

    if w["challenger_flip"] == result:
        wid, wname = w["challenger_id"], w["challenger_name"]
        lid, lname = w["target_id"],     w["target_name"]
    else:
        wid, wname = w["target_id"],     w["target_name"]
        lid, lname = w["challenger_id"], w["challenger_name"]

    await context.bot.send_message(chat_id=gid,
        text=f"🪙 <b>Result: {result.capitalize()}!</b>\n🏆 <b>{wname}</b> wins the flip!", parse_mode="HTML")
    await _finish(war_id, gid, context, wid, wname, "Coin Flip", lid, lname, "Coin Flip", prize, amount, True)


async def _finish(war_id, gid, context, wid, wname, wweapon, lid, lname, lweapon, prize, amount, is_flip):
    wdata = await get_user(wid, gid)
    streak = wdata.get("war_streak", 0) + 1
    await update_user(wid, gid, {"balance": wdata["balance"]+prize, "kills": wdata.get("kills",0)+1, "war_streak": streak})
    await update_user(lid, gid, {"war_streak": 0})

    streak_msg = ""
    if streak == 3:   streak_msg = "\n🔥 <b>3 Win Streak!</b>"
    elif streak == 5: streak_msg = "\n🔥🔥 <b>5 Win Streak!</b>"
    elif streak == 10:streak_msg = "\n👑 <b>LEGENDARY Streak!</b>"

    await save_war_history({"group_id":gid,"winner_id":wid,"winner_name":wname,"loser_id":lid,"loser_name":lname,
        "winner_weapon":wweapon,"loser_weapon":lweapon,"amount":amount,"winner_amount":prize,"is_flip":is_flip,"timestamp":time.time()})
    await delete_war(war_id)

    caption = f"""⚔️ <b>WAR RESULT!</b>
━━━━━━━━━━━━━━━
🏆 <b>Winner:</b> {wname}
<blockquote>Used: {wweapon}</blockquote>
💀 <b>Loser:</b> {lname}
<blockquote>Used: {lweapon}</blockquote>
━━━━━━━━━━━━━━━
💸 <b>{wname} wins:</b> {fmt(prize)}
💸 <b>{lname} lost:</b> {fmt(amount)}{streak_msg}"""

    await send_with_image(context.bot, gid, IMG_WAR_WIN, caption)


async def warlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user; gid = update.effective_chat.id
    s = await get_war_stats(u.id, gid)
    if s["total"] == 0:
        await update.message.reply_text("⚔️ No wars yet!"); return
    await update.message.reply_text(
        f"""📜 <b>{u.first_name}'s War Log</b>
━━━━━━━━━━━━━━━
🏆 <b>Wins:</b> {s['wins']} | 💀 <b>Losses:</b> {s['losses']}
📊 <b>Total:</b> {s['total']}
💰 <b>Earned:</b> {fmt(s['total_earned'])}
💸 <b>Lost:</b> {fmt(s['total_lost'])}
🥇 <b>Best Win:</b> {fmt(s['biggest_win'])}""", parse_mode="HTML")


async def wanted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import db
    wanted_col = db["wanted"]
    gid   = update.effective_chat.id
    today = int(time.time() // 86400)
    recs  = await wanted_col.find({"group_id":gid,"day":today,"kills":{"$gte":10}}).sort("kills",-1).to_list(10)
    if not recs:
        await update.message.reply_text("✅ No wanted players today!"); return
    lines = "\n".join(f"{i+1}. <b>{r['username']}</b> — {r['kills']} kills 🔫" for i,r in enumerate(recs))
    await update.message.reply_text(
        f"""🚨 <b>WANTED LIST</b>
━━━━━━━━━━━━━━━
{lines}

💰 <b>Bounty:</b> {fmt(500)} per wanted kill!""", parse_mode="HTML")
