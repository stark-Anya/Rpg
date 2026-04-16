import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import fmt, send_with_image, get_best_weapon, is_weapon_valid
from config import WEAPONS, FLEX_ITEMS, get_rarity, SELL_RETURN_PERCENT, IMG_SHOP

WEAPONS_PER_PAGE = 6
FLEX_PER_PAGE    = 6


# ── Keyboards ────────────────────────────────────────────────────────────────

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚔️ 𝐖𝐞𝐩𝐨𝐧𝐬",    callback_data="shop_weapons_0"),
            InlineKeyboardButton("💎 𝐅𝐥𝐞𝐱 & 𝐕𝐈𝐏", callback_data="shop_flex_0"),
        ],
        [InlineKeyboardButton("❌ 𝐂𝐥𝐨𝐬𝐞", callback_data="shop_close")]
    ])


def weapons_page_keyboard(page: int, inventory: dict, balance: int):
    keys  = list(WEAPONS.keys())
    start = page * WEAPONS_PER_PAGE
    chunk = keys[start:start + WEAPONS_PER_PAGE]
    rows  = []

    # 2 per row
    for i in range(0, len(chunk), 2):
        row = []
        for k in chunk[i:i+2]:
            item     = WEAPONS[k]
            owned    = inventory.get(k, {})
            is_owned = owned.get("qty", 0) > 0 and is_weapon_valid(owned)
            label    = f"{item['emoji']} {item['name'].split(' ',1)[1]} · {fmt(item['price'])}"
            if is_owned:
                label = f"{item['emoji']} {item['name'].split(' ',1)[1]} · owned"
            row.append(InlineKeyboardButton(label, callback_data=f"shop_witem_{k}"))
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ 𝐏𝐫𝐞𝐯", callback_data=f"shop_weapons_{page-1}"))
    if start + WEAPONS_PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("𝐍𝐞𝐱𝐭 ▶", callback_data=f"shop_weapons_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 𝐌𝐚𝐢𝐧 𝐌𝐞𝐧𝐮", callback_data="shop_main")])
    return InlineKeyboardMarkup(rows)


def flex_page_keyboard(page: int, inventory: dict, balance: int):
    keys  = list(FLEX_ITEMS.keys())
    start = page * FLEX_PER_PAGE
    chunk = keys[start:start + FLEX_PER_PAGE]
    rows  = []

    # 2 per row
    for i in range(0, len(chunk), 2):
        row = []
        for k in chunk[i:i+2]:
            item     = FLEX_ITEMS[k]
            owned    = inventory.get(k, {})
            is_owned = owned.get("qty", 0) > 0
            label    = f"{item['emoji']} {item['name'].split(' ',1)[1]} · {fmt(item['price'])}"
            if is_owned:
                label = f"{item['emoji']} {item['name'].split(' ',1)[1]} · owned"
            row.append(InlineKeyboardButton(label, callback_data=f"shop_fitem_{k}"))
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ 𝐏𝐫𝐞𝐯", callback_data=f"shop_flex_{page-1}"))
    if start + FLEX_PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("𝐍𝐞𝐱𝐭 ▶", callback_data=f"shop_flex_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 𝐌𝐚𝐢𝐧 𝐌𝐞𝐧𝐮", callback_data="shop_main")])
    return InlineKeyboardMarkup(rows)


def weapon_action_kb(item_key: str, can_buy: bool, is_owned: bool):
    if is_owned:
        buy_btn = InlineKeyboardButton("✅ 𝐎𝐰𝐧𝐞𝐝", callback_data=f"shop_owned_w_{item_key}")
    elif can_buy:
        buy_btn = InlineKeyboardButton("🛒 𝐁𝐮𝐲 𝐍𝐨𝐰", callback_data=f"shop_buy_w_{item_key}")
    else:
        buy_btn = InlineKeyboardButton("❌ 𝐂𝐚𝐧'𝐭 𝐀𝐟𝐟𝐨𝐫𝐝", callback_data=f"shop_poor_w_{item_key}")

    return InlineKeyboardMarkup([
        [buy_btn],
        [InlineKeyboardButton("◀️ 𝐁𝐚𝐜𝐤", callback_data="shop_weapons_0")]
    ])


def flex_action_kb(item_key: str, can_buy: bool, is_owned: bool):
    if is_owned:
        buy_btn = InlineKeyboardButton("✅ 𝐎𝐰𝐧𝐞𝐝", callback_data=f"shop_owned_f_{item_key}")
    elif can_buy:
        buy_btn = InlineKeyboardButton("🛒 𝐁𝐨𝐮 𝐍𝐨𝐰", callback_data=f"shop_buy_f_{item_key}")
    else:
        buy_btn = InlineKeyboardButton("❌ 𝐂𝐚𝐧'𝐭 𝐀𝐟𝐟𝐨𝐫𝐝", callback_data=f"shop_poor_f_{item_key}")

    return InlineKeyboardMarkup([
        [buy_btn],
        [InlineKeyboardButton("◀️ 𝐁𝐚𝐜𝐤", callback_data="shop_flex_0")]
    ])


# ── /shop command ────────────────────────────────────────────────────────────

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    group_id = update.effective_chat.id
    udata    = await get_user(user.id, group_id, user.first_name)

    text = f"""🛒 <b>𝐊𝐢𝐚𝐫𝐚 𝐌𝐚𝐫𝐤𝐞𝐭𝐩𝐥𝐚𝐜𝐞</b>
━━━━━━━━━━━━━━━
👤 Customer: <b>{user.first_name}</b>
👛 Wallet: <b>{fmt(udata['balance'])}</b>
━━━━━━━━━━━━━━━
<i>Select a category to browse our goods!</i>"""

    await send_with_image(update, group_id, IMG_SHOP, text, reply_markup=main_keyboard())


# ── Button Handler ───────────────────────────────────────────────────────────

async def shop_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    user     = update.effective_user
    data     = query.data
    group_id = update.effective_chat.id

    async def edit(text, kb):
        try:
            await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            try:
                await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb)
            except Exception:
                pass

    udata     = await get_user(user.id, group_id, user.first_name)
    inventory = udata.get("inventory", {})
    balance   = udata["balance"]

    # ── Close ──────────────────────────────────────────────────
    if data == "shop_close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ── Main Menu ──────────────────────────────────────────────
    if data == "shop_main":
        await query.answer()
        text = f"""🛒 <b>𝐊𝐢𝐚𝐫𝐚 𝐌𝐚𝐫𝐤𝐞𝐭𝐩𝐥𝐚𝐜𝐞</b>
━━━━━━━━━━━━━━━
👤 Customer: <b>{user.first_name}</b>
👛 Wallet: <b>{fmt(balance)}</b>
━━━━━━━━━━━━━━━
<i>Select a category to browse our goods!</i>"""
        await edit(text, main_keyboard())
        return

    # ── Weapons List ───────────────────────────────────────────
    if data.startswith("shop_weapons_"):
        await query.answer()
        page = int(data.split("_")[-1])
        text = f"""⚔️ <b>𝐖𝐞𝐚𝐩𝐨𝐧𝐬 𝐀𝐫𝐦𝐨𝐫𝐲</b>
Lethal gear for killers.
━━━━━━━━━━━━━━━
💰 Balance: <b>{fmt(balance)}</b>"""
        await edit(text, weapons_page_keyboard(page, inventory, balance))
        return

    # ── Flex List ──────────────────────────────────────────────
    if data.startswith("shop_flex_"):
        await query.answer()
        page = int(data.split("_")[-1])
        text = f"""💎 <b>𝐕𝐈𝐏 𝐅𝐥𝐞𝐱 𝐙𝐨𝐧𝐞</b>
Pure status symbols.
━━━━━━━━━━━━━━━
💰 Balance: <b>{fmt(balance)}</b>"""
        await edit(text, flex_page_keyboard(page, inventory, balance))
        return

    # ── Weapon Detail ──────────────────────────────────────────
    if data.startswith("shop_witem_"):
        await query.answer()
        key  = data[len("shop_witem_"):]
        item = WEAPONS.get(key)
        if not item:
            return

        owned    = inventory.get(key, {})
        is_owned = owned.get("qty", 0) > 0 and is_weapon_valid(owned)
        can_buy  = balance >= item["price"]

        expire_str = ""
        if is_owned and owned.get("expires_at"):
            rem = int(owned["expires_at"] - time.time())
            if rem > 0:
                expire_str = f"\n⏳ <b>Expires in:</b> {rem//3600}h {(rem%3600)//60}m"

        text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 <b>Price:</b> {fmt(item['price'])}
🌟 <b>Rarity:</b> {get_rarity(item['price'])}
💥 <b>Kill Loot Bonus:</b> +{int(item['kill_loot_bonus']*100)}%
⏱️ <b>Duration:</b> {item['lifetime_hours']}h
━━━━━━━━━━━━━━━
👛 <b>Your Wallet:</b> {fmt(balance)}{expire_str}"""

        await edit(text, weapon_action_kb(key, can_buy, is_owned))
        return

    # ── Flex Detail ────────────────────────────────────────────
    if data.startswith("shop_fitem_"):
        await query.answer()
        key  = data[len("shop_fitem_"):]
        item = FLEX_ITEMS.get(key)
        if not item:
            return

        owned    = inventory.get(key, {})
        is_owned = owned.get("qty", 0) > 0
        can_buy  = balance >= item["price"]

        text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 <b>Price:</b> {fmt(item['price'])}
🌟 <b>Rarity:</b> {get_rarity(item['price'])}
⏱️ <b>Duration:</b> ♾️ Permanent
━━━━━━━━━━━━━━━
👛 <b>Your Wallet:</b> {fmt(balance)}"""

        await edit(text, flex_action_kb(key, can_buy, is_owned))
        return

    # ── Can't Afford popup ─────────────────────────────────────
    if data.startswith("shop_poor_"):
        await query.answer("📉 ʏᴏᴜ ᴀʀᴇ ᴛᴏᴏ ᴘᴏᴏʀ ᴛᴏ ʙᴜʏ ᴛʜɪs!", show_alert=True)
        return

    # ── Already Owned popup ────────────────────────────────────
    if data.startswith("shop_owned_"):
        parts = data.split("_")
        itype = parts[2]
        if itype == "w":
            await query.answer("✅ ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴏᴡɴ ᴛʜɪs ᴡᴇᴘᴏɴ ! ᴡᴀɪᴛ ꜰᴏʀ ɪᴛ ᴛᴏ ᴇxᴘɪʀᴇ.", show_alert=True)
        else:
            await query.answer("💎 ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴅʏ ᴏᴡɴ ᴛʜɪs. cʜᴇᴀᴋ ʏᴏᴜʀ ɪɴᴠᴇɴᴛᴏʀʏ🎒", show_alert=True)
        return

    # ── Buy ────────────────────────────────────────────────────
    if data.startswith("shop_buy_"):
        parts   = data.split("_")
        itype   = parts[2]
        ikey    = "_".join(parts[3:])
        catalog = WEAPONS if itype == "w" else FLEX_ITEMS
        item    = catalog.get(ikey)

        if not item:
            await query.answer("❌ Item not found!", show_alert=True)
            return

        udata2    = await get_user(user.id, group_id, user.first_name)
        inventory = udata2.get("inventory", {})
        balance2  = udata2["balance"]

        if itype == "w":
            owned = inventory.get(ikey, {})
            if owned.get("qty", 0) > 0 and is_weapon_valid(owned):
                await query.answer("✅ ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴅʏ ᴏᴡɴᴇʀ ᴛʜɪs ᴡᴇᴘᴏɴ !", show_alert=True)
                return
        else:
            if inventory.get(ikey, {}).get("qty", 0) > 0:
                await query.answer("💎 ᴀʟʀᴇᴀᴅʏ ᴏᴡɴᴇᴅ!", show_alert=True)
                return

        if balance2 < item["price"]:
            await query.answer("📉 ʏᴏᴜ ᴀʀᴇ ᴛᴏᴏ ᴘᴏᴏʀ ꜰᴏʀ ᴛʜɪs !", show_alert=True)
            return

        if itype == "w":
            expires_at = time.time() + item["lifetime_hours"] * 3600
            inventory[ikey] = {"qty": 1, "expires_at": expires_at}
        else:
            existing = inventory.get(ikey, {})
            inventory[ikey] = {"qty": existing.get("qty", 0) + 1, "expires_at": None}

        new_balance = balance2 - item["price"]
        await update_user(user.id, group_id, {"balance": new_balance, "inventory": inventory})
        await query.answer(f"🎉 {item['name']} purchased!", show_alert=True)

        # Refresh detail view after buy
        if itype == "w":
            owned = inventory.get(ikey, {})
            expire_str = ""
            if owned.get("expires_at"):
                rem = int(owned["expires_at"] - time.time())
                if rem > 0:
                    expire_str = f"\n⏳ <b>Expires in:</b> {rem//3600}h {(rem%3600)//60}m"
            text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 <b>Price:</b> {fmt(item['price'])}
🌟 <b>Rarity:</b> {get_rarity(item['price'])}
💥 <b>Kill Loot Bonus:</b> +{int(item['kill_loot_bonus']*100)}%
⏱️ <b>Duration:</b> {item['lifetime_hours']}h
━━━━━━━━━━━━━━━
👛 <b>Your Wallet:</b> {fmt(new_balance)}{expire_str}"""
            await edit(text, weapon_action_kb(ikey, False, True))
        else:
            text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 <b>Price:</b> {fmt(item['price'])}
🌟 <b>Rarity:</b> {get_rarity(item['price'])}
⏱️ <b>Duration:</b> ♾️ Permanent
━━━━━━━━━━━━━━━
👛 <b>Your Wallet:</b> {fmt(new_balance)}"""
            await edit(text, flex_action_kb(ikey, False, True))

        try:
            await context.bot.send_message(
                chat_id=group_id,
                text=f"🛍️ <b>{user.first_name}</b> bought <b>{item['name']}</b> for <b>{fmt(item['price'])}</b>!",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return


# ── /sell command ─────────────────────────────────────────────────────────────

SELL_PER_PAGE = 6   # 2 cols × 3 rows


def sell_inventory_keyboard(owned_keys: list, page: int):
    """2 cols × 3 rows of owned flex items. Item's own emoji, sell price shown."""
    start = page * SELL_PER_PAGE
    chunk = owned_keys[start:start + SELL_PER_PAGE]
    rows  = []

    for i in range(0, len(chunk), 2):
        row = []
        for k in chunk[i:i+2]:
            item       = FLEX_ITEMS[k]
            sell_price = int(item["price"] * SELL_RETURN_PERCENT)
            label      = f"{item['emoji']} {item['name'].split(' ',1)[1]} · {fmt(sell_price)}"
            row.append(InlineKeyboardButton(label, callback_data=f"sell_item_{k}"))
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ 𝐏𝐫𝐞𝐯", callback_data=f"sell_page_{page-1}"))
    if start + SELL_PER_PAGE < len(owned_keys):
        nav.append(InlineKeyboardButton("𝐍𝐞𝐱𝐭 ▶", callback_data=f"sell_page_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("❌ 𝐂𝐥𝐨𝐬𝐞", callback_data="sell_close")])
    return InlineKeyboardMarkup(rows)


def sell_item_keyboard(ikey: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 𝐒𝐞𝐥𝐥 𝐍𝐨𝐰", callback_data=f"sell_now_{ikey}")],
        [InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤",     callback_data="sell_back_list")]
    ])


def sell_confirm_keyboard(ikey: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ 𝐂𝐨𝐧𝐟𝐨𝐫𝐦", callback_data=f"sell_do_{ikey}"),
            InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤",   callback_data=f"sell_close")
        ]
    ])


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point — show user's owned flex items."""
    user     = update.effective_user
    group_id = update.effective_chat.id
    udata    = await get_user(user.id, group_id, user.first_name)
    inventory = udata.get("inventory", {})

    owned_keys = [k for k, v in inventory.items() if k in FLEX_ITEMS and v.get("qty", 0) > 0]

    if not owned_keys:
        await update.message.reply_text(
            "🎒 𝚈𝚘𝚞 𝚍𝚘𝚗'𝚝 𝚘𝚠𝚗 𝚊𝚗𝚢 𝚏𝚕𝚎𝚡 𝚒𝚝𝚎𝚖 𝚝𝚘 𝚜𝚎𝚕𝚕 !\n𝚅𝚒𝚜𝚒𝚝 /shop 𝚝𝚘 𝚋𝚞𝚢 𝚜𝚘𝚖.",
            parse_mode="HTML"
        )
        return

    # Store session
    context.user_data["sell"] = {
        "user_id":    user.id,
        "group_id":   group_id,
        "owned_keys": owned_keys,
        "page":       0,
    }

    text = f"""💸 <b>𝐒𝐞𝐥𝐥 𝐈𝐭𝐞𝐦𝐬</b>
━━━━━━━━━━━━━━━
👤 {user.first_name}
👛 Balance: <b>{fmt(udata['balance'])}</b>
🎒 Items owned: <b>{len(owned_keys)}</b>
━━━━━━━━━━━━━━━
𝑆𝑒𝑙𝑒𝑐𝑡 𝐼𝑡𝑒𝑚 𝑡𝑜 𝑠𝑒𝑙𝑙 👇"""

    await update.message.reply_text(
        text, parse_mode="HTML",
        reply_markup=sell_inventory_keyboard(owned_keys, 0)
    )


async def sell_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    user     = update.effective_user
    group_id = update.effective_chat.id
    data     = query.data
    sd       = context.user_data.get("sell")

    async def edit(text, kb):
        try:
            await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass

    # Session guard
    if not sd:
        await query.answer("⏰ Session expired. Use /sell again.", show_alert=True)
        return
    if user.id != sd["user_id"]:
        await query.answer("🚫 This is not your sell session!", show_alert=True)
        return

    udata     = await get_user(user.id, group_id, user.first_name)
    inventory = udata.get("inventory", {})
    owned_keys = [k for k, v in inventory.items() if k in FLEX_ITEMS and v.get("qty", 0) > 0]

    # ── Close ──────────────────────────────────────────────────
    if data == "sell_close":
        await query.answer()
        context.user_data.pop("sell", None)
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ── Page nav ────────────────────────────────────────────────
    if data.startswith("sell_page_"):
        await query.answer()
        page          = int(data.split("_")[-1])
        sd["page"]    = page
        sd["owned_keys"] = owned_keys
        context.user_data["sell"] = sd

        text = f"""💸 <b>𝐒𝐞𝐥𝐥 𝐈𝐭𝐞𝐦𝐬</b>
━━━━━━━━━━━━━━━
👤 {user.first_name}
👛 Balance: <b>{fmt(udata['balance'])}</b>
🎒 Items owned: <b>{len(owned_keys)}</b>
━━━━━━━━━━━━━━━
𝐒𝐞𝐥𝐞𝐜𝐭 𝐚𝐧 𝐢𝐭𝐞𝐦 𝐭𝐨 𝐬𝐞𝐥𝐥. 👇"""
        await edit(text, sell_inventory_keyboard(owned_keys, page))
        return

    # ── Back to list ────────────────────────────────────────────
    if data == "sell_back_list":
        await query.answer()
        sd["owned_keys"] = owned_keys
        page = sd.get("page", 0)
        context.user_data["sell"] = sd

        text = f"""💸 <b>𝐒𝐞𝐥𝐥 𝐈𝐭𝐞𝐦</b>
━━━━━━━━━━━━━━━
👤 {user.first_name}
👛 Balance: <b>{fmt(udata['balance'])}</b>
🎒 Items owned: <b>{len(owned_keys)}</b>
━━━━━━━━━━━━━━━
𝐒𝐞𝐥𝐞𝐜𝐭 𝐚𝐧 𝐢𝐭𝐞𝐦 𝐭𝐨 𝐬𝐞𝐥𝐥. 👇"""
        await edit(text, sell_inventory_keyboard(owned_keys, page))
        return

    # ── Item detail ─────────────────────────────────────────────
    if data.startswith("sell_item_"):
       await query.answer()
       ikey = data[len("sell_item_"):]
       item = FLEX_ITEMS.get(ikey)
       if not item:
           return

        owned_qty  = inventory.get(ikey, {}).get("qty", 0)
        sell_price = int(item["price"] * SELL_RETURN_PERCENT)
        tax_amt    = item["price"] - sell_price

        text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
💰 Original price: <b>{fmt(item['price'])}</b>
💸 Selling price: <b>{fmt(sell_price)}</b>
✂️ Selling tax (15%): -{fmt(tax_amt)}
🎒 You own: <b>{owned_qty}x</b>
━━━━━━━━━━━━━━━
👛 After sell: {fmt(udata['balance'] + sell_price)}"""

        await edit(text, sell_item_keyboard(ikey))
        return

    
    # ── Confirm screen ──────────────────────────────────────────
    if data.startswith("sell_now_"):
        await query.answer()
        ikey = data[len("sell_now_"):]

        item = FLEX_ITEMS.get(ikey)
        if not item:
            return

        owned = inventory.get(ikey, {})
        if not owned or owned.get("qty", 0) <= 0:
            await query.answer("❌ You no longer own this item!", show_alert=True)
            return

        sell_price = int(item["price"] * SELL_RETURN_PERCENT)
        tax_amt    = item["price"] - sell_price

        text = f"""{item['emoji']} <b>𝐂𝐨𝐧𝐟𝐢𝐫𝐦 𝐒𝐞𝐥𝐥</b>
━━━━━━━━━━━━━━━
🛍️ Item: <b>{item['name']}</b>
💰 Original: {fmt(item['price'])}
✂️ Tax (15%): -{fmt(tax_amt)}
💸 You receive: <b>{fmt(sell_price)}</b>
━━━━━━━━━━━━━━━
𝔸𝕣𝕖 𝕪𝕠𝕦 𝕤𝕦𝕣𝕖 ?"""

        await edit(text, sell_confirm_keyboard(ikey))
        return

    # ── Execute sell ────────────────────────────────────────────
    if data.startswith("sell_do_"):
        ikey = data[len("sell_do_"):]
        item = FLEX_ITEMS.get(ikey)
        if not item:
            await query.answer("❌ 𝙸𝚝𝚎𝚖 𝚗𝚘𝚝 𝚏𝚘𝚞𝚗𝚍 !", show_alert=True)
            return

        # Fresh fetch
        udata2    = await get_user(user.id, group_id, user.first_name)
        inventory2 = udata2.get("inventory", {})
        owned     = inventory2.get(ikey, {})

        if not owned or owned.get("qty", 0) <= 0:
            await query.answer("❌ 𝚈𝚘𝚞 𝚗𝚘 𝚕𝚘𝚗𝚐𝚎𝚛 𝚘𝚠𝚗 𝚝𝚑𝚒𝚜 𝚒𝚝𝚎𝚖 !", show_alert=True)
            return

        sell_price  = int(item["price"] * SELL_RETURN_PERCENT)
        tax_amt     = item["price"] - sell_price
        new_qty     = owned["qty"] - 1

        if new_qty <= 0:
            del inventory2[ikey]
        else:
            inventory2[ikey]["qty"] = new_qty

        new_balance = udata2["balance"] + sell_price
        await update_user(user.id, group_id, {"balance": new_balance, "inventory": inventory2})

        # Popup
        await query.answer(f"{item['emoji']} {item['name'].split(' ',1)[1]} is sold!", show_alert=True)

        # Clear session
        context.user_data.pop("sell", None)

        # Receipt in chat
        receipt = f"""{item['emoji']} <b>𝐈𝐭𝐞𝐦 𝐒𝐨𝐥𝐝 !</b>
━━━━━━━━━━━━━━━
🛍️ Item: <b>{item['name']}</b>
🌟 Rarity: {get_rarity(item['price'])}
━━━━━━━━━━━━━━━
💰 Original price: {fmt(item['price'])}
✂️ Selling tax (15%): -{fmt(tax_amt)}
💸 Amount received: <b>{fmt(sell_price)}</b>
━━━━━━━━━━━━━━━
👛 New balance: {fmt(new_balance)}"""

        try:
            await query.edit_message_text(receipt, parse_mode="HTML", reply_markup=None)
        except Exception:
            pass
        return
