import time
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import fmt, check_economy
from config import BANK_INTEREST_RATE, LOAN_MAX, LOAN_INTEREST_RATE, BANK_MIN_DEPOSIT


async def _apply_interest(data, user_id, group_id):
    now = time.time(); updates = {}
    if data["bank_balance"] > 0 and data.get("bank_deposited_at"):
        days = (now - data["bank_deposited_at"]) / 86400
        if days >= 1:
            fd = int(days); interest = int(data["bank_balance"] * BANK_INTEREST_RATE * fd)
            updates["bank_balance"] = data["bank_balance"] + interest
            updates["bank_deposited_at"] = data["bank_deposited_at"] + fd * 86400
    if data["loan"] > 0 and data.get("loan_taken_at"):
        days = (now - data["loan_taken_at"]) / 86400
        if days >= 1:
            fd = int(days); interest = int(data["loan"] * LOAN_INTEREST_RATE * fd)
            updates["loan"] = data["loan"] + interest
            updates["loan_taken_at"] = data["loan_taken_at"] + fd * 86400
    if updates:
        await update_user(user_id, group_id, updates)
        data.update(updates)
    return data


async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user; gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)
    data = await _apply_interest(data, u.id, gid)
    await update.message.reply_text(
        f"""🏦 <b>{u.first_name}'s Bank</b>
━━━━━━━━━━━━━━━
💰 <b>Wallet:</b> {fmt(data['balance'])}
🏦 <b>Bank:</b> {fmt(data['bank_balance'])}
📈 <b>Interest:</b> +10% daily
━━━━━━━━━━━━━━━
💸 <b>Loan:</b> {fmt(data['loan'])}
📉 <b>Loan Rate:</b> 5% daily
🔒 <b>Min Deposit:</b> {fmt(BANK_MIN_DEPOSIT)}""", parse_mode="HTML")


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user; gid = update.effective_chat.id
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ <code>/deposit [amount]</code>", parse_mode="HTML"); return
    data = await get_user(u.id, gid, u.first_name)
    data = await _apply_interest(data, u.id, gid)
    if data["balance"] < BANK_MIN_DEPOSIT:
        await update.message.reply_text(f"❌ Need at least {fmt(BANK_MIN_DEPOSIT)} in wallet to deposit!", parse_mode="HTML"); return
    if data["balance"] < amount:
        await update.message.reply_text(f"❌ Not enough! You have {fmt(data['balance'])}", parse_mode="HTML"); return
    nb = data["bank_balance"] + amount
    await update_user(u.id, gid, {"balance": data["balance"]-amount, "bank_balance": nb, "bank_deposited_at": data.get("bank_deposited_at") or time.time()})
    await update.message.reply_text(
        f"""📥 <b>Deposited!</b>
💸 <b>Amount:</b> {fmt(amount)}
🏦 <b>Bank Balance:</b> {fmt(nb)}
👛 <b>Wallet:</b> {fmt(data['balance']-amount)}
📈 <b>Earning 10% daily!</b>""", parse_mode="HTML")


async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user; gid = update.effective_chat.id
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ <code>/withdraw [amount]</code>", parse_mode="HTML"); return
    data = await get_user(u.id, gid, u.first_name)
    data = await _apply_interest(data, u.id, gid)
    if data["bank_balance"] < amount:
        await update.message.reply_text(f"❌ Bank has {fmt(data['bank_balance'])}", parse_mode="HTML"); return
    nb = data["bank_balance"] - amount
    await update_user(u.id, gid, {"balance": data["balance"]+amount, "bank_balance": nb})
    await update.message.reply_text(
        f"""📤 <b>Withdrawn!</b>
💸 <b>Amount:</b> {fmt(amount)}
👛 <b>Wallet:</b> {fmt(data['balance']+amount)}
🏦 <b>Bank:</b> {fmt(nb)}""", parse_mode="HTML")


async def loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user; gid = update.effective_chat.id
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(f"❌ <code>/loan [amount]</code>\n<b>Max:</b> {fmt(LOAN_MAX)}", parse_mode="HTML"); return
    if amount <= 0 or amount > LOAN_MAX:
        await update.message.reply_text(f"❌ Max loan is {fmt(LOAN_MAX)}", parse_mode="HTML"); return
    data = await get_user(u.id, gid, u.first_name)
    if data["loan"] > 0:
        await update.message.reply_text(f"❌ You have an active loan of {fmt(data['loan'])}!\nUse /repay first.", parse_mode="HTML"); return
    nb = data["balance"] + amount
    await update_user(u.id, gid, {"balance": nb, "loan": amount, "loan_taken_at": time.time()})
    await update.message.reply_text(
        f"""🏧 <b>Loan Approved!</b>
💸 <b>+{fmt(amount)}</b>
👛 <b>Wallet:</b> {fmt(nb)}
📉 <b>5% interest daily</b> — pay fast!""", parse_mode="HTML")


async def repay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update): return
    u = update.effective_user; gid = update.effective_chat.id
    data = await get_user(u.id, gid, u.first_name)
    data = await _apply_interest(data, u.id, gid)
    if data["loan"] <= 0:
        await update.message.reply_text("✅ No active loan!"); return
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(f"❌ <code>/repay [amount]</code>\n<b>Loan:</b> {fmt(data['loan'])}", parse_mode="HTML"); return
    if data["balance"] < amount:
        await update.message.reply_text(f"❌ Not enough! You have {fmt(data['balance'])}", parse_mode="HTML"); return
    repaid = min(amount, data["loan"])
    new_loan = data["loan"] - repaid
    ud = {"balance": data["balance"]-repaid, "loan": new_loan}
    if new_loan == 0: ud["loan_taken_at"] = None
    await update_user(u.id, gid, ud)
    status = "✅ <b>Loan fully repaid!</b>" if new_loan == 0 else f"💸 <b>Remaining:</b> {fmt(new_loan)}"
    await update.message.reply_text(
        f"""💳 <b>Repaid {fmt(repaid)}</b>
👛 <b>Wallet:</b> {fmt(data['balance']-repaid)}
{status}""", parse_mode="HTML")
