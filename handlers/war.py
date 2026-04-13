import random
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from models.user import get_user, update_user
from models.war import (
    create_war, get_war, update_war, delete_war,
    save_war_history, get_war_stats, get_active_war_by_user,
    cleanup_expired_wars
)
from utils.helpers import format_coins, get_target_user
from config import SHOP_ITEMS


def war_accept_keyboard(war_id: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Accept", callback_data=f"war_accept_{war_id}"),
        InlineKeyboardButton("❌ Decline", callback_data=f"war_decline_{war_id}")
    ]])


def weapon_select_keyboard(war_id: str, inventory: dict, side: str):
    buttons = []
    for key, qty in inventory.items():
        if key in SHOP_ITEMS and SHOP_ITEMS[key]["type"] == "weapon" and qty > 0:
            item = SHOP_ITEMS[key]
            buttons.append([InlineKeyboardButton(
                f"{item['name']} (DMG: {item['damage']})",
                callback_data=f"war_weapon_{war_id}_{side}_{key}"
            )])
    buttons.append([InlineKeyboardButton(
        "🛒 Buy Weapon", callback_data=f"war_buyweapon_{war_id}"
    )])
    return InlineKeyboardMarkup(buttons)


def coin_flip_keyboard(war_id: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🪙 Heads", callback_data=f"war_flip_{war_id}_heads"),
        InlineKeyboardButton("🪙 Tails", callback_data=f"war_flip_{war_id}_tails")
    ]])


async def war_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    challenger = update.effective_user
    group_id = update.effective_chat.id

    # Cleanup expired wars first
    expired = await cleanup_expired_wars()
    for w in expired:
        try:
            await context.bot.edit_message_text(
                chat_id=group_id,
                message_id=w["message_id"],
                text=f"⏰ War challenge expired — {w['challenger_name']} vs {w['target_name']}",
                reply_markup=None
            )
            # Refund both
            cu = await get_user(w["challenger_id"], group_id)
            await update_user(w["challenger_id"], group_id, {"balance": cu["balance"] + w["amount"]})
        except Exception:
            pass

    target_id, target_name = await get_target_user(update, context)

    try:
        if update.message.reply_to_message:
            amount = int(context.args[0]) if context.args else None
        else:
            amount = int(context.args[1]) if len(context.args) >= 2 else None
    except (ValueError, IndexError):
        amount = None

    if not target_id or not amount:
        await update.message.reply_text(
            "❌ Usage: Reply + <code>/war [amount]</code>\n"
            "Or: <code>/war [user_id] [amount]</code>",
            parse_mode="HTML"
        )
        return

    if target_id == challenger.id:
        await update.message.reply_text("❌ You can't war with yourself!")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    # Check existing active war
    existing = await get_active_war_by_user(challenger.id, group_id)
    if existing:
        await update.message.reply_text("❌ You already have an active war! Finish it first.")
        return

    challenger_data = await get_user(challenger.id, group_id, challenger.first_name)
    target_data = await get_user(target_id, group_id, target_name)

    if challenger_data["status"] == "dead":
        await update.message.reply_text("💀 You are dead! Use /revive first.")
        return

    if target_data["status"] == "dead":
        await update.message.reply_text(f"💀 {target_name} is dead and can't fight!")
        return

    if challenger_data["balance"] < amount:
        await update.message.reply_text(
            f"❌ Not enough coins!\n💰 You have: {format_coins(challenger_data['balance'])}"
        )
        return

    if target_data["balance"] < amount:
        await update.message.reply_text(
            f"❌ {target_name} doesn't have enough coins for this war!\n"
            f"💰 Their balance: {format_coins(target_data['balance'])}"
        )
        return

    # Deduct challenger's stake immediately
    await update_user(challenger.id, group_id, {"balance": challenger_data["balance"] - amount})

    msg = await update.message.reply_text(
        f"⚔️ <b>WAR CHALLENGE!</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🥊 {challenger.first_name} vs {target_name}\n"
        f"💰 Stake: {format_coins(amount)} each\n"
        f"🏆 Winner gets: {format_coins(int(amount * 2 * 0.9))}\n"
        f"⏰ Expires in 60 seconds\n\n"
        f"<b>{target_name}</b>, do you accept?",
        parse_mode="HTML",
        reply_markup=war_accept_keyboard("PLACEHOLDER")
    )

    war_id = await create_war(
        challenger.id, challenger.first_name,
        target_id, target_name,
        amount, group_id, msg.message_id
    )

    # Update message with real war_id
    await msg.edit_reply_markup(war_accept_keyboard(war_id))

    # Schedule auto-cancel after 60s
    asyncio.create_task(auto_cancel_war(war_id, group_id, challenger.id, amount, msg, context))


async def auto_cancel_war(war_id, group_id, challenger_id, amount, msg, context):
    await asyncio.sleep(60)
    war_data = await get_war(war_id)
    if war_data and war_data["status"] == "pending":
        await delete_war(war_id)
        # Refund challenger
        u = await get_user(challenger_id, group_id)
        await update_user(challenger_id, group_id, {"balance": u["balance"] + amount})
        try:
            await msg.edit_text(
                f"⏰ War challenge expired! {format_coins(amount)} refunded to {war_data['challenger_name']}.",
                reply_markup=None
            )
        except Exception:
            pass


async def war_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    group_id = update.effective_chat.id
    data = query.data

    # Accept / Decline
    if data.startswith("war_accept_"):
        war_id = data.replace("war_accept_", "")
        war_data = await get_war(war_id)
        if not war_data:
            await query.edit_message_text("⏰ This war has expired!")
            return
        if war_data["status"] != "pending":
            return
        if user.id != war_data["target_id"]:
            await query.answer("❌ This challenge is not for you!", show_alert=True)
            return

        target_data = await get_user(user.id, group_id, user.first_name)
        if target_data["balance"] < war_data["amount"]:
            await query.answer("❌ You don't have enough coins!", show_alert=True)
            return

        # Deduct target's stake
        await update_user(user.id, group_id, {"balance": target_data["balance"] - war_data["amount"]})
        await update_war(war_id, {"status": "weapon_select"})

        await query.edit_message_text(
            f"⚔️ <b>WAR ACCEPTED!</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🥊 {war_data['challenger_name']} vs {war_data['target_name']}\n"
            f"💰 Total pot: {format_coins(war_data['amount'] * 2)}\n\n"
            f"⚔️ Both fighters, check your DM to select weapons!\n"
            f"<i>Waiting for both to pick...</i>",
            parse_mode="HTML",
            reply_markup=None
        )

        # Send weapon select to both via DM
        challenger_data = await get_user(war_data["challenger_id"], group_id)
        target_data2 = await get_user(war_data["target_id"], group_id)

        try:
            await context.bot.send_message(
                chat_id=war_data["challenger_id"],
                text=f"⚔️ <b>War vs {war_data['target_name']}</b>\nSelect your weapon:",
                parse_mode="HTML",
                reply_markup=weapon_select_keyboard(war_id, challenger_data.get("inventory", {}), "challenger")
            )
        except Exception:
            pass

        try:
            await context.bot.send_message(
                chat_id=war_data["target_id"],
                text=f"⚔️ <b>War vs {war_data['challenger_name']}</b>\nSelect your weapon:",
                parse_mode="HTML",
                reply_markup=weapon_select_keyboard(war_id, target_data2.get("inventory", {}), "target")
            )
        except Exception:
            pass

    elif data.startswith("war_decline_"):
        war_id = data.replace("war_decline_", "")
        war_data = await get_war(war_id)
        if not war_data or war_data["status"] != "pending":
            return
        if user.id != war_data["target_id"]:
            await query.answer("❌ Not your challenge!", show_alert=True)
            return

        await delete_war(war_id)
        # Refund challenger
        u = await get_user(war_data["challenger_id"], group_id)
        await update_user(war_data["challenger_id"], group_id, {"balance": u["balance"] + war_data["amount"]})

        await query.edit_message_text(
            f"❌ <b>{war_data['target_name']}</b> declined the war challenge.\n"
            f"💰 {format_coins(war_data['amount'])} refunded to {war_data['challenger_name']}.",
            parse_mode="HTML"
        )

    # Weapon select
    elif data.startswith("war_weapon_"):
        parts = data.split("_")
        war_id = parts[2]
        side = parts[3]
        weapon_key = "_".join(parts[4:])

        war_data = await get_war(war_id)
        if not war_data or war_data["status"] != "weapon_select":
            await query.edit_message_text("⚠️ War is no longer active.")
            return

        # Verify correct user
        if side == "challenger" and user.id != war_data["challenger_id"]:
            await query.answer("❌ Not your war!", show_alert=True)
            return
        if side == "target" and user.id != war_data["target_id"]:
            await query.answer("❌ Not your war!", show_alert=True)
            return

        if weapon_key not in SHOP_ITEMS:
            await query.answer("❌ Invalid weapon!", show_alert=True)
            return

        field = "challenger_weapon" if side == "challenger" else "target_weapon"
        await update_war(war_id, {field: weapon_key})
        await query.edit_message_text(
            f"✅ Weapon selected! Waiting for opponent...\n"
            f"<i>Your choice is hidden until the battle ends!</i>",
            parse_mode="HTML"
        )

        # Check if both selected
        war_data = await get_war(war_id)
        if war_data["challenger_weapon"] and war_data["target_weapon"]:
            await resolve_war(war_id, group_id, context)

    # Buy weapon redirect
    elif data.startswith("war_buyweapon_"):
        await query.answer(
            "Visit /shop in the group to buy weapons, then come back!",
            show_alert=True
        )

    # Coin flip
    elif data.startswith("war_flip_"):
        parts = data.split("_")
        war_id = parts[2]
        choice = parts[3]

        war_data = await get_war(war_id)
        if not war_data or war_data["status"] != "coin_flip":
            return

        if user.id not in [war_data["challenger_id"], war_data["target_id"]]:
            await query.answer("❌ Not your war!", show_alert=True)
            return

        # Store choice
        if user.id == war_data["challenger_id"] and not war_data.get("challenger_flip"):
            await update_war(war_id, {"challenger_flip": choice})
        elif user.id == war_data["target_id"] and not war_data.get("target_flip"):
            await update_war(war_id, {"target_flip": choice})
        else:
            await query.answer("You already chose!", show_alert=True)
            return

        await query.edit_message_text(
            f"✅ You chose <b>{choice.capitalize()}</b>! Waiting for opponent...",
            parse_mode="HTML"
        )

        war_data = await get_war(war_id)
        if war_data.get("challenger_flip") and war_data.get("target_flip"):
            await resolve_coin_flip(war_id, group_id, context)


async def resolve_war(war_id: str, group_id: int, context):
    war_data = await get_war(war_id)
    c_weapon_key = war_data["challenger_weapon"]
    t_weapon_key = war_data["target_weapon"]

    c_weapon = SHOP_ITEMS[c_weapon_key]
    t_weapon = SHOP_ITEMS[t_weapon_key]

    c_data = await get_user(war_data["challenger_id"], group_id)
    t_data = await get_user(war_data["target_id"], group_id)

    # Apply protection damage reduction (40% less damage if protected)
    now = time.time()
    c_protected = c_data.get("protected_until") and now < c_data["protected_until"]
    t_protected = t_data.get("protected_until") and now < t_data["protected_until"]

    c_damage = t_weapon["damage"]  # target attacks challenger
    t_damage = c_weapon["damage"]  # challenger attacks target

    if c_protected:
        c_damage = int(c_damage * 0.6)
    if t_protected:
        t_damage = int(t_damage * 0.6)

    amount = war_data["amount"]
    total_pot = amount * 2
    winner_prize = int(total_pot * 0.9)

    # Draw — same weapon
    if c_weapon_key == t_weapon_key:
        await update_war(war_id, {"status": "coin_flip"})
        try:
            flip_msg = await context.bot.send_message(
                chat_id=group_id,
                text=(
                    f"⚔️ <b>WAR RESULT — DRAW!</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"Both used <b>{c_weapon['name']}</b>!\n\n"
                    f"🪙 <b>COIN FLIP to decide the winner!</b>\n"
                    f"Both fighters, choose your side in DM!"
                ),
                parse_mode="HTML"
            )
            await update_war(war_id, {"flip_message_id": flip_msg.message_id})
        except Exception:
            pass

        # Send coin flip to both
        for uid, name in [(war_data["challenger_id"], war_data["challenger_name"]),
                          (war_data["target_id"], war_data["target_name"])]:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text="🪙 <b>Coin Flip!</b> Choose your side:",
                    parse_mode="HTML",
                    reply_markup=coin_flip_keyboard(war_id)
                )
            except Exception:
                pass
        return

    # Decide winner by damage dealt
    if t_damage >= c_damage:
        winner_id = war_data["challenger_id"]
        winner_name = war_data["challenger_name"]
        loser_id = war_data["target_id"]
        loser_name = war_data["target_name"]
        winner_weapon = c_weapon["name"]
        loser_weapon = t_weapon["name"]
        w_damage = t_damage
        l_damage = c_damage
    else:
        winner_id = war_data["target_id"]
        winner_name = war_data["target_name"]
        loser_id = war_data["challenger_id"]
        loser_name = war_data["challenger_name"]
        winner_weapon = t_weapon["name"]
        loser_weapon = c_weapon["name"]
        w_damage = c_damage
        l_damage = t_damage

    await finish_war(
        war_id, group_id, context,
        winner_id, winner_name, loser_id, loser_name,
        winner_weapon, loser_weapon, w_damage, l_damage,
        winner_prize, amount, is_flip=False
    )


async def resolve_coin_flip(war_id: str, group_id: int, context):
    war_data = await get_war(war_id)
    result = random.choice(["heads", "tails"])

    c_choice = war_data["challenger_flip"]
    t_choice = war_data["target_flip"]

    amount = war_data["amount"]
    total_pot = amount * 2
    winner_prize = int(total_pot * 0.9)

    if c_choice == result:
        winner_id = war_data["challenger_id"]
        winner_name = war_data["challenger_name"]
        loser_id = war_data["target_id"]
        loser_name = war_data["target_name"]
    else:
        winner_id = war_data["target_id"]
        winner_name = war_data["target_name"]
        loser_id = war_data["challenger_id"]
        loser_name = war_data["challenger_name"]

    c_weapon = SHOP_ITEMS.get(war_data["challenger_weapon"], {}).get("name", "Unknown")
    t_weapon = SHOP_ITEMS.get(war_data["target_weapon"], {}).get("name", "Unknown")

    try:
        await context.bot.send_message(
            chat_id=group_id,
            text=(
                f"🪙 <b>COIN FLIP RESULT!</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Result: <b>{result.capitalize()}</b>!\n\n"
                f"🏆 Winner: <b>{winner_name}</b>\n"
                f"💸 Loser: <b>{loser_name}</b>\n\n"
                f"💰 {winner_name} wins {format_coins(winner_prize)}!\n"
                f"💸 {loser_name} lost {format_coins(amount)}!"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await finish_war(
        war_id, group_id, context,
        winner_id, winner_name, loser_id, loser_name,
        c_weapon, t_weapon, 0, 0,
        winner_prize, amount, is_flip=True
    )


async def finish_war(
    war_id, group_id, context,
    winner_id, winner_name, loser_id, loser_name,
    winner_weapon, loser_weapon, w_damage, l_damage,
    winner_prize, amount, is_flip=False
):
    # Update balances
    winner_data = await get_user(winner_id, group_id)
    loser_data = await get_user(loser_id, group_id)

    new_winner_bal = winner_data["balance"] + winner_prize
    await update_user(winner_id, group_id, {
        "balance": new_winner_bal,
        "kills": winner_data.get("kills", 0) + 1,
        "war_streak": winner_data.get("war_streak", 0) + 1
    })
    await update_user(loser_id, group_id, {
        "war_streak": 0
    })

    # Streak bonus message
    streak = winner_data.get("war_streak", 0) + 1
    streak_msg = ""
    if streak == 3:
        streak_msg = "\n🔥 <b>3 Win Streak!</b> +10% loot bonus active!"
    elif streak == 5:
        streak_msg = "\n🔥 <b>5 Win Streak!</b> +20% loot bonus active!"
    elif streak == 10:
        streak_msg = "\n👑 <b>LEGENDARY 10 Win Streak!</b>"

    # Check wanted
    wanted_msg = await check_wanted(winner_id, group_id, winner_name)

    # Save history
    await save_war_history({
        "group_id": group_id,
        "winner_id": winner_id,
        "winner_name": winner_name,
        "loser_id": loser_id,
        "loser_name": loser_name,
        "winner_weapon": winner_weapon,
        "loser_weapon": loser_weapon,
        "winner_damage": w_damage,
        "loser_damage": l_damage,
        "amount": amount,
        "winner_amount": winner_prize,
        "is_flip": is_flip,
        "timestamp": time.time()
    })

    await delete_war(war_id)

    if not is_flip:
        result_text = (
            f"⚔️ <b>WAR RESULT!</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏆 Winner: <b>{winner_name}</b>\n"
            f"   Weapon: {winner_weapon} | DMG: {w_damage}\n\n"
            f"💀 Loser: <b>{loser_name}</b>\n"
            f"   Weapon: {loser_weapon} | DMG: {l_damage}\n\n"
            f"💰 {winner_name} wins {format_coins(winner_prize)}!\n"
            f"💸 {loser_name} lost {format_coins(amount)}!"
            f"{streak_msg}"
        )
        if wanted_msg:
            result_text += f"\n\n{wanted_msg}"

        try:
            await context.bot.send_message(
                chat_id=group_id,
                text=result_text,
                parse_mode="HTML"
            )
        except Exception:
            pass


async def check_wanted(user_id: int, group_id: int, username: str) -> str:
    """Check if user crossed 10 kills today and mark as wanted."""
    from database import db
    wanted_col = db["wanted"]
    today = int(time.time() // 86400)

    rec = await wanted_col.find_one({"user_id": user_id, "group_id": group_id, "day": today})
    if rec:
        kills_today = rec["kills"] + 1
        await wanted_col.update_one(
            {"user_id": user_id, "group_id": group_id, "day": today},
            {"$set": {"kills": kills_today}}
        )
    else:
        kills_today = 1
        await wanted_col.insert_one({
            "user_id": user_id,
            "group_id": group_id,
            "day": today,
            "username": username,
            "kills": 1
        })

    if kills_today == 10:
        bounty = 500
        return f"🚨 <b>{username} is now WANTED!</b> 10 kills today!\n💰 Bounty: {format_coins(bounty)} for whoever kills them!"
    return ""


async def warlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    stats = await get_war_stats(user.id, group_id)

    if stats["total"] == 0:
        await update.message.reply_text("⚔️ You haven't fought any wars yet!")
        return

    await update.message.reply_text(
        f"⚔️ <b>{user.first_name}'s War Log</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏆 Wins: {stats['wins']}  💀 Losses: {stats['losses']}\n"
        f"📊 Total Wars: {stats['total']}\n"
        f"💰 Total Earned: {format_coins(stats['total_earned'])}\n"
        f"💸 Total Lost: {format_coins(stats['total_lost'])}\n"
        f"🥇 Biggest Win: {format_coins(stats['biggest_win'])}",
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
        text += f"{i}. <b>{r['username']}</b> — {r['kills']} kills today 🔫\n"
    text += "\n💰 Bounty: 500 coins for killing a wanted player!"

    await update.message.reply_text(text, parse_mode="HTML")
