import time
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import fmt, check_economy
from config import BANK_INTEREST_RATE, LOAN_MAX, LOAN_INTEREST_RATE, BANK_MIN_DEPOSIT


async def _apply_interest(data, user_id, group_id):
    now = time.time()
    updates = {}

    if data["bank_balance"] > 0 and data.get("bank_deposited_at"):
        days = (now - data["bank_deposited_at"]) / 86400
        if days >= 1:
            fd = int(days)
            interest = int(data["bank_balance"] * BANK_INTEREST_RATE * fd)
            updates["bank_balance"] = data["bank_balance"] + interest
            updates["bank_deposited_at"] = data["bank_deposited_at"] + fd * 86400

    if data["loan"] > 0 and data.get("loan_taken_at"):
        days = (now - data["loan_taken_at"]) / 86400
        if days >= 1:
            fd = int(days)
            interest = int(data["loan"] * LOAN_INTEREST_RATE * fd)
            updates["loan"] = data["loan"] + interest
            updates["loan_taken_at"] = data["loan_taken_at"] + fd * 86400

    if updates:
        await update_user(user_id, group_id, updates)
        data.update(updates)
    return data


async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)
    data = await _apply_interest(data, u.id, gid)

    loan_line = f"\n💸 <b>Loan:</b> {fmt(data['loan'])} <i>(10%/day)</i>" if data["loan"] > 0 else "\n✅ <b>No active loan</b>"

    await update.message.reply_text(
        f"""🏦 <b>{u.first_name}'s Bank</b>
━━━━━━━━━━━━━━━
👛 Wallet — {fmt(data['balance'])}
🏦 Bank — {fmt(data['bank_balance'])} <i>(+5%/day)</i>
{loan_line}
━━━━━━━━━━━━━━━
📌 Min deposit: {fmt(BANK_MIN_DEPOSIT)}
📌 Max loan: {fmt(LOAN_MAX)}""",
        parse_mode="HTML"
    )


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id

    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Usage: <code>/deposit [amount]</code>", parse_mode="HTML")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    data = await get_user(u.id, gid, u.first_name)
    data = await _apply_interest(data, u.id, gid)

    if amount < BANK_MIN_DEPOSIT:
        await update.message.reply_text(f"❌ Minimum deposit: {fmt(BANK_MIN_DEPOSIT)}", parse_mode="HTML")
        return
    if data["balance"] < amount:
        await update.message.reply_text(f"❌ Not enough! Wallet: {fmt(data['balance'])}", parse_mode="HTML")
        return

    new_bank = data["bank_balance"] + amount
    new_bal  = data["balance"] - amount
    deposited_at = data.get("bank_deposited_at") or time.time()

    await update_user(u.id, gid, {
        "balance": new_bal,
        "bank_balance": new_bank,
        "bank_deposited_at": deposited_at
    })

    await update.message.reply_text(
        f"""📥 <b>Deposited!</b>
━━━━━━━━━━━━━━━
💰 +{fmt(amount)} → Bank
👛 Wallet: {fmt(new_bal)}
🏦 Bank: {fmt(new_bank)}
📈 Earning 5% daily!""",
        parse_mode="HTML"
    )


async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id

    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Usage: <code>/withdraw [amount]</code>", parse_mode="HTML")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    data = await get_user(u.id, gid, u.first_name)
    data = await _apply_interest(data, u.id, gid)

    if data["bank_balance"] < amount:
        await update.message.reply_text(f"❌ Bank balance: {fmt(data['bank_balance'])}", parse_mode="HTML")
        return

    new_bank = data["bank_balance"] - amount
    new_bal  = data["balance"] + amount

    await update_user(u.id, gid, {"balance": new_bal, "bank_balance": new_bank})

    await update.message.reply_text(
        f"""📤 <b>Withdrawn!</b>
━━━━━━━━━━━━━━━
💰 +{fmt(amount)} → Wallet
👛 Wallet: {fmt(new_bal)}
🏦 Bank: {fmt(new_bank)}""",
        parse_mode="HTML"
    )


async def loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id

    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            f"❌ Usage: <code>/loan [amount]</code>\n📌 Max: {fmt(LOAN_MAX)}",
            parse_mode="HTML"
        )
        return

    if amount <= 0 or amount > LOAN_MAX:
        await update.message.reply_text(f"❌ Loan range: {fmt(1)} – {fmt(LOAN_MAX)}", parse_mode="HTML")
        return

    data = await get_user(u.id, gid, u.first_name)

    if data["loan"] > 0:
        await update.message.reply_text(
            f"❌ Active loan: {fmt(data['loan'])}\nUse /repay first!",
            parse_mode="HTML"
        )
        return

    new_bal = data["balance"] + amount
    await update_user(u.id, gid, {"balance": new_bal, "loan": amount, "loan_taken_at": time.time()})

    await update.message.reply_text(
        f"""🏧 <b>Loan Approved!</b>
━━━━━━━━━━━━━━━
💸 +{fmt(amount)} added to wallet
👛 Wallet: {fmt(new_bal)}
⚠️ 10% interest per day — repay fast!""",
        parse_mode="HTML"
    )


async def repay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user
    gid = update.effective_chat.id

    data = await get_user(u.id, gid, u.first_name)
    data = await _apply_interest(data, u.id, gid)

    if data["loan"] <= 0:
        await update.message.reply_text("✅ No active loan!")
        return

    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            f"❌ Usage: <code>/repay [amount]</code>\n💸 Loan due: {fmt(data['loan'])}",
            parse_mode="HTML"
        )
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return
    if data["balance"] < amount:
        await update.message.reply_text(f"❌ Wallet: {fmt(data['balance'])}", parse_mode="HTML")
        return

    repaid   = min(amount, data["loan"])
    new_loan = data["loan"] - repaid
    new_bal  = data["balance"] - repaid

    ud = {"balance": new_bal, "loan": new_loan}
    if new_loan == 0:
        ud["loan_taken_at"] = None

    await update_user(u.id, gid, ud)

    status = "✅ Loan fully cleared!" if new_loan == 0 else f"📌 Remaining: {fmt(new_loan)}"
    await update.message.reply_text(
        f"""💳 <b>Repaid {fmt(repaid)}</b>
━━━━━━━━━━━━━━━
👛 Wallet: {fmt(new_bal)}
{status}""",
        parse_mode="HTML"
    )
