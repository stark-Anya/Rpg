import time
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import check_economy, format_coins
from config import BANK_INTEREST_RATE, LOAN_MAX, LOAN_INTEREST_RATE


async def apply_bank_interest(data: dict) -> dict:
    """Calculate and apply pending bank interest and loan interest."""
    now = time.time()
    updates = {}

    # Bank interest
    if data["bank_balance"] > 0 and data.get("bank_deposited_at"):
        days_elapsed = (now - data["bank_deposited_at"]) / 86400
        if days_elapsed >= 1:
            full_days = int(days_elapsed)
            interest = int(data["bank_balance"] * BANK_INTEREST_RATE * full_days)
            updates["bank_balance"] = data["bank_balance"] + interest
            updates["bank_deposited_at"] = data["bank_deposited_at"] + (full_days * 86400)

    # Loan interest
    if data["loan"] > 0 and data.get("loan_taken_at"):
        days_elapsed = (now - data["loan_taken_at"]) / 86400
        if days_elapsed >= 1:
            full_days = int(days_elapsed)
            interest = int(data["loan"] * LOAN_INTEREST_RATE * full_days)
            updates["loan"] = data["loan"] + interest
            updates["loan_taken_at"] = data["loan_taken_at"] + (full_days * 86400)

    return updates


async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)

    # Apply pending interest
    interest_updates = await apply_bank_interest(data)
    if interest_updates:
        await update_user(user.id, group_id, interest_updates)
        data.update(interest_updates)

    bank_bal = data["bank_balance"]
    loan = data["loan"]

    text = (
        f"🏦 <b>{user.first_name}'s Bank</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Wallet: {format_coins(data['balance'])}\n"
        f"🏦 Bank Balance: {format_coins(bank_bal)}\n"
        f"📈 Daily Interest: +10% on deposits\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💸 Loan: {format_coins(loan)}\n"
        f"📉 Loan Interest: -5% daily\n"
        f"🏧 Max Loan: 🪙 1,000\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📥 /deposit [amount]\n"
        f"📤 /withdraw [amount]"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id

    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Usage: <code>/deposit [amount]</code>", parse_mode="HTML")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    data = await get_user(user.id, group_id, user.first_name)

    # Apply pending interest first
    interest_updates = await apply_bank_interest(data)
    if interest_updates:
        await update_user(user.id, group_id, interest_updates)
        data.update(interest_updates)

    if data["balance"] < amount:
        await update.message.reply_text(
            f"❌ Insufficient balance!\n💰 You have: {format_coins(data['balance'])}",
            parse_mode="HTML"
        )
        return

    new_balance = data["balance"] - amount
    new_bank = data["bank_balance"] + amount

    await update_user(user.id, group_id, {
        "balance": new_balance,
        "bank_balance": new_bank,
        "bank_deposited_at": data.get("bank_deposited_at") or time.time()
    })

    await update.message.reply_text(
        f"📥 Deposited {format_coins(amount)} to bank!\n"
        f"🏦 Bank Balance: {format_coins(new_bank)}\n"
        f"💰 Wallet: {format_coins(new_balance)}\n"
        f"📈 Earning 10% interest daily!",
        parse_mode="HTML"
    )


async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id

    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Usage: <code>/withdraw [amount]</code>", parse_mode="HTML")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return

    data = await get_user(user.id, group_id, user.first_name)

    # Apply pending interest first
    interest_updates = await apply_bank_interest(data)
    if interest_updates:
        await update_user(user.id, group_id, interest_updates)
        data.update(interest_updates)

    if data["bank_balance"] < amount:
        await update.message.reply_text(
            f"❌ Not enough in bank!\n🏦 Bank Balance: {format_coins(data['bank_balance'])}",
            parse_mode="HTML"
        )
        return

    new_balance = data["balance"] + amount
    new_bank = data["bank_balance"] - amount

    await update_user(user.id, group_id, {
        "balance": new_balance,
        "bank_balance": new_bank
    })

    await update.message.reply_text(
        f"📤 Withdrew {format_coins(amount)} from bank!\n"
        f"💰 Wallet: {format_coins(new_balance)}\n"
        f"🏦 Bank Balance: {format_coins(new_bank)}",
        parse_mode="HTML"
    )


async def loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id

    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            f"❌ Usage: <code>/loan [amount]</code>\nMax loan: 🪙 {LOAN_MAX:,}",
            parse_mode="HTML"
        )
        return

    if amount <= 0 or amount > LOAN_MAX:
        await update.message.reply_text(f"❌ Loan amount must be between 1 and {format_coins(LOAN_MAX)}!", parse_mode="HTML")
        return

    data = await get_user(user.id, group_id, user.first_name)

    if data["loan"] > 0:
        await update.message.reply_text(
            f"❌ You already have an active loan of {format_coins(data['loan'])}!\n"
            f"Use <code>/repay [amount]</code> to pay it back.",
            parse_mode="HTML"
        )
        return

    new_balance = data["balance"] + amount
    await update_user(user.id, group_id, {
        "balance": new_balance,
        "loan": amount,
        "loan_taken_at": time.time()
    })

    await update.message.reply_text(
        f"🏦 Loan approved!\n"
        f"💰 +{format_coins(amount)} added to wallet\n"
        f"📉 5% interest per day\n"
        f"⚠️ Repay with <code>/repay [amount]</code>",
        parse_mode="HTML"
    )


async def repay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id

    data = await get_user(user.id, group_id, user.first_name)

    # Apply pending loan interest
    interest_updates = await apply_bank_interest(data)
    if interest_updates:
        await update_user(user.id, group_id, interest_updates)
        data.update(interest_updates)

    if data["loan"] <= 0:
        await update.message.reply_text("✅ You have no active loan!")
        return

    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            f"❌ Usage: <code>/repay [amount]</code>\n"
            f"💸 Outstanding loan: {format_coins(data['loan'])}",
            parse_mode="HTML"
        )
        return

    if data["balance"] < amount:
        await update.message.reply_text(
            f"❌ Not enough coins!\n💰 You have: {format_coins(data['balance'])}",
            parse_mode="HTML"
        )
        return

    repay_amount = min(amount, data["loan"])
    new_loan = data["loan"] - repay_amount
    new_balance = data["balance"] - repay_amount

    update_data = {"balance": new_balance, "loan": new_loan}
    if new_loan == 0:
        update_data["loan_taken_at"] = None

    await update_user(user.id, group_id, update_data)

    status = "✅ Loan fully repaid!" if new_loan == 0 else f"💸 Remaining loan: {format_coins(new_loan)}"
    await update.message.reply_text(
        f"💳 Repaid {format_coins(repay_amount)}\n"
        f"💰 Wallet: {format_coins(new_balance)}\n"
        f"{status}",
        parse_mode="HTML"
    )
