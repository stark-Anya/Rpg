"""
/gift handler — send a flex item as a gift to another user.

Flow:
  1. /gift @user  or  /gift {userid}
     → Opens flex shop (inline buttons, price = item price + GIFT_SURCHARGE)
  2. User taps a flex item → item selected, stored in context.user_data
  3. Bot asks: "Write a message or send /skip"
  4. User types message OR sends /skip
  5. Bot shows confirm screen with [✅ Send Gift] [❌ Cancel]
  6. On confirm → deduct from sender, add to receiver inventory, notify both
"""

import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from models.user import get_user, update_user
from utils.helpers import fmt, send_with_image, is_weapon_valid
from config import FLEX_ITEMS, get_rarity, GIFT_SURCHARGE, IMG_GIFT

# Conversation states
AWAITING_MESSAGE = 1

FLEX_PER_ROW = 2


# ── Build flex keyboard for gifting ─────────────────────────────────────────

def gift_flex_keyboard(inventory_sender: dict, balance: int, page: int = 0):
    """Show all flex items. Price = item price + GIFT_SURCHARGE."""
    PER_PAGE = 8
    keys  = list(FLEX_ITEMS.keys())
    start = page * PER_PAGE
    chunk = keys[start:start + PER_PAGE]
    rows  = []

    for k in chunk:
        item       = FLEX_ITEMS[k]
        gift_price = item["price"] + GIFT_SURCHARGE
        can_buy    = balance >= gift_price

        if not can_buy:
            label = f"❌ {item['name'].split(' ',1)[1]} · {fmt(gift_price)}"
        else:
            label = f"{item['emoji']} {item['name'].split(' ',1)[1]} · {fmt(gift_price)}"

        rows.append([InlineKeyboardButton(label, callback_data=f"gift_item_{k}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"gift_page_{page-1}"))
    if start + PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"gift_page_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("❌ Cancel", callback_data="gift_cancel")])
    return InlineKeyboardMarkup(rows)


def confirm_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Send Gift", callback_data="gift_confirm"),
        InlineKeyboardButton("❌ Cancel",    callback_data="gift_cancel")
    ]])


# ── /gift entry point ────────────────────────────────────────────────────────

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    group_id = update.effective_chat.id

    # Get target
    tid, tname = None, None
    if update.message.reply_to_message:
        t     = update.message.reply_to_message.from_user
        tid   = t.id
        tname = t.first_name
    elif context.args:
        try:
            tid   = int(context.args[0])
            tname = str(tid)
            # Try to get real name
            try:
                chat  = await context.bot.get_chat(tid)
                tname = chat.first_name or tname
            except Exception:
                pass
        except ValueError:
            pass

    if not tid:
        await update.message.reply_text(
            "❌ Usage: <code>/gift {userid}</code> or reply to someone",
            parse_mode="HTML"
        )
        return

    if tid == user.id:
        await update.message.reply_text("❌ You can't gift yourself!")
        return

    udata = await get_user(user.id, group_id, user.first_name)

    # Store in user_data for conversation
    context.user_data["gift"] = {
        "sender_id":   user.id,
        "sender_name": user.first_name,
        "target_id":   tid,
        "target_name": tname,
        "group_id":    group_id,
        "item_key":    None,
        "message":     None,
    }

    text = f"""🎁 <b>Gift Shop</b>
━━━━━━━━━━━━━━━
👤 Gifting to: <b>{tname}</b>
👛 Your Wallet: <b>{fmt(udata['balance'])}</b>
📦 Gift charge: +{fmt(GIFT_SURCHARGE)} per item
━━━━━━━━━━━━━━━
Select a flex item to gift 👇"""

    await send_with_image(
        update, group_id, IMG_GIFT, text,
        reply_markup=gift_flex_keyboard(udata.get("inventory", {}), udata["balance"])
    )


# ── Callback: page navigation & item selection ───────────────────────────────

async def gift_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    user     = update.effective_user
    group_id = update.effective_chat.id
    data     = query.data

    gift_data = context.user_data.get("gift")

    async def edit(text, kb):
        try:
            await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            try:
                await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb)
            except Exception:
                pass

    # Only the sender can interact
    if gift_data and user.id != gift_data["sender_id"]:
        await query.answer("❌ This is not your gift session!", show_alert=True)
        return

    # ── Cancel ──────────────────────────────────────────────────
    if data == "gift_cancel":
        await query.answer()
        context.user_data.pop("gift", None)
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ── Page navigation ─────────────────────────────────────────
    if data.startswith("gift_page_"):
        await query.answer()
        page  = int(data.split("_")[-1])
        udata = await get_user(user.id, group_id, user.first_name)
        text  = f"""🎁 <b>Gift Shop</b>
━━━━━━━━━━━━━━━
👤 Gifting to: <b>{gift_data['target_name']}</b>
👛 Your Wallet: <b>{fmt(udata['balance'])}</b>
📦 Gift charge: +{fmt(GIFT_SURCHARGE)} per item
━━━━━━━━━━━━━━━
Select a flex item to gift 👇"""
        await edit(text, gift_flex_keyboard(udata.get("inventory", {}), udata["balance"], page))
        return

    # ── Item selected ───────────────────────────────────────────
    if data.startswith("gift_item_"):
        ikey = data[len("gift_item_"):]
        item = FLEX_ITEMS.get(ikey)
        if not item:
            await query.answer("❌ Item not found!", show_alert=True)
            return

        udata      = await get_user(user.id, group_id, user.first_name)
        gift_price = item["price"] + GIFT_SURCHARGE

        if udata["balance"] < gift_price:
            await query.answer("📉 You can't afford this gift!", show_alert=True)
            return

        await query.answer()
        # Save selected item
        gift_data["item_key"] = ikey
        context.user_data["gift"] = gift_data

        text = f"""🎁 <b>Gift Selected!</b>
━━━━━━━━━━━━━━━
{item['emoji']} <b>{item['name']}</b>
💰 Cost: {fmt(gift_price)} ({fmt(item['price'])} + {fmt(GIFT_SURCHARGE)} gift charge)
🌟 Rarity: {get_rarity(item['price'])}
━━━━━━━━━━━━━━━
💬 <b>Write a message for {gift_data['target_name']}</b>
Or send <code>/skip</code> to skip the message."""

        await edit(text, InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭️ Skip Message", callback_data="gift_skipmsg")
        ]]))
        return

    # ── Skip message via button ─────────────────────────────────
    if data == "gift_skipmsg":
        if not gift_data or not gift_data.get("item_key"):
            await query.answer("❌ No item selected!", show_alert=True)
            return

        await query.answer()
        gift_data["message"] = None
        context.user_data["gift"] = gift_data
        await _show_confirm(query, context, gift_data, edit_fn=edit)
        return

    # ── Final confirm ───────────────────────────────────────────
    if data == "gift_confirm":
        if not gift_data or not gift_data.get("item_key"):
            await query.answer("❌ Session expired!", show_alert=True)
            return

        await query.answer()
        await _execute_gift(query, context, gift_data)
        return


# ── Text message handler (for gift message input) ────────────────────────────

async def gift_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captures the gift message typed by sender."""
    gift_data = context.user_data.get("gift")
    if not gift_data or not gift_data.get("item_key"):
        return  # Not in gift flow, ignore

    if update.effective_user.id != gift_data["sender_id"]:
        return

    text = update.message.text.strip()

    if text.lower() == "/skip":
        gift_data["message"] = None
    else:
        gift_data["message"] = text[:200]  # cap at 200 chars

    context.user_data["gift"] = gift_data

    item       = FLEX_ITEMS[gift_data["item_key"]]
    gift_price = item["price"] + GIFT_SURCHARGE
    msg_line   = f'💬 Message: <i>"{gift_data["message"]}"</i>' if gift_data["message"] else "💬 Message: <i>None</i>"

    confirm_text = f"""🎁 <b>Confirm Gift</b>
━━━━━━━━━━━━━━━
👤 To: <b>{gift_data['target_name']}</b>
{item['emoji']} Item: <b>{item['name']}</b>
💰 Total cost: <b>{fmt(gift_price)}</b>
{msg_line}
━━━━━━━━━━━━━━━
Ready to send?"""

    await update.message.reply_text(confirm_text, parse_mode="HTML", reply_markup=confirm_keyboard())


# ── Helper: show confirm screen ──────────────────────────────────────────────

async def _show_confirm(query, context, gift_data, edit_fn):
    item       = FLEX_ITEMS[gift_data["item_key"]]
    gift_price = item["price"] + GIFT_SURCHARGE
    msg_line   = f'💬 Message: <i>"{gift_data["message"]}"</i>' if gift_data["message"] else "💬 Message: <i>None</i>"

    text = f"""🎁 <b>Confirm Gift</b>
━━━━━━━━━━━━━━━
👤 To: <b>{gift_data['target_name']}</b>
{item['emoji']} Item: <b>{item['name']}</b>
💰 Total cost: <b>{fmt(gift_price)}</b>
{msg_line}
━━━━━━━━━━━━━━━
Ready to send?"""

    await edit_fn(text, confirm_keyboard())


# ── Execute gift ─────────────────────────────────────────────────────────────

async def _execute_gift(query, context, gift_data):
    sender_id  = gift_data["sender_id"]
    sender_name = gift_data["sender_name"]
    target_id  = gift_data["target_id"]
    target_name = gift_data["target_name"]
    group_id   = gift_data["group_id"]
    ikey       = gift_data["item_key"]
    msg        = gift_data.get("message")
    item       = FLEX_ITEMS[ikey]
    gift_price = item["price"] + GIFT_SURCHARGE

    # Fresh fetch
    sdata = await get_user(sender_id, group_id, sender_name)
    if sdata["balance"] < gift_price:
        try:
            await query.edit_message_caption(
                caption="❌ <b>Not enough balance to complete the gift!</b>",
                parse_mode="HTML", reply_markup=None
            )
        except Exception:
            pass
        return

    # Deduct from sender
    new_sender_bal = sdata["balance"] - gift_price
    await update_user(sender_id, group_id, {"balance": new_sender_bal})

    # Add to receiver inventory
    tdata    = await get_user(target_id, group_id, target_name)
    inv      = tdata.get("inventory", {})
    existing = inv.get(ikey, {"qty": 0, "expires_at": None})
    inv[ikey] = {"qty": existing["qty"] + 1, "expires_at": None}
    await update_user(target_id, group_id, {"inventory": inv})

    # Clear conversation data
    context.user_data.pop("gift", None)

    msg_line      = f'\n💬 <i>"{msg}"</i>' if msg else ""
    item_cost_line = fmt(item["price"])
    charge_line    = fmt(GIFT_SURCHARGE)

    # ── Group announcement ──────────────────────────────────────
    group_text = f"""🎁 <b>Gift Sent!</b>
━━━━━━━━━━━━━━━
💌 <b>{sender_name}</b> gifted <b>{target_name}</b>
{item['emoji']} <b>{item['name']}</b>
💰 Item cost: {item_cost_line}
📦 Gift charge: +{charge_line}
🌟 Rarity: {get_rarity(item['price'])}{msg_line}"""

    try:
        await query.delete_message()
    except Exception:
        pass

    await send_with_image(
        context.bot, group_id, IMG_GIFT, group_text
    )

    # ── Private DM to receiver ──────────────────────────────────
    dm_text = f"""🎁 <b>You received a gift!</b>
━━━━━━━━━━━━━━━
💌 From: <b>{sender_name}</b>
{item['emoji']} <b>{item['name']}</b>
💰 Item value: {item_cost_line}
🌟 Rarity: {get_rarity(item['price'])}{msg_line}
━━━━━━━━━━━━━━━
✅ Added to your inventory!"""

    try:
        if IMG_GIFT:
            await context.bot.send_photo(
                chat_id=target_id, photo=IMG_GIFT,
                caption=dm_text, parse_mode="HTML"
            )
        else:
            await context.bot.send_message(
                chat_id=target_id, text=dm_text, parse_mode="HTML"
            )
    except Exception:
        pass
