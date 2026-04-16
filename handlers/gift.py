#===================================================#
#=============== OWNER : MISTER STARK ==============#
#===================================================#
#============== CREDIT NA LENA BACHHO 🤣 ===========#
#===================================================

"""
/gift handler

Flow:
  1. /gift @user  or  /gift {userid}
     → Opens flex gift shop — 2 columns, 3 rows = 6 items per page
     → Each button: {emoji} {name} · {price+surcharge}
     → No ❌ prefix — just item's own emoji if can't afford (grayed label)
     → Nav: [◀️ Prev] [Next ▶️] + [🚫 Close] at bottom

  2. Tap item → item detail + [🎁 Send Gift] or [💸 Can't Afford]
  3. Bot asks: write a message or tap [⏭️ Skip]
  4. Confirm screen → [✅ Confirm] [🔙 Back]
  5. Gift sent → group announcement + receiver DM with image
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import fmt, send_with_image
from config import FLEX_ITEMS, get_rarity, GIFT_SURCHARGE, IMG_GIFT

ITEMS_PER_PAGE = 6   # 2 cols × 3 rows


# ── Keyboards ────────────────────────────────────────────────────────────────

def gift_list_keyboard(balance: int, page: int = 0):
    """2 columns, 3 rows of flex items. Item's own emoji, price shown."""
    keys  = list(FLEX_ITEMS.keys())
    total = len(keys)
    start = page * ITEMS_PER_PAGE
    chunk = keys[start:start + ITEMS_PER_PAGE]
    rows  = []

    # 2 items per row
    for i in range(0, len(chunk), 2):
        row = []
        for k in chunk[i:i+2]:
            item       = FLEX_ITEMS[k]
            gift_price = item["price"] + GIFT_SURCHARGE
            # Always show item's own emoji — no extra prefix
            label = f"{item['emoji']} {item['name'].split(' ',1)[1]} · {fmt(gift_price)}"
            row.append(InlineKeyboardButton(label, callback_data=f"gift_item_{k}"))
        rows.append(row)

    # Nav row
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ 𝐏𝐫𝐞𝐯", callback_data=f"gift_page_{page-1}"))
    if start + ITEMS_PER_PAGE < total:
        nav.append(InlineKeyboardButton("𝐍𝐞𝐱𝐭 ▶️", callback_data=f"gift_page_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("❌ 𝐂𝐥𝐨𝐬𝐞", callback_data="gift_cancel")])
    return InlineKeyboardMarkup(rows)


def gift_item_keyboard(ikey: str, can_afford: bool):
    if can_afford:
        action_btn = InlineKeyboardButton("🎁 𝐒𝐞𝐧𝐝 𝐓𝐡𝐢𝐬 𝐆𝐢𝐟𝐭", callback_data=f"gift_select_{ikey}")
    else:
        action_btn = InlineKeyboardButton("💸 𝙲𝚊𝚗𝚝 𝙰𝚏𝚏𝚘𝚛𝚍", callback_data="gift_poor")
    return InlineKeyboardMarkup([
        [action_btn],
        [InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤 𝐓𝐨 𝐥𝐢𝐬𝐭", callback_data="gift_back_list")]
    ])


def gift_confirm_keyboard(ikey: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ 𝐂𝐨𝐧𝐟𝐨𝐫𝐦 & 𝐒𝐞𝐧𝐝", callback_data="gift_confirm"),
            InlineKeyboardButton("🔙 𝙱𝚊𝚌𝚔",           callback_data=f"gift_back_item_{ikey}")
        ]
    ])


def gift_message_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ 𝕊𝕜𝕚𝕡 𝕄𝕖𝕤𝕤𝕖𝕘𝕖𝕤", callback_data="gift_skipmsg")]
    ])


# ── /gift entry ──────────────────────────────────────────────────────────────

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    group_id = update.effective_chat.id

    # Resolve target
    tid, tname = None, None
    if update.message.reply_to_message:
        t     = update.message.reply_to_message.from_user
        tid   = t.id
        tname = t.first_name
    elif context.args:
        try:
            tid   = int(context.args[0])
            tname = str(tid)
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
        await update.message.reply_text("🎁 Can't gift yourself!")
        return

    udata = await get_user(user.id, group_id, user.first_name)

    # Store session
    context.user_data["gift"] = {
        "sender_id":   user.id,
        "sender_name": user.first_name,
        "target_id":   tid,
        "target_name": tname,
        "group_id":    group_id,
        "item_key":    None,
        "message":     None,
        "page":        0,
    }

    text = f"""🎁 <b>𝐆𝐢𝐟𝐭 𝐒𝐭𝐨𝐫𝐞</b>
━━━━━━━━━━━━━━━
👤 Your Name : <b>{tname}</b>
👛 Your wallet: <b>{fmt(udata['balance'])}</b>
📦 Gift charge: +{fmt(GIFT_SURCHARGE)} per item
━━━━━━━━━━━━━━━
<b>𝑃𝑖𝑐𝑘 𝑎 𝐹𝑙𝑒𝑥 𝑎𝑛𝑑 𝑉𝑖𝑝 𝑖𝑡𝑒𝑚 𝑡𝑜 𝑠𝑒𝑛𝑑</b> 👇"""

    await send_with_image(
        update, group_id, IMG_GIFT, text,
        reply_markup=gift_list_keyboard(udata["balance"], 0)
    )


# ── Button Handler ───────────────────────────────────────────────────────────

async def gift_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    user     = update.effective_user
    group_id = update.effective_chat.id
    data     = query.data
    gd       = context.user_data.get("gift")  # gift session

    async def edit(text, kb):
        try:
            await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            try:
                await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb)
            except Exception:
                pass

    # Session guard
    if not gd:
        await query.answer("⏰ Session expired. Use /gift again.", show_alert=True)
        return
    if user.id != gd["sender_id"]:
        await query.answer("🚫 This is not your gift session!", show_alert=True)
        return

    udata   = await get_user(user.id, group_id, user.first_name)
    balance = udata["balance"]

    # ── Close ──────────────────────────────────────────────────
    if data == "gift_cancel":
        await query.answer()
        context.user_data.pop("gift", None)
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ── Can't afford popup ──────────────────────────────────────
    if data == "gift_poor":
        await query.answer("💸 𝚈𝚘𝚞 𝙲𝚊𝚗'𝚝 𝙰𝚏𝚏𝚘𝚛𝚍 𝚃𝚑𝚒𝚜 𝙶𝚒𝚏𝚝!", show_alert=True)
        return

    # ── Page navigation ─────────────────────────────────────────
    if data.startswith("gift_page_"):
        await query.answer()
        page      = int(data.split("_")[-1])
        gd["page"] = page
        context.user_data["gift"] = gd

        text = f"""🎁 <b> 𝐆𝐢𝐟𝐭 𝐒𝐡𝐨𝐩</b>
━━━━━━━━━━━━━━━
👤 Gifting to: <b>{gd['target_name']}</b>
👛 Your wallet: <b>{fmt(balance)}</b>
📦 Gift surcharge: +{fmt(GIFT_SURCHARGE)} per item
━━━━━━━━━━━━━━━
<b>𝑃𝑖𝑐𝑘 𝑎 𝐹𝑙𝑒𝑥 𝑎𝑛𝑑 𝑉𝑖𝑝 𝑖𝑡𝑒𝑚 𝑡𝑜 𝑠𝑒𝑛𝑑</b> 👇"""
        await edit(text, gift_list_keyboard(balance, page))
        return

    # ── Back to list ────────────────────────────────────────────
    if data == "gift_back_list":
        await query.answer()
        page = gd.get("page", 0)
        text = f"""🎁 <b>𝐆𝐢𝐟𝐭 𝐒𝐡𝐨𝐩</b>
━━━━━━━━━━━━━━━
👤 Gifting to: <b>{gd['target_name']}</b>
👛 Your wallet: <b>{fmt(balance)}</b>
📦 Gift surcharge: +{fmt(GIFT_SURCHARGE)} per item
━━━━━━━━━━━━━━━
<b>𝑃𝑖𝑐𝑘 𝑎 𝐹𝑙𝑒𝑥 𝑎𝑛𝑑 𝑉𝑖𝑝 𝑖𝑡𝑒𝑚 𝑡𝑜 𝑠𝑒𝑛𝑑</b> 👇"""
        await edit(text, gift_list_keyboard(balance, page))
        return

    # ── Item detail view ────────────────────────────────────────
    if data.startswith("gift_item_"):
        await query.answer()
        ikey       = data[len("gift_item_"):]
        item       = FLEX_ITEMS.get(ikey)
        if not item:
            return
        gift_price = item["price"] + GIFT_SURCHARGE
        can_afford = balance >= gift_price

        text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 Item price: {fmt(item['price'])}
📦 Gift charge: +{fmt(GIFT_SURCHARGE)}
💸 Total: <b>{fmt(gift_price)}</b>
⏱️ Duration: ♾️ Permanent
━━━━━━━━━━━━━━━
👛 Your wallet: {fmt(balance)}"""

        await edit(text, gift_item_keyboard(ikey, can_afford))
        return

    # ── Item selected for gifting ───────────────────────────────
    if data.startswith("gift_select_"):
        await query.answer()
        ikey       = data[len("gift_select_"):]
        item       = FLEX_ITEMS.get(ikey)
        if not item:
            return
        gift_price = item["price"] + GIFT_SURCHARGE

        if balance < gift_price:
            await query.answer("💸 𝙽𝚘𝚝 𝙴𝚗𝚘𝚞𝚐𝚑 𝙱𝚊𝚕𝚊𝚗𝚌𝚎!", show_alert=True)
            return

        gd["item_key"] = ikey
        context.user_data["gift"] = gd

        text = f"""{item['emoji']} <b>{item['name']}</b> selected!
━━━━━━━━━━━━━━━
👤 Gifting to: <b>{gd['target_name']}</b>
💸 Total cost: <b>{fmt(gift_price)}</b>
━━━━━━━━━━━━━━━
💬 <b>Write a personal message</b> for {gd['target_name']}
Or tap Skip below 👇"""

        await edit(text, gift_message_keyboard())
        return

    # ── Skip message ────────────────────────────────────────────
    if data == "gift_skipmsg":
        if not gd.get("item_key"):
            await query.answer("⚠️ No item selected!", show_alert=True)
            return
        await query.answer()
        gd["message"] = None
        context.user_data["gift"] = gd
        await _show_confirm(edit, gd, balance)
        return

    # ── Back to item from confirm ───────────────────────────────
    if data.startswith("gift_back_item_"):
        await query.answer()
        ikey       = data[len("gift_back_item_"):]
        item       = FLEX_ITEMS.get(ikey)
        if not item:
            return
        gift_price = item["price"] + GIFT_SURCHARGE
        can_afford = balance >= gift_price

        text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 Item price: {fmt(item['price'])}
📦 Gift charge: +{fmt(GIFT_SURCHARGE)}
💸 Total: <b>{fmt(gift_price)}</b>
━━━━━━━━━━━━━━━
👛 Your wallet: {fmt(balance)}"""

        await edit(text, gift_item_keyboard(ikey, can_afford))
        return

    # ── Final confirm ───────────────────────────────────────────
    if data == "gift_confirm":
        if not gd.get("item_key"):
            await query.answer("⚠️ Session expired!", show_alert=True)
            return
        await query.answer()
        await _execute_gift(query, context, gd)
        return


# ── Text message input for gift message ──────────────────────────────────────

async def gift_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gd = context.user_data.get("gift")
    if not gd or not gd.get("item_key"):
        return  # Not in gift flow
    if update.effective_user.id != gd["sender_id"]:
        return

    text = update.message.text.strip()
    if text.startswith("/"):
        return  # ignore other commands

    gd["message"] = text[:200]
    context.user_data["gift"] = gd

    item       = FLEX_ITEMS[gd["item_key"]]
    gift_price = item["price"] + GIFT_SURCHARGE
    msg_line   = f'💬 Message: <i>"{gd["message"]}"</i>'

    confirm_text = f"""🎁 <b>𝐂𝐨𝐧𝐟𝐨𝐫𝐦 𝐆𝐢𝐟𝐭</b>
━━━━━━━━━━━━━━━
👤 To: <b>{gd['target_name']}</b>
{item['emoji']} <b>{item['name']}</b>
💰 Total: <b>{fmt(gift_price)}</b>
{msg_line}
━━━━━━━━━━━━━━━
<b>ᴀʀᴇ ʏᴏᴜ ʀᴇᴀᴅʏ ᴛᴏ sᴇɴᴅ ɢɪꜰᴛ ?</b>"""

    await update.message.reply_text(
        confirm_text, parse_mode="HTML",
        reply_markup=gift_confirm_keyboard(gd["item_key"])
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _show_confirm(edit_fn, gd: dict, balance: int):
    item       = FLEX_ITEMS[gd["item_key"]]
    gift_price = item["price"] + GIFT_SURCHARGE
    msg_line   = f'💬 Message: <i>"{gd["message"]}"</i>' if gd["message"] else "💬 Message: None"

    text = f"""🎁 <b>𝐂𝐨𝐧𝐟𝐨𝐫𝐦 𝐆𝐢𝐟𝐭</b>
━━━━━━━━━━━━━━━
👤 To: <b>{gd['target_name']}</b>
{item['emoji']} <b>{item['name']}</b>
💰 Total: <b>{fmt(gift_price)}</b>
{msg_line}
━━━━━━━━━━━━━━━
<b>ᴀʀᴇ ʏᴏᴜ ʀᴇᴀᴅʏ ᴛᴏ sᴇɴᴅ ɢɪꜰᴛ ?</b>"""

    await edit_fn(text, gift_confirm_keyboard(gd["item_key"]))


async def _execute_gift(query, context, gd: dict):
    sender_id   = gd["sender_id"]
    sender_name = gd["sender_name"]
    target_id   = gd["target_id"]
    target_name = gd["target_name"]
    group_id    = gd["group_id"]
    ikey        = gd["item_key"]
    msg         = gd.get("message")
    item        = FLEX_ITEMS[ikey]
    gift_price  = item["price"] + GIFT_SURCHARGE

    # Fresh balance check
    sdata = await get_user(sender_id, group_id, sender_name)
    if sdata["balance"] < gift_price:
        try:
            await query.edit_message_caption(
                caption="💸 <b>𝙽𝚘𝚝 𝙴𝚗𝚘𝚞𝚐𝚑 𝙱𝚊𝚕𝚊𝚗𝚌𝚎 !</b> 𝙶𝚒𝚏𝚝 𝙲𝚊𝚗𝚌𝚎𝚕𝚕𝚎𝚍.",
                parse_mode="HTML", reply_markup=None
            )
        except Exception:
            pass
        context.user_data.pop("gift", None)
        return

    # Deduct sender
    await update_user(sender_id, group_id, {"balance": sdata["balance"] - gift_price})

    # Add to receiver inventory
    tdata    = await get_user(target_id, group_id, target_name)
    inv      = tdata.get("inventory", {})
    existing = inv.get(ikey, {"qty": 0, "expires_at": None})
    inv[ikey] = {"qty": existing["qty"] + 1, "expires_at": None}
    await update_user(target_id, group_id, {"inventory": inv})

    context.user_data.pop("gift", None)

    msg_line = f'\n💬 <i>"{msg}"</i>' if msg else ""

    # ── Group message ──────────────────────────────────────────
    group_text = f"""🎁 <b>𝐆𝐢𝐟𝐭 𝐒𝐞𝐧𝐭 !</b>
━━━━━━━━━━━━━━━
💌 From: <b>{sender_name}</b>
🎯 To: <b>{target_name}</b>
{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
💰 Item: {fmt(item['price'])}
📦 Charge: +{fmt(GIFT_SURCHARGE)}
💸 Total paid: {fmt(gift_price)}
🌟 {msg_line}"""

    try:
        await query.delete_message()
    except Exception:
        pass

    await send_with_image(context.bot, group_id, IMG_GIFT, group_text)

    # ── Private DM to receiver ──────────────────────────────────
    dm_text = f"""🎁 <b>𝕐𝕠𝕦 𝔾𝕠𝕥 𝔸 𝔾𝕚𝕗𝕥 !</b>
━━━━━━━━━━━━━━━
💌 From: <b>{sender_name}</b>
{item['emoji']} <b>{item['name']}</b>
💰 Value: {fmt(item['price'])}
🌟 {msg_line}
━━━━━━━━━━━━━━━
✅ 𝐴𝑑𝑑 𝑡𝑜 𝑌𝑜𝑢 𝐼𝑛𝑣𝑒𝑛𝑡𝑜𝑟𝑦 !"""

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
