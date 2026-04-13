import time
from telegram import Update
from telegram.ext import ContextTypes
from models.group import is_economy_open
from config import OWNER_ID


def time_remaining(last_time, cooldown: int) -> int:
    if last_time is None:
        return 0
    elapsed = time.time() - last_time
    return max(0, int(cooldown - elapsed))


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


async def send_with_image(update_or_bot, chat_id, image_url: str, caption: str, reply_markup=None, parse_mode="HTML"):
    """Send message with image if available, else plain text."""
    try:
        if image_url:
            if hasattr(update_or_bot, 'message'):
                await update_or_bot.message.reply_photo(
                    photo=image_url,
                    caption=caption,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
            else:
                await update_or_bot.send_photo(
                    chat_id=chat_id,
                    photo=image_url,
                    caption=caption,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
        else:
            raise Exception("No image")
    except Exception:
        if hasattr(update_or_bot, 'message'):
            await update_or_bot.message.reply_text(
                caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        else:
            await update_or_bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
