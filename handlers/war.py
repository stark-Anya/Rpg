import random
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from models.war import (
    create_war, get_war, update_war, delete_war,
    save_war_history, get_war_stats, get_active_war_by_user,
    cleanup_expired_wars
)
from utils.helpers import format_coins, get_target_user, send_with_image
from config import SHOP_ITEMS, WAR_TIMEOUT, WAR_WINNER_PERCENT, WAR_PROTECTION_DAMAGE_REDUCE, IMG_WAR_WIN, IMG_WAR_DRAW


def accept_keyboard(war_id: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Accept", callback_data=f"war_accept_{war_id}"),
        InlineKeyboardButton("❌ Decline", callback_data=f"war_decline_{war_id}")
    ]])


def weapon_keyboard(war_id: str, side: str, inventory: dict):
    buttons = []
    for key, qty in inventory.items():
        if key in SHOP_ITEMS and SHOP_ITEMS[key]["type"] == "weapon" and qty > 0:
            item = SHOP_ITEMS[key]
            buttons.append([InlineKeyboardButton(
                f"{item['name']} ⚔️ {item['damage']} DMG",
                callback_data=f"war_weapon_{war_id}_{side}_{key}"
            )])
    buttons.append([InlineKeyboardButton("🛒 Buy Weapon — /shop", callback_data="war_noop")])
    return InlineKeyboardMarkup(buttons)


def coinflip_keyboard(war_id: str, side: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🪙 Heads", callback_data=f"war_flip_{war_id}_{side}_heads"),
        InlineKeyboardButton("🪙 Tails", callback_data=f"war_flip_{war_id}_{side}_tails")
    ]])


async def war_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    challenger = update.effective_user
    group_id = update.effective_chat.id

    # Cleanup expired
    expired = await cleanup_expired_wars()
    for w in expired:
        cu = await get_user(w["challenger_id"], w["group_id"])
        await update_user(w["challenger_id"], w["group_id"], {"balance": cu["balance"] + w["amount"]})
        try:
            await context.bot.edit_message_text(
                chat_id=w["group_id"], message_id=w["message_id"],
                text=f"⏰ War challenge expired! {format_coins(w['amount'])} refunded to {w['challenger_name']}.",
                reply_markup=None
            )
        except Exception:
            pass

    target_id, target_name = await get_target_user(update, context)
    try:
        amount = int(context.args[0]) if update.message.reply_to_message else int(context.args[1]) if len(context.args) >= 2 else None
    except (ValueError, IndexError):
        amount = None

    if not target_id or not amount:
        await update.message.reply_text(
            "❌ <b>Usage:</b> Reply + <code>/war [amount]</code>\nOr: <code>/war [user_id] [amount]</code>",
            parse_mode="HTML"
        )
        return

    if target_id == challenger.id:
        await update.message.reply_text("❌ You can't war with yourself!")
        return
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    existing = await get_active_war_by_user(challenger.id, group_id)
    if existing:
        await update.message.reply_text("❌ You already have an active war!")
        return

    c_data = await get_user(challenger.id, group_id, challenger.first_name)
    t_data = await get_user(target_id, group_id, target_name)

    if c_data["status"] == "dead":
        await update.message.reply_text("💀 You are dead! Use /revive first.")
        return
    if t_data["status"] == "dead":
        await update.message.reply_text(f"💀 <b>{target_name}</b> is dead and can't fight!", parse_mode="HTML")
        return
    if c_data["balance"] < amount:
        await update.message.reply_text(f"❌ Not enough coins!\n💰 You have: {format_coins(c_data['balance'])}", parse_mode="HTML")
        return
    if t_data["balance"] < amount:
        await update.message.reply_text(f"❌ <b>{target_name}</b> doesn't have enough coins!", parse_mode="HTML")
        return

    # Deduct challenger stake
    await update_user(challenger.id, group_id, {"balance": c_data["balance"] - amount})

    winner_prize = int(amount * 2 * WAR_WINNER_PERCENT)
    msg = await update.message.reply_text(
        f"""⚔️ <b>WAR CHALLENGE!</b>
━━━━━━━━━━━━━━━
🥊 <b>{challenger.first_name}</b> vs <b>{target_name}</b>
💰 <b>Stake:</b> {format_coins(amount)} each
🏆 <b>Winner gets:</b> {format_coins(winner_prize)}
⏰ <b>Expires in:</b> 60 seconds

<b>{target_name}</b>, do you accept the challenge?""",
        parse_mode="HTML",
        reply_markup=accept_keyboard("TEMP")
    )

    war_id = await create_war(
        challenger.id, challenger.first_name,
        target_id, target_name,
        amount, group_id, msg.message_id
    )
    await msg.edit_reply_markup(accept_keyboard(war_id))
    asyncio.create_task(_auto_cancel(war_id, group_id, challenger.id, amount, msg, context))


async def _auto_cancel(war_id, group_id, challenger_id, amount, msg, context):
    await asyncio.sleep(WAR_TIMEOUT)
    w = await get_war(war_id)
    if w and w["status"] == "pending":
        await delete_war(war_id)
        u = await get_user(challenger_id, group_id)
        await update_user(challenger_id, group_id, {"balance": u["balance"] + amount})
        try:
            await msg.edit_text(
                f"⏰ War challenge expired!\n💰 {format_coins(amount)} refunded to {w['challenger_name']}.",
                reply_markup=None
            )
        except Exception:
            pass


async def war_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    group_id = update.effective_chat.id
    data = query.data

    if data == "war_noop":
        await query.answer("Visit /shop in the group to buy weapons!", show_alert=True)
        return

    # ── ACCEPT ──
    if data.startswith("war_accept_"):
        war_id = data[len("war_accept_"):]
        w = await get_war(war_id)
        if not w or w["status"] != "pending":
            await query.answer("⏰ War expired!", show_alert=True)
            return
        if user.id != w["target_id"]:
            await query.answer("❌ This challenge is not for you!", show_alert=True)
            return

        t_data = await get_user(user.id, group_id, user.first_name)
        if t_data["balance"] < w["amount"]:
            await query.answer("❌ Not enough coins!", show_alert=True)
            return

        await update_user(user.id, group_id, {"balance": t_data["balance"] - w["amount"]})
        await update_war(war_id, {"status": "weapon_select"})
        await query.answer()

        winner_prize = int(w["amount"] * 2 * WAR_WINNER_PERCENT)
        c_data = await get_user(w["challenger_id"], group_id)

        # Edit original message
        try:
            await query.edit_message_text(
                f"""⚔️ <b>WAR ACCEPTED!</b>
━━━━━━━━━━━━━━━
🥊 <b>{w['challenger_name']}</b> vs <b>{w['target_name']}</b>
💰 <b>Total Pot:</b> {format_coins(w['amount'] * 2)}
🏆 <b>Winner gets:</b> {format_coins(winner_prize)}

⏳ <i>Both fighters, choose your weapons below!</i>""",
                parse_mode="HTML",
                reply_markup=None
            )
        except Exception:
            pass

        # Challenger weapon select message
        c_inv = c_data.get("inventory", {})
        c_msg = await context.bot.send_message(
            chat_id=group_id,
            text=f"""🗡️ <b>{w['challenger_name']}</b>, choose your weapon!
<i>(Only you can click your button)</i>""",
            parse_mode="HTML",
            reply_markup=weapon_keyboard(war_id, "challenger", c_inv)
        )

        # Target weapon select message
        t_inv = t_data.get("inventory", {})
        t_msg = await context.bot.send_message(
            chat_id=group_id,
            text=f"""🗡️ <b>{w['target_name']}</b>, choose your weapon!
<i>(Only you can click your button)</i>""",
            parse_mode="HTML",
            reply_markup=weapon_keyboard(war_id, "target", t_inv)
        )

        await update_war(war_id, {
            "challenger_msg_id": c_msg.message_id,
            "target_msg_id": t_msg.message_id
        })

    # ── DECLINE ──
    elif data.startswith("war_decline_"):
        war_id = data[len("war_decline_"):]
        w = await get_war(war_id)
        if not w or w["status"] != "pending":
            await query.answer()
            return
        if user.id != w["target_id"]:
            await query.answer("❌ Not your challenge!", show_alert=True)
            return

        await query.answer()
        await delete_war(war_id)
        u = await get_user(w["challenger_id"], group_id)
        await update_user(w["challenger_id"], group_id, {"balance": u["balance"] + w["amount"]})

        try:
            await query.edit_message_text(
                f"""❌ <b>War Declined!</b>
━━━━━━━━━━━━━━━
😤 <b>{w['target_name']}</b> refused the challenge.
💰 {format_coins(w['amount'])} refunded to <b>{w['challenger_name']}</b>.""",
                parse_mode="HTML",
                reply_markup=None
            )
        except Exception:
            pass

    # ── WEAPON SELECT ──
    elif data.startswith("war_weapon_"):
        parts = data.split("_")
        war_id = parts[2]
        side = parts[3]
        weapon_key = "_".join(parts[4:])

        w = await get_war(war_id)
        if not w or w["status"] != "weapon_select":
            await query.answer("⚠️ War no longer active!", show_alert=True)
            return

        # Verify correct user
        expected_id = w["challenger_id"] if side == "challenger" else w["target_id"]
        if user.id != expected_id:
            await query.answer("❌ This is not your weapon selection!", show_alert=True)
            return

        already = w.get("challenger_weapon") if side == "challenger" else w.get("target_weapon")
        if already:
            await query.answer("✅ Already selected!", show_alert=True)
            return

        if weapon_key not in SHOP_ITEMS:
            await query.answer("❌ Invalid weapon!", show_alert=True)
            return

        await query.answer()
        field = "challenger_weapon" if side == "challenger" else "target_weapon"
        await update_war(war_id, {field: weapon_key})

        try:
            await query.edit_message_text(
                f"""✅ <b>Weapon Selected!</b>
🗡️ <i>Your choice is locked in — hidden until battle ends!</i>
⏳ <i>Waiting for opponent...</i>""",
                parse_mode="HTML",
                reply_markup=None
            )
        except Exception:
            pass

        # Check if both selected
        w = await get_war(war_id)
        if w.get("challenger_weapon") and w.get("target_weapon"):
            await resolve_war(war_id, group_id, context)

    # ── COIN FLIP ──
    elif data.startswith("war_flip_"):
        parts = data.split("_")
        war_id = parts[2]
        side = parts[3]
        choice = parts[4]

        w = await get_war(war_id)
        if not w or w["status"] != "coin_flip":
            await query.answer("⚠️ No active coin flip!", show_alert=True)
            return

        expected_id = w["challenger_id"] if side == "challenger" else w["target_id"]
        if user.id != expected_id:
            await query.answer("❌ Not your coin flip!", show_alert=True)
            return

        field = "challenger_flip" if side == "challenger" else "target_flip"
        if w.get(field):
            await query.answer("✅ Already chose!", show_alert=True)
            return

        await query.answer()
        await update_war(war_id, {field: choice})

        try:
            await query.edit_message_text(
                f"""🪙 <b>You chose {choice.capitalize()}!</b>
⏳ <i>Waiting for opponent to choose...</i>""",
                parse_mode="HTML",
                reply_markup=None
            )
        except Exception:
            pass

        w = await get_war(war_id)
        if w.get("challenger_flip") and w.get("target_flip"):
            await resolve_coin_flip(war_id, group_id, context)


async def resolve_war(war_id: str, group_id: int, context):
    w = await get_war(war_id)
    c_key = w["challenger_weapon"]
    t_key = w["target_weapon"]
    c_item = SHOP_ITEMS[c_key]
    t_item = SHOP_ITEMS[t_key]

    c_data = await get_user(w["challenger_id"], group_id)
    t_data = await get_user(w["target_id"], group_id)

    now = time.time()
    c_protected = c_data.get("protected_until") and now < c_data["protected_until"]
    t_protected = t_data.get("protected_until") and now < t_data["protected_until"]

    # Damage dealt to each
    c_takes = t_item["damage"]
    t_takes = c_item["damage"]
    if c_protected:
        c_takes = int(c_takes * (1 - WAR_PROTECTION_DAMAGE_REDUCE))
    if t_protected:
        t_takes = int(t_takes * (1 - WAR_PROTECTION_DAMAGE_REDUCE))

    amount = w["amount"]
    winner_prize = int(amount * 2 * WAR_WINNER_PERCENT)

    # Draw — same weapon
    if c_key == t_key:
        await update_war(war_id, {"status": "coin_flip"})
        c_flip_msg = await context.bot.send_message(
            chat_id=group_id,
            text=f"""🪙 <b>IT'S A DRAW!</b>
━━━━━━━━━━━━━━━
Both used <b>{c_item['name']}</b>!
<b>{w['challenger_name']}</b>, choose your side:""",
            parse_mode="HTML",
            reply_markup=coinflip_keyboard(war_id, "challenger")
        )
        t_flip_msg = await context.bot.send_message(
            chat_id=group_id,
            text=f"""🪙 <b>IT'S A DRAW!</b>
━━━━━━━━━━━━━━━
Both used <b>{c_item['name']}</b>!
<b>{w['target_name']}</b>, choose your side:""",
            parse_mode="HTML",
            reply_markup=coinflip_keyboard(war_id, "target")
        )
        await update_war(war_id, {
            "c_flip_msg_id": c_flip_msg.message_id,
            "t_flip_msg_id": t_flip_msg.message_id
        })
        return

    # Winner = more damage dealt to opponent
    if t_takes >= c_takes:
        winner_id, winner_name, winner_weapon = w["challenger_id"], w["challenger_name"], c_item["name"]
        loser_id, loser_name, loser_weapon = w["target_id"], w["target_name"], t_item["name"]
        w_dmg, l_dmg = t_takes, c_takes
    else:
        winner_id, winner_name, winner_weapon = w["target_id"], w["target_name"], t_item["name"]
        loser_id, loser_name, loser_weapon = w["challenger_id"], w["challenger_name"], c_item["name"]
        w_dmg, l_dmg = c_takes, t_takes

    await finish_war(war_id, group_id, context, winner_id, winner_name,
                     loser_id, loser_name, winner_weapon, loser_weapon,
                     w_dmg, l_dmg, winner_prize, amount, is_flip=False)


async def resolve_coin_flip(war_id: str, group_id: int, context):
    w = await get_war(war_id)
    result = random.choice(["heads", "tails"])
    amount = w["amount"]
    winner_prize = int(amount * 2 * WAR_WINNER_PERCENT)

    if w["challenger_flip"] == result:
        winner_id, winner_name = w["challenger_id"], w["challenger_name"]
        loser_id, loser_name = w["target_id"], w["target_name"]
    else:
        winner_id, winner_name = w["target_id"], w["target_name"]
        loser_id, loser_name = w["challenger_id"], w["challenger_name"]

    c_weapon = SHOP_ITEMS.get(w["challenger_weapon"], {}).get("name", "?")
    t_weapon = SHOP_ITEMS.get(w["target_weapon"], {}).get("name", "?")

    await context.bot.send_message(
        chat_id=group_id,
        text=f"""🪙 <b>COIN FLIP RESULT!</b>
━━━━━━━━━━━━━━━
🎲 <b>Result:</b> {result.capitalize()}!
🏆 <b>Winner:</b> {winner_name}
💸 <b>Loser:</b> {loser_name}
💰 <b>{winner_name} wins:</b> {format_coins(winner_prize)}""",
        parse_mode="HTML"
    )

    await finish_war(war_id, group_id, context, winner_id, winner_name,
                     loser_id, loser_name, c_weapon, t_weapon,
                     0, 0, winner_prize, amount, is_flip=True)


async def finish_war(war_id, group_id, context,
                     winner_id, winner_name, loser_id, loser_name,
                     winner_weapon, loser_weapon, w_dmg, l_dmg,
                     winner_prize, amount, is_flip):

    w_data = await get_user(winner_id, group_id)
    new_winner_bal = w_data["balance"] + winner_prize
    new_streak = w_data.get("war_streak", 0) + 1

    await update_user(winner_id, group_id, {
        "balance": new_winner_bal,
        "kills": w_data.get("kills", 0) + 1,
        "war_streak": new_streak
    })
    await update_user(loser_id, group_id, {"war_streak": 0})

    streak_msg = ""
    if new_streak == 3:
        streak_msg = "\n🔥 <b>3 Win Streak!</b> +10% loot bonus active!"
    elif new_streak == 5:
        streak_msg = "\n🔥🔥 <b>5 Win Streak!</b> +20% loot bonus!"
    elif new_streak == 10:
        streak_msg = "\n👑 <b>LEGENDARY 10 Win Streak!</b>"

    wanted_msg = await _check_wanted(winner_id, group_id, winner_name, context)

    await save_war_history({
        "group_id": group_id,
        "winner_id": winner_id, "winner_name": winner_name,
        "loser_id": loser_id, "loser_name": loser_name,
        "winner_weapon": winner_weapon, "loser_weapon": loser_weapon,
        "winner_damage": w_dmg, "loser_damage": l_dmg,
        "amount": amount, "winner_amount": winner_prize,
        "is_flip": is_flip, "timestamp": time.time()
    })
    await delete_war(war_id)

    if not is_flip:
        caption = f"""⚔️ <b>WAR RESULT!</b>
━━━━━━━━━━━━━━━
🏆 <b>Winner:</b> {winner_name}
<blockquote>Weapon: {winner_weapon} | DMG dealt: {w_dmg}</blockquote>
💀 <b>Loser:</b> {loser_name}
<blockquote>Weapon: {loser_weapon} | DMG dealt: {l_dmg}</blockquote>
━━━━━━━━━━━━━━━
💰 <b>{winner_name} wins:</b> {format_coins(winner_prize)}
💸 <b>{loser_name} lost:</b> {format_coins(amount)}{streak_msg}"""
    else:
        caption = f"""🪙 <b>COIN FLIP WAR RESULT!</b>
━━━━━━━━━━━━━━━
🏆 <b>Winner:</b> {winner_name}
💀 <b>Loser:</b> {loser_name}
━━━━━━━━━━━━━━━
💰 <b>{winner_name} wins:</b> {format_coins(winner_prize)}
💸 <b>{loser_name} lost:</b> {format_coins(amount)}{streak_msg}"""

    if wanted_msg:
        caption += f"\n\n{wanted_msg}"

    await send_with_image(context.bot, group_id, IMG_WAR_WIN, caption)


async def _check_wanted(user_id, group_id, username, context) -> str:
    from database import db
    wanted_col = db["wanted"]
    today = int(time.time() // 86400)
    rec = await wanted_col.find_one({"user_id": user_id, "group_id": group_id, "day": today})
    if rec:
        kills = rec["kills"] + 1
        await wanted_col.update_one({"_id": rec["_id"]}, {"$set": {"kills": kills}})
    else:
        kills = 1
        await wanted_col.insert_one({"user_id": user_id, "group_id": group_id, "day": today, "username": username, "kills": 1})
    if kills == 10:
        return f"🚨 <b>{username} is now WANTED!</b> 10 kills today!\n💰 <b>Bounty:</b> 500 coins!"
    return ""


async def warlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    stats = await get_war_stats(user.id, group_id)
    if stats["total"] == 0:
        await update.message.reply_text("⚔️ You haven't fought any wars yet!")
        return
    await update.message.reply_text(
        f"""📜 <b>{user.first_name}'s War Log</b>
━━━━━━━━━━━━━━━
🏆 <b>Wins:</b> {stats['wins']}  💀 <b>Losses:</b> {stats['losses']}
📊 <b>Total Wars:</b> {stats['total']}
💰 <b>Total Earned:</b> {format_coins(stats['total_earned'])}
💸 <b>Total Lost:</b> {format_coins(stats['total_lost'])}
🥇 <b>Biggest Win:</b> {format_coins(stats['biggest_win'])}""",
        parse_mode="HTML"
    )


async def wanted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import db
    wanted_col = db["wanted"]
    group_id = update.effective_chat.id
    today = int(time.time() // 86400)
    records = await wanted_col.find(
        {"group_id": group_id, "day": today, "kills": {"$gte": 10}}
    ).sort("kills", -1).to_list(length=10)

    if not records:
        await update.message.reply_text("✅ No wanted players today!")
        return

    text = "🚨 <b>WANTED LIST</b>\n━━━━━━━━━━━━━━━\n"
    for i, r in enumerate(records, 1):
        text += f"{i}. <b>{r['username']}</b> — {r['kills']} kills 🔫\n"
    text += "\n💰 <b>Bounty:</b> 500 coins for killing a wanted player!"
    await update.message.reply_text(text, parse_mode="HTML")
