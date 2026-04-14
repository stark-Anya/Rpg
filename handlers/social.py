import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import fmt, get_target_user, send_with_image
from config import PROPOSE_TAX, DIVORCE_COST, IMG_PROPOSE, IMG_MARRY, IMG_DIVORCE

COUPLE_MESSAGES = [
    "💑 The stars aligned and brought <b>{u1}</b> and <b>{u2}</b> together! ✨",
    "💘 Cupid's arrow struck <b>{u1}</b> and <b>{u2}</b>! 🏹",
    "🌹 <b>{u1}</b> and <b>{u2}</b> are today's soulmates! 💕",
    "💫 The universe chose <b>{u1}</b> and <b>{u2}</b>! 🌟",
    "🎯 <b>{u1}</b> and <b>{u2}</b> — a dynamic duo! 🌸",
]
CRUSH_MESSAGES = [
    "💓 <b>{u1}</b> has a secret crush on <b>{u2}</b>! 😳",
    "😍 <b>{u1}</b> can't stop thinking about <b>{u2}</b>! 💭",
    "💌 <b>{u1}</b> sent a love letter to <b>{u2}</b>! 📝",
    "🌹 <b>{u1}</b> left roses at <b>{u2}</b>'s door! 👀",
    "💘 <b>{u1}</b> blushes every time they see <b>{u2}</b>! 🥰",
]
LOVE_MESSAGES = [
    "❤️ <b>{u1}</b> loves <b>{u2}</b> to the moon and back! 🌙",
    "💞 The love between <b>{u1}</b> and <b>{u2}</b> could move mountains! 🏔️",
    "💖 <b>{u1}</b> and <b>{u2}</b> share an unbreakable bond! 🔗",
    "🥰 <b>{u1}</b> whispered 'I love you' to <b>{u2}</b>! 💬",
    "💝 <b>{u1}</b> + <b>{u2}</b> = Forever! 📖",
]


async def propose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    if not target_id:
        await update.message.reply_text("❌ Reply to a user to propose!")
        return
    if target_id == user.id:
        await update.message.reply_text("❌ You can't propose to yourself! 😂")
        return

    proposer = await get_user(user.id, group_id, user.first_name)
    if proposer.get("married_to"):
        await update.message.reply_text("❌ You're already married! Use /divorce first.")
        return

    target = await get_user(target_id, group_id, target_name)
    if target.get("married_to"):
        await update.message.reply_text(f"❌ <b>{target_name}</b> is already married!", parse_mode="HTML")
        return

    tax = int(proposer["balance"] * PROPOSE_TAX)
    if proposer["balance"] < tax:
        await update.message.reply_text(
            f"❌ Not enough coins!\nProposal tax: {fmt(tax)} (5% of balance)",
            parse_mode="HTML"
        )
        return

    from database import db
    proposals_col = db["proposals"]
    await proposals_col.delete_many({"proposer_id": user.id, "group_id": group_id})
    result = await proposals_col.insert_one({
        "proposer_id": user.id,
        "proposer_name": user.first_name,
        "target_id": target_id,
        "target_name": target_name,
        "tax": tax,
        "group_id": group_id
    })
    prop_id = str(result.inserted_id)

    text = f"""💍 <b>{user.first_name}</b> proposes to <b>{target_name}</b>!
━━━━━━━━━━━━━━━
💰 Tax: {fmt(tax)} (5%)

<b>{target_name}</b>, will you accept? 💕"""

    # Fixed: pass update when available
    await send_with_image(
        update, group_id, IMG_PROPOSE, text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💍 Accept", callback_data=f"prop_accept_{prop_id}"),
            InlineKeyboardButton("💔 Decline", callback_data=f"prop_decline_{prop_id}")
        ]])
    )


async def propose_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    group_id = update.effective_chat.id
    data = query.data

    from database import db
    from bson import ObjectId
    proposals_col = db["proposals"]

    if data.startswith("prop_accept_"):
        prop_id = data[len("prop_accept_"):]
        prop = await proposals_col.find_one({"_id": ObjectId(prop_id)})
        if not prop:
            await query.answer("💔 Proposal expired!", show_alert=True)
            return
        if user.id != prop["target_id"]:
            await query.answer("❌ Not your proposal!", show_alert=True)
            return

        proposer = await get_user(prop["proposer_id"], group_id, prop["proposer_name"])
        if proposer["balance"] < prop["tax"]:
            await query.answer("❌ Proposer no longer has enough coins!", show_alert=True)
            await proposals_col.delete_one({"_id": ObjectId(prop_id)})
            return

        await update_user(prop["proposer_id"], group_id, {
            "balance": proposer["balance"] - prop["tax"],
            "married_to": prop["target_id"]
        })
        await update_user(prop["target_id"], group_id, {"married_to": prop["proposer_id"]})
        await proposals_col.delete_one({"_id": ObjectId(prop_id)})

        text = f"""💍 <b>Married!</b>
━━━━━━━━━━━━━━━
🎉 <b>{prop['proposer_name']}</b> &amp; <b>{prop['target_name']}</b>
💰 Tax paid: {fmt(prop['tax'])}
❤️ Congratulations!"""

        try:
            await query.delete_message()
        except Exception:
            pass
        await send_with_image(context.bot, group_id, IMG_MARRY, text)

    elif data.startswith("prop_decline_"):
        prop_id = data[len("prop_decline_"):]
        prop = await proposals_col.find_one({"_id": ObjectId(prop_id)})
        if not prop:
            await query.answer("Already handled!", show_alert=True)
            return
        if user.id != prop["target_id"]:
            await query.answer("❌ Not your proposal!", show_alert=True)
            return

        await proposals_col.delete_one({"_id": ObjectId(prop_id)})
        try:
            await query.edit_message_caption(
                caption=f"""💔 <b>{prop['target_name']}</b> declined!
😢 <b>{prop['proposer_name']}</b>'s heart is broken...""",
                parse_mode="HTML",
                reply_markup=None
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=f"""💔 <b>{prop['target_name']}</b> declined!
😢 <b>{prop['proposer_name']}</b>'s heart is broken...""",
                    parse_mode="HTML",
                    reply_markup=None
                )
            except Exception:
                pass


async def marry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if not data.get("married_to"):
        await update.message.reply_text(
            f"""💔 <b>{user.first_name}</b> is single!
Use /propose @user to find your match! 💍""",
            parse_mode="HTML"
        )
        return

    partner = await get_user(data["married_to"], group_id)
    await update.message.reply_text(
        f"💑 <b>{user.first_name}</b> is married to <b>{partner.get('username', 'Unknown')}</b>! ❤️",
        parse_mode="HTML"
    )


async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if not data.get("married_to"):
        await update.message.reply_text("❌ You're not married!")
        return
    if data["balance"] < DIVORCE_COST:
        await update.message.reply_text(
            f"❌ Divorce costs {fmt(DIVORCE_COST)}!\nWallet: {fmt(data['balance'])}",
            parse_mode="HTML"
        )
        return

    partner = await get_user(data["married_to"], group_id)
    partner_name = partner.get("username", "Unknown")
    new_balance = data["balance"] - DIVORCE_COST

    await update_user(user.id, group_id, {"balance": new_balance, "married_to": None})
    await update_user(data["married_to"], group_id, {"married_to": None})

    text = f"""💔 <b>Divorced!</b>
━━━━━━━━━━━━━━━
<b>{user.first_name}</b> and <b>{partner_name}</b> split up.
💸 Cost: {fmt(DIVORCE_COST)}
👛 Balance: {fmt(new_balance)}"""

    await send_with_image(update, update.effective_chat.id, IMG_DIVORCE, text)


async def couple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from models.user import get_all_users
    group_id = update.effective_chat.id
    users = await get_all_users(group_id)

    if len(users) < 2:
        await update.message.reply_text("❌ Not enough users!")
        return

    pair = random.sample(users, 2)
    msg  = random.choice(COUPLE_MESSAGES).format(u1=pair[0]["username"], u2=pair[1]["username"])
    await update.message.reply_text(msg, parse_mode="HTML")


async def crush(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    if not target_id:
        from models.user import get_all_users
        users  = await get_all_users(group_id)
        others = [u for u in users if u["user_id"] != user.id]
        if not others:
            await update.message.reply_text("❌ No one else here!")
            return
        target_name = random.choice(others)["username"]

    msg = random.choice(CRUSH_MESSAGES).format(u1=user.first_name, u2=target_name)
    await update.message.reply_text(msg, parse_mode="HTML")


async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    if not target_id:
        from models.user import get_all_users
        users  = await get_all_users(group_id)
        others = [u for u in users if u["user_id"] != user.id]
        if not others:
            await update.message.reply_text("❌ No one else here!")
            return
        target_name = random.choice(others)["username"]

    msg = random.choice(LOVE_MESSAGES).format(u1=user.first_name, u2=target_name)
    await update.message.reply_text(msg, parse_mode="HTML")
