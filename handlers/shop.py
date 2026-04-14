import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import fmt, send_with_image, get_best_weapon, is_weapon_valid
from config import WEAPONS, FLEX_ITEMS, get_rarity, SELL_RETURN_PERCENT, IMG_SHOP

WEAPONS_PER_PAGE = 6
FLEX_PER_PAGE    = 6


def shop_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Weapons", callback_data="shop_weapons_0"),
         InlineKeyboardButton("💎 Flex & VIP", callback_data="shop_flex_0")],
        [InlineKeyboardButton("❌ Close", callback_data="shop_close")]
    ])


def weapons_page_keyboard(page: int):
    keys = list(WEAPONS.keys())
    start = page * WEAPONS_PER_PAGE
    chunk = keys[start:start + WEAPONS_PER_PAGE]
    rows = []
    for i in range(0, len(chunk), 2):
        row = [InlineKeyboardButton(
            f"{WEAPONS[chunk[i]]['emoji']} {WEAPONS[chunk[i]]['name'].split(' ',1)[1]}",
            callback_data=f"shop_witem_{chunk[i]}"
        )]
        if i + 1 < len(chunk):
            row.append(InlineKeyboardButton(
                f"{WEAPONS[chunk[i+1]]['emoji']} {WEAPONS[chunk[i+1]]['name'].split(' ',1)[1]}",
                callback_data=f"shop_witem_{chunk[i+1]}"
            ))
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"shop_weapons_{page-1}"))
    if start + WEAPONS_PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"shop_weapons_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏪 Menu", callback_data="shop_main")])
    return InlineKeyboardMarkup(rows)


def flex_page_keyboard(page: int):
    keys = list(FLEX_ITEMS.keys())
    start = page * FLEX_PER_PAGE
    chunk = keys[start:start + FLEX_PER_PAGE]
    rows = []
    for i in range(0, len(chunk), 2):
        row = [InlineKeyboardButton(
            f"{FLEX_ITEMS[chunk[i]]['emoji']} {FLEX_ITEMS[chunk[i]]['name'].split(' ',1)[1]}",
            callback_data=f"shop_fitem_{chunk[i]}"
        )]
        if i + 1 < len(chunk):
            row.append(InlineKeyboardButton(
                f"{FLEX_ITEMS[chunk[i+1]]['emoji']} {FLEX_ITEMS[chunk[i+1]]['name'].split(' ',1)[1]}",
                callback_data=f"shop_fitem_{chunk[i+1]}"
            ))
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"shop_flex_{page-1}"))
    if start + FLEX_PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"shop_flex_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏪 Menu", callback_data="shop_main")])
    return InlineKeyboardMarkup(rows)


def item_keyboard(item_key: str, item_type: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 Buy", callback_data=f"shop_buy_{item_type}_{item_key}"),
        InlineKeyboardButton("◀️ Back to Shop", callback_data=f"shop_{'weapons_0' if item_type == 'w' else 'flex_0'}")
    ]])


async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🏪 <b>Shop</b>
━━━━━━━━━━━━━━━
⚔️ <b>Weapons</b> — Limited 24h, boosts kill loot
💎 <b>Flex & VIP</b> — Permanent flex items

Choose a category 👇"""
    await send_with_image(update, update.effective_chat.id, IMG_SHOP, text, reply_markup=shop_main_keyboard())


async def shop_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    data  = query.data

    async def edit(text, kb):
        try:
            await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            try:
                await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb)
            except Exception:
                pass

    if data == "shop_close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    if data == "shop_main":
        await query.answer()
        text = """🏪 <b>Shop</b>
━━━━━━━━━━━━━━━
⚔️ <b>Weapons</b> — Limited 24h, boosts kill loot
💎 <b>Flex & VIP</b> — Permanent flex items

Choose a category 👇"""
        await edit(text, shop_main_keyboard())
        return

    if data.startswith("shop_weapons_"):
        await query.answer()
        page = int(data.split("_")[-1])
        keys = list(WEAPONS.keys())
        start = page * WEAPONS_PER_PAGE
        chunk = keys[start:start + WEAPONS_PER_PAGE]
        lines = "\n".join(
            f"{WEAPONS[k]['emoji']} <b>{WEAPONS[k]['name'].split(' ',1)[1]}</b> — {fmt(WEAPONS[k]['price'])}"
            for k in chunk
        )
        text = f"⚔️ <b>Weapons</b>\n━━━━━━━━━━━━━━━\n{lines}\n\n<i>Tap to view details</i>"
        await edit(text, weapons_page_keyboard(page))
        return

    if data.startswith("shop_flex_"):
        await query.answer()
        page = int(data.split("_")[-1])
        keys = list(FLEX_ITEMS.keys())
        start = page * FLEX_PER_PAGE
        chunk = keys[start:start + FLEX_PER_PAGE]
        lines = "\n".join(
            f"{FLEX_ITEMS[k]['emoji']} <b>{FLEX_ITEMS[k]['name'].split(' ',1)[1]}</b> — {fmt(FLEX_ITEMS[k]['price'])}"
            for k in chunk
        )
        text = f"💎 <b>Flex & VIP</b>\n━━━━━━━━━━━━━━━\n{lines}\n\n<i>Tap to view details</i>"
        await edit(text, flex_page_keyboard(page))
        return

    if data.startswith("shop_witem_"):
        await query.answer()
        key  = data[len("shop_witem_"):]
        item = WEAPONS.get(key)
        if not item:
            return
        group_id = update.effective_chat.id
        udata = await get_user(user.id, group_id, user.first_name)
        bonus_pct = int(item['kill_loot_bonus'] * 100)
        text = f"""🛍️ {item['name']}
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 <b>Price:</b> {fmt(item['price'])}
🌟 <b>Rarity:</b> {get_rarity(item['price'])}
💥 <b>Buff:</b> +{bonus_pct}% Kill Loot
⏱️ <b>Life:</b> ⏳ {item['lifetime_hours']} Hours

👛 <b>Your Wallet:</b> {fmt(udata['balance'])}"""
        await edit(text, item_keyboard(key, "w"))
        return

    if data.startswith("shop_fitem_"):
        await query.answer()
        key  = data[len("shop_fitem_"):]
        item = FLEX_ITEMS.get(key)
        if not item:
            return
        group_id = update.effective_chat.id
        udata = await get_user(user.id, group_id, user.first_name)
        text = f"""🛍️ {item['name']}
━━━━━━━━━━━━━━━
📖 {item['desc']}
━━━━━━━━━━━━━━━
💰 <b>Price:</b> {fmt(item['price'])}
🌟 <b>Rarity:</b> {get_rarity(item['price'])}
⏱️ <b>Life:</b> ♾️ Permanent

👛 <b>Your Wallet:</b> {fmt(udata['balance'])}"""
        await edit(text, item_keyboard(key, "f"))
        return

    if data.startswith("shop_buy_"):
        parts    = data.split("_")
        itype    = parts[2]
        ikey     = "_".join(parts[3:])
        group_id = update.effective_chat.id
        catalog  = WEAPONS if itype == "w" else FLEX_ITEMS
        item     = catalog.get(ikey)
        if not item:
            await query.answer("❌ Item not found!", show_alert=True)
            return

        udata = await get_user(user.id, group_id, user.first_name)
        if udata["balance"] < item["price"]:
            await query.answer("❌ You can't afford this.", show_alert=True)
            return

        inventory = udata.get("inventory", {})
        if itype == "w":
            expires_at = time.time() + item["lifetime_hours"] * 3600
            inventory[ikey] = {"qty": 1, "expires_at": expires_at}
        else:
            existing = inventory.get(ikey, {})
            inventory[ikey] = {"qty": existing.get("qty", 0) + 1, "expires_at": None}

        new_balance = udata["balance"] - item["price"]
        await update_user(user.id, group_id, {"balance": new_balance, "inventory": inventory})

        await query.answer("🎉 Congratulations! Item purchased!", show_alert=True)

        # Announce in group
        try:
            await context.bot.send_message(
                chat_id=group_id,
                text=f"""🛍️ <b>New Purchase!</b>
👤 <b>{user.first_name}</b> just bought <b>{item['name']}</b>
💸 <b>Paid:</b> {fmt(item['price'])}""",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    group_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text(
            "❌ <b>Usage:</b> <code>/sell [item_name]</code>\nEx: <code>/sell cookie</code>",
            parse_mode="HTML"
        )
        return

    ikey  = context.args[0].lower()
    item  = FLEX_ITEMS.get(ikey)
    if not item:
        await update.message.reply_text("❌ <b>Only Flex & VIP items can be sold!</b>", parse_mode="HTML")
        return

    udata     = await get_user(user.id, group_id, user.first_name)
    inventory = udata.get("inventory", {})
    owned     = inventory.get(ikey, {})

    if not owned or owned.get("qty", 0) <= 0:
        await update.message.reply_text("❌ Do you want to scam me?\n❌ <b>You do not have this item.</b>", parse_mode="HTML")
        return

    sell_price  = int(item["price"] * SELL_RETURN_PERCENT)
    new_qty     = owned["qty"] - 1
    if new_qty <= 0:
        del inventory[ikey]
    else:
        inventory[ikey]["qty"] = new_qty

    new_balance = udata["balance"] + sell_price
    await update_user(user.id, group_id, {"balance": new_balance, "inventory": inventory})

    await update.message.reply_text(
        f"""💸 <b>Item Sold!</b>
━━━━━━━━━━━━━━━
🛍️ <b>Item:</b> {item['name']}
💰 <b>Received:</b> {fmt(sell_price)}
👛 <b>Balance:</b> {fmt(new_balance)}""",
        parse_mode="HTML"
    )
