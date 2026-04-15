import time
from telegram import Update
from telegram.ext import ContextTypes
from models.group import is_economy_open
from config import OWNER_ID, CURRENCY_SYMBOL


def time_remaining(last_time, cooldown: int) -> int:
    if last_time is None:
        return 0
    return max(0, int(cooldown - (time.time() - last_time)))


def format_time(seconds: int) -> str:
    if seconds <= 0:
        return "now"
    parts = []
    if seconds // 3600: parts.append(f"{seconds//3600}h")
    if (seconds % 3600) // 60: parts.append(f"{(seconds%3600)//60}m")
    if seconds % 60 and not seconds // 3600: parts.append(f"{seconds%60}s")
    return " ".join(parts)


def fmt(amount) -> str:
    return f"{CURRENCY_SYMBOL}{int(amount):,}"


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def is_sudo_or_owner(user_id: int) -> bool:
    """True if main owner OR sudo user."""
    if user_id == OWNER_ID:
        return True
    from models.sudo import is_sudo
    return await is_sudo(user_id)


async def check_economy(update: Update) -> bool:
    if update.effective_chat.type == "private":
        return True
    open_status = await is_economy_open(update.effective_chat.id)
    if not open_status:
        await update.message.reply_text("❌ Economy is closed in this group.")
    return open_status


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        return True
    from models.sudo import is_sudo
    if await is_sudo(user_id):
        return True
    member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    return member.status in ["administrator", "creator"]


async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        return t.id, t.first_name
    if context.args:
        try:
            return int(context.args[0]), str(context.args[0])
        except ValueError:
            pass
    return None, None


async def send_with_image(target, chat_id, image_url: str, text: str, reply_markup=None, parse_mode="HTML"):
    try:
        if image_url:
            if hasattr(target, 'message'):
                await target.message.reply_photo(photo=image_url, caption=text,
                    parse_mode=parse_mode, reply_markup=reply_markup)
            else:
                await target.send_photo(chat_id=chat_id, photo=image_url, caption=text,
                    parse_mode=parse_mode, reply_markup=reply_markup)
            return
    except Exception:
        pass
    if hasattr(target, 'message'):
        await target.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    else:
        await target.send_message(chat_id=chat_id, text=text,
            parse_mode=parse_mode, reply_markup=reply_markup)


def get_best_weapon(inventory: dict) -> tuple:
    from config import WEAPONS
    best_key, best_item, best_price = None, None, -1
    for key, data in inventory.items():
        if key in WEAPONS and data.get("qty", 0) > 0:
            item = WEAPONS[key]
            if item["price"] > best_price:
                best_price = item["price"]
                best_key = key
                best_item = item
    return best_key, best_item


def is_weapon_valid(weapon_data: dict) -> bool:
    if not weapon_data.get("expires_at"):
        return False
    return time.time() < weapon_data["expires_at"]
