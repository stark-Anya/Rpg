import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import fmt, send_with_image, get_best_weapon, is_weapon_valid
from config import WEAPONS, FLEX_ITEMS, get_rarity, SELL_RETURN_PERCENT, IMG_SHOP

WEAPONS_PER_PAGE = 9
FLEX_PER_PAGE    = 9


# ── Keyboards ────────────────────────────────────────────────────────────────

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚔️ Weapons",    callback_data="shop_weapons_0"),
            InlineKeyboardButton("💎 Flex & VIP", callback_data="shop_flex_0"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="shop_close")]
    ])


def weapons_page_keyboard(page: int, inventory: dict, balance: int):
    keys  = list(WEAPONS.keys())
    start = page * WEAPONS_PER_PAGE
    chunk = keys[start:start + WEAPONS_PER_PAGE]
    rows  = []

    for k in chunk:
        item     = WEAPONS[k]
        owned    = inventory.get(k, {})
        is_owned = owned.get("qty", 0) > 0 and is_weapon_valid(owned)
        can_buy  = balance >= item["price"]

        if is_owned:
            label = f"✅ {item['name']} · owned"
        elif not can_buy:
            label = f"❌ {item['name'].split(' ',1)[1]} · {fmt(item['price'])}"
        else:
            label = f"{item['emoji']} {item['name'].split(' ',1)[1]} · {fmt(item['price'])}"

        rows.append([InlineKeyboardButton(label, callback_data=f"shop_witem_{k}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"shop_weapons_{page-1}"))
    if start + WEAPONS_PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"shop_weapons_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 Main Menu", callback_data="shop_main")])
    return InlineKeyboardMarkup(rows)


def flex_page_keyboard(page: int, inventory: dict, balance: int):
    keys  = list(FLEX_ITEMS.keys())
    start = page * FLEX_PER_PAGE
    chunk = keys[start:start + FLEX_PER_PAGE]
    rows  = []

    for k in chunk:
        item     = FLEX_ITEMS[k]
        owned    = inventory.get(k, {})
        is_owned = owned.get("qty", 0) > 0
        can_buy  = balance >= item["price"]

        if is_owned:
            label = f"✅ {item['name']} · owned"
        elif not can_buy:
            label = f"❌ {item['name'].split(' ',1)[1]} · {fmt(item['price'])}"
        else:
            label = f"{item['emoji']} {item['name'].split(' ',1)[1]} · {fmt(item['price'])}"

        rows.append([InlineKeyboardButton(label, callback_data=f"shop_fitem_{k}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"shop_flex_{page-1}"))
    if start + FLEX_PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"shop_flex_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 Main Menu", callback_data="shop_main")])
    return InlineKeyboardMarkup(rows)


def weapon_action_kb(item_key: str, can_buy: bool, is_owned: bool):
    if is_owned:
        buy_btn = InlineKeyboardButton("✅ Owned", callback_data=f"shop_owned_w_{item_key}")
    elif can_buy:
        buy_btn = InlineKeyboardButton("🛒 Buy Now", callback_data=f"shop_buy_w_{item_key}")
    else:
        buy_btn = InlineKeyboardButton("❌ Can't Afford", callback_data=f"shop_poor_w_{item_key}")

    return InlineKeyboardMarkup([
        [buy_btn],
        [InlineKeyboardButton("◀️ Back", callback_data="shop_weapons_0")]
    ])


def flex_action_kb(item_key: str, can_buy: bool, is_owned: bool):
    if is_owned:
        buy_btn = InlineKeyboardButton("✅ Owned", callback_data=f"shop_owned_f_{item_key}")
    elif can_buy:
        buy_btn = InlineKeyboardButton("🛒 Buy Now", callback_data=f"shop_buy_f_{item_key}")
    else:
        buy_btn = InlineKeyboardButton("❌ Can't Afford", callback_data=f"shop_poor_f_{item_key}")

    return InlineKeyboardMarkup([
        [buy_btn],
        [InlineKeyboardButton("◀️ Back", callback_data="shop_flex_0")]
    ])


# ── /shop command ────────────────────────────────────────────────────────────

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    group_id = update.effective_chat.id
    udata    = await get_user(user.id, group_id, user.first_name)

    text = f"""🛒 <b>𝐌𝐚𝐫𝐢𝐞 𝐌𝐚𝐫𝐤𝐞𝐭𝐩𝐥𝐚𝐜𝐞</b>
━━━━━━━━━━━━━━━
👤 Customer: <b>{user.first_name}</b>
👛 Wallet: <b>{fmt(udata['balance'])}</b>
━━━━━━━━━━━━━━━
Select a category to browse our goods!"""

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
        text = f"""🛒 <b>𝐌𝐚𝐫𝐢𝐞 𝐌𝐚𝐫𝐤𝐞𝐭𝐩𝐥𝐚𝐜𝐞</b>
━━━━━━━━━━━━━━━
👤 Customer: <b>{user.first_name}</b>
👛 Wallet: <b>{fmt(balance)}</b>
━━━━━━━━━━━━━━━
Select a category to browse our goods!"""
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
                expire_str = f"\n⏳ Expires in: <b>{rem//3600}h {(rem%3600)//60}m</b>"

        status_line = "✅ <b>You own this weapon!</b>" if is_owned else \
                      "❌ <b>Can't afford</b>" if not can_buy else \
                      "🛒 Available to buy"

        text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 Price: <b>{fmt(item['price'])}</b>
🌟 Rarity: {get_rarity(item['price'])}
💥 Kill Loot Bonus: <b>+{int(item['kill_loot_bonus']*100)}%</b>
⏱️ Duration: <b>{item['lifetime_hours']}h</b>
━━━━━━━━━━━━━━━
{status_line}{expire_str}"""

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

        status_line = "✅ <b>You own this!</b>" if is_owned else \
                      "❌ <b>Can't afford</b>" if not can_buy else \
                      "🛒 Available to buy"

        text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 Price: <b>{fmt(item['price'])}</b>
🌟 Rarity: {get_rarity(item['price'])}
⏱️ Duration: <b>♾️ Permanent</b>
━━━━━━━━━━━━━━━
{status_line}"""

        await edit(text, flex_action_kb(key, can_buy, is_owned))
        return

    # ── Can't Afford popup ─────────────────────────────────────
    if data.startswith("shop_poor_"):
        await query.answer("📉 You are too poor for this!", show_alert=True)
        return

    # ── Already Owned popup ────────────────────────────────────
    if data.startswith("shop_owned_"):
        parts = data.split("_")
        itype = parts[2]  # w or f
        if itype == "w":
            await query.answer("✅ You already own this weapon! Wait for it to expire.", show_alert=True)
        else:
            await query.answer("💎 You already own this. Check your inventory 🎒", show_alert=True)
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

        # Fresh fetch
        udata2    = await get_user(user.id, group_id, user.first_name)
        inventory = udata2.get("inventory", {})
        balance2  = udata2["balance"]

        # Prevent double buy
        if itype == "w":
            owned = inventory.get(ikey, {})
            if owned.get("qty", 0) > 0 and is_weapon_valid(owned):
                await query.answer("✅ You already own this weapon! Wait for it to expire.", show_alert=True)
                return
        else:
            if inventory.get(ikey, {}).get("qty", 0) > 0:
                await query.answer("💎 You already own this. Check your inventory 🎒", show_alert=True)
                return

        if balance2 < item["price"]:
            await query.answer("📉 You are too poor for this!", show_alert=True)
            return

        # Purchase
        if itype == "w":
            expires_at = time.time() + item["lifetime_hours"] * 3600
            inventory[ikey] = {"qty": 1, "expires_at": expires_at}
        else:
            existing = inventory.get(ikey, {})
            inventory[ikey] = {"qty": existing.get("qty", 0) + 1, "expires_at": None}

        new_balance = balance2 - item["price"]
        await update_user(user.id, group_id, {"balance": new_balance, "inventory": inventory})
        await query.answer(f"🎉 {item['name']} purchased!", show_alert=True)

        # Refresh detail view
        if itype == "w":
            owned = inventory.get(ikey, {})
            expire_str = ""
            if owned.get("expires_at"):
                rem = int(owned["expires_at"] - time.time())
                if rem > 0:
                    expire_str = f"\n⏳ Expires in: <b>{rem//3600}h {(rem%3600)//60}m</b>"
            text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 Price: <b>{fmt(item['price'])}</b>
🌟 Rarity: {get_rarity(item['price'])}
💥 Kill Loot Bonus: <b>+{int(item['kill_loot_bonus']*100)}%</b>
⏱️ Duration: <b>{item['lifetime_hours']}h</b>
━━━━━━━━━━━━━━━
✅ <b>You own this weapon!</b>{expire_str}"""
            await edit(text, weapon_action_kb(ikey, False, True))
        else:
            text = f"""{item['emoji']} <b>{item['name']}</b>
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 Price: <b>{fmt(item['price'])}</b>
🌟 Rarity: {get_rarity(item['price'])}
⏱️ Duration: <b>♾️ Permanent</b>
━━━━━━━━━━━━━━━
✅ <b>You own this!</b>"""
            await edit(text, flex_action_kb(ikey, False, True))

        # Group announcement
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

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    group_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text(
            "❌ Usage: <code>/sell [item_key]</code>\nEx: <code>/sell cookie</code>",
            parse_mode="HTML"
        )
        return

    ikey = context.args[0].lower()
    item = FLEX_ITEMS.get(ikey)

    if not item:
        await update.message.reply_text("❌ Only Flex & VIP items can be sold!", parse_mode="HTML")
        return

    udata     = await get_user(user.id, group_id, user.first_name)
    inventory = udata.get("inventory", {})
    owned     = inventory.get(ikey, {})

    if not owned or owned.get("qty", 0) <= 0:
        await update.message.reply_text("❌ You don't own this item!", parse_mode="HTML")
        return

    sell_price = int(item["price"] * SELL_RETURN_PERCENT)
    new_qty    = owned["qty"] - 1

    if new_qty <= 0:
        del inventory[ikey]
    else:
        inventory[ikey]["qty"] = new_qty

    new_balance = udata["balance"] + sell_price
    await update_user(user.id, group_id, {"balance": new_balance, "inventory": inventory})

    await update.message.reply_text(
        f"""💸 <b>Sold!</b>
━━━━━━━━━━━━━━━
🛍️ {item['name']}
💰 Got: {fmt(sell_price)} (85% back)
👛 Balance: {fmt(new_balance)}""",
        parse_mode="HTML"
    )
