import time
from telegram import Update
from telegram.ext import ContextTypes
from models.group import is_economy_open
from config import OWNER_ID


def time_remaining(last_time, cooldown: int) -> int:
    if last_time is None:
        return 0
    elapsed = time.time() - last_time
    remaining = cooldown - elapsed
    return max(0, int(remaining))


def format_time(seconds: int) -> str:
    if seconds <= 0:
        return "now"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs and not hours:
        parts.append(f"{secs}s")
    return " ".join(parts)


def format_coins(amount) -> str:
    return f"🪙 {int(amount):,}"


async def check_economy(update: Update) -> bool:
    group_id = update.effective_chat.id
    open_status = await is_economy_open(group_id)
    if not open_status:
        await update.message.reply_text("❌ Economy is currently closed in this group.")
    return open_status


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if user_id == OWNER_ID:
        return True
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ["administrator", "creator"]


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns (user_id, username) of target from reply or args."""
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        return target.id, target.first_name
    if context.args and len(context.args) >= 1:
        try:
            uid = int(context.args[0])
            return uid, str(uid)
        except ValueError:
            pass
    return None, None
