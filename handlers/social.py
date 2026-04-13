import random
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import format_coins, get_target_user
from config import PROPOSE_TAX, DIVORCE_COST

COUPLE_MESSAGES = [
    "💑 The stars aligned and brought {u1} and {u2} together! A match made in heaven! ✨",
    "💘 Cupid's arrow struck {u1} and {u2}! They are today's perfect couple! 🏹",
    "🌹 {u1} and {u2} are today's soulmates! Love is in the air! 💕",
    "💫 The universe chose {u1} and {u2} to be together! What a pair! 🌟",
    "🎯 {u1} and {u2} — a dynamic duo! Romance is blooming! 🌸",
]

CRUSH_MESSAGES = [
    "💓 {u1} has a secret crush on {u2}! Awww! 😳",
    "😍 {u1} can't stop thinking about {u2}! Someone's in love! 💭",
    "💌 {u1} sent a love letter to {u2}! How sweet! 📝",
    "🌹 {u1} left roses at {u2}'s door anonymously... or did they? 👀",
    "💘 {u1} blushes every time they see {u2}! Cute! 🥰",
]

LOVE_MESSAGES = [
    "❤️ {u1} loves {u2} to the moon and back! 🌙",
    "💞 The love between {u1} and {u2} could move mountains! 🏔️",
    "💖 {u1} and {u2} share a bond that can't be broken! 🔗",
    "🥰 {u1} whispered 'I love you' to {u2}! So precious! 💬",
    "💝 {u1} + {u2} = Forever! A love story for the ages! 📖",
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
        await update.message.reply_text("❌ You are already married! Use /divorce first.")
        return

    target = await get_user(target_id, group_id, target_name)
    if target.get("married_to"):
        await update.message.reply_text(f"❌ {target_name} is already married!")
        return

    tax = int(proposer["balance"] * PROPOSE_TAX)
    if proposer["balance"] < tax:
        await update.message.reply_text(f"❌ Not enough coins! Proposal tax is {format_coins(tax)} (5% of your balance).")
        return

    new_balance = proposer["balance"] - tax
    await update_user(user.id, group_id, {
        "balance": new_balance,
        "married_to": target_id
    })
    await update_user(target_id, group_id, {"married_to": user.id})

    await update.message.reply_text(
        f"💍 <b>{user.first_name}</b> proposed to <b>{target_name}</b>!\n"
        f"🎉 They are now officially married!\n"
        f"💸 Proposal tax paid: {format_coins(tax)}\n"
        f"👛 {user.first_name}'s balance: {format_coins(new_balance)}\n\n"
        f"❤️ Congratulations to the happy couple!",
        parse_mode="HTML"
    )


async def marry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if not data.get("married_to"):
        await update.message.reply_text(
            f"💔 <b>{user.first_name}</b> is currently single!\n"
            f"Use /propose @user to get married! 💍",
            parse_mode="HTML"
        )
        return

    partner_id = data["married_to"]
    partner = await get_user(partner_id, group_id)

    await update.message.reply_text(
        f"💑 <b>{user.first_name}</b> is happily married to <b>{partner.get('username', 'Unknown')}</b>!\n"
        f"❤️ A beautiful couple!",
        parse_mode="HTML"
    )


async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    if not data.get("married_to"):
        await update.message.reply_text("❌ You are not married!")
        return

    if data["balance"] < DIVORCE_COST:
        await update.message.reply_text(
            f"❌ Divorce costs {format_coins(DIVORCE_COST)}!\n"
            f"💰 You have: {format_coins(data['balance'])}",
            parse_mode="HTML"
        )
        return

    partner_id = data["married_to"]
    partner = await get_user(partner_id, group_id)
    partner_name = partner.get("username", "Unknown")

    new_balance = data["balance"] - DIVORCE_COST
    await update_user(user.id, group_id, {
        "balance": new_balance,
        "married_to": None
    })
    await update_user(partner_id, group_id, {"married_to": None})

    await update.message.reply_text(
        f"💔 <b>{user.first_name}</b> divorced <b>{partner_name}</b>!\n"
        f"💸 Divorce cost: {format_coins(DIVORCE_COST)}\n"
        f"👛 Balance: {format_coins(new_balance)}\n\n"
        f"😢 It's over... but life goes on!",
        parse_mode="HTML"
    )


async def couple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from models.user import get_all_users
    group_id = update.effective_chat.id
    users = await get_all_users(group_id)

    if len(users) < 2:
        await update.message.reply_text("❌ Not enough users in this group for matchmaking!")
        return

    pair = random.sample(users, 2)
    u1 = pair[0]["username"]
    u2 = pair[1]["username"]
    msg = random.choice(COUPLE_MESSAGES).format(u1=f"<b>{u1}</b>", u2=f"<b>{u2}</b>")
    await update.message.reply_text(msg, parse_mode="HTML")


async def crush(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    if not target_id:
        from models.user import get_all_users
        users = await get_all_users(group_id)
        others = [u for u in users if u["user_id"] != user.id]
        if not others:
            await update.message.reply_text("❌ No one else in this group!")
            return
        target_name = random.choice(others)["username"]

    msg = random.choice(CRUSH_MESSAGES).format(
        u1=f"<b>{user.first_name}</b>",
        u2=f"<b>{target_name}</b>"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    target_id, target_name = await get_target_user(update, context)

    if not target_id:
        from models.user import get_all_users
        users = await get_all_users(group_id)
        others = [u for u in users if u["user_id"] != user.id]
        if not others:
            await update.message.reply_text("❌ No one else in this group!")
            return
        target_name = random.choice(others)["username"]

    msg = random.choice(LOVE_MESSAGES).format(
        u1=f"<b>{user.first_name}</b>",
        u2=f"<b>{target_name}</b>"
    )
    await update.message.reply_text(msg, parse_mode="HTML")
