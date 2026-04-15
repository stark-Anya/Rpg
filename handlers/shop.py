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
        [
            InlineKeyboardButton("⚔️ 𝐖𝐞𝐚𝐩𝐨𝐧𝐬", callback_data="shop_weapons_0"),
            InlineKeyboardButton("💎 𝐕𝐈𝐏 𝐅𝐥𝐞𝐱 𝐙𝐨𝐧𝐞", callback_data="shop_flex_0")
        ],
        [InlineKeyboardButton("🔙 𝐂𝐥𝐨𝐬𝐞", callback_data="shop_close")]
    ])


def weapons_page_keyboard(page: int):
    keys  = list(WEAPONS.keys())
    start = page * WEAPONS_PER_PAGE
    chunk = keys[start:start + WEAPONS_PER_PAGE]
    rows  = []

    for i in range(0, len(chunk), 2):
        row = [InlineKeyboardButton(
            f"{WEAPONS[chunk[i]]['emoji']} {WEAPONS[chunk[i]]['name'].split(' ', 1)[1]}",
            callback_data=f"shop_witem_{chunk[i]}"
        )]
        if i + 1 < len(chunk):
            row.append(InlineKeyboardButton(
                f"{WEAPONS[chunk[i+1]]['emoji']} {WEAPONS[chunk[i+1]]['name'].split(' ', 1)[1]}",
                callback_data=f"shop_witem_{chunk[i+1]}"
            ))
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ 𝐏ʀᴇᴠ", callback_data=f"shop_weapons_{page-1}"))
    if start + WEAPONS_PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("𝐍ᴇxᴛ ▶️", callback_data=f"shop_weapons_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("🏪 𝐁ᴀᴄᴋ 𝐓ᴏ 𝐒ʜᴏᴘ", callback_data="shop_main")])
    return InlineKeyboardMarkup(rows)


def flex_page_keyboard(page: int):
    keys  = list(FLEX_ITEMS.keys())
    start = page * FLEX_PER_PAGE
    chunk = keys[start:start + FLEX_PER_PAGE]
    rows  = []

    for i in range(0, len(chunk), 2):
        row = [InlineKeyboardButton(
            f"{FLEX_ITEMS[chunk[i]]['emoji']} {FLEX_ITEMS[chunk[i]]['name'].split(' ', 1)[1]}",
            callback_data=f"shop_fitem_{chunk[i]}"
        )]
        if i + 1 < len(chunk):
            row.append(InlineKeyboardButton(
                f"{FLEX_ITEMS[chunk[i+1]]['emoji']} {FLEX_ITEMS[chunk[i+1]]['name'].split(' ', 1)[1]}",
                callback_data=f"shop_fitem_{chunk[i+1]}"
            ))
        rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ 𝐏ʀᴇᴠ", callback_data=f"shop_flex_{page-1}"))
    if start + FLEX_PER_PAGE < len(keys):
        nav.append(InlineKeyboardButton("𝐍ᴇxᴛ ▶️", callback_data=f"shop_flex_{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("🏪 𝐁ᴀᴄᴋ 𝐓ᴏ 𝐒ʜᴏᴘ", callback_data="shop_main")])
    return InlineKeyboardMarkup(rows)


def item_action_keyboard(item_key: str, item_type: str):
    back_data = "shop_weapons_0" if item_type == "w" else "shop_flex_0"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("💳 Buy Now", callback_data=f"shop_buy_{item_type}_{item_key}"),
        InlineKeyboardButton("◀️ Back", callback_data=back_data)
    ]])


async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🏪 <b>Shop</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
⚔️ <b>Weapons</b>
└ Boosts kill loot | Lasts 24h

💎 <b>Flex & VIP</b>
└ Permanent collectibles | Show off your wealth

Choose a category 👇"""
    await send_with_image(update, update.effective_chat.id, IMG_SHOP, text, reply_markup=shop_main_keyboard())


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
        text = """🏪 <b>Shop</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
⚔️ <b>Weapons</b>
└ Boosts kill loot | Lasts 24h

💎 <b>Flex & VIP</b>
└ Permanent collectibles | Show off your wealth

Choose a category 👇"""
        await edit(text, shop_main_keyboard())
        return

    # ── Weapons List ───────────────────────────────────────────
    if data.startswith("shop_weapons_"):
        await query.answer()
        page  = int(data.split("_")[-1])
        keys  = list(WEAPONS.keys())
        start = page * WEAPONS_PER_PAGE
        chunk = keys[start:start + WEAPONS_PER_PAGE]
        total = len(keys)
        pages = (total + WEAPONS_PER_PAGE - 1) // WEAPONS_PER_PAGE

        lines = "\n".join(
            f"{WEAPONS[k]['emoji']} <b>{WEAPONS[k]['name'].split(' ',1)[1]}</b>\n"
            f"   └ {fmt(WEAPONS[k]['price'])} · +{int(WEAPONS[k]['kill_loot_bonus']*100)}% loot · {get_rarity(WEAPONS[k]['price'])}"
            for k in chunk
        )
        text = f"⚔️ <b>Weapons</b>  <i>({page+1}/{pages})</i>\n◈ ━━━━━━ ⸙ ━━━━━━ ◈\n{lines}\n\n<i>Tap to view & buy</i>"
        await edit(text, weapons_page_keyboard(page))
        return

    # ── Flex List ──────────────────────────────────────────────
    if data.startswith("shop_flex_"):
        await query.answer()
        page  = int(data.split("_")[-1])
        keys  = list(FLEX_ITEMS.keys())
        start = page * FLEX_PER_PAGE
        chunk = keys[start:start + FLEX_PER_PAGE]
        total = len(keys)
        pages = (total + FLEX_PER_PAGE - 1) // FLEX_PER_PAGE

        lines = "\n".join(
            f"{FLEX_ITEMS[k]['emoji']} <b>{FLEX_ITEMS[k]['name'].split(' ',1)[1]}</b>\n"
            f"   └ {fmt(FLEX_ITEMS[k]['price'])} · {get_rarity(FLEX_ITEMS[k]['price'])} · ♾️ Permanent"
            for k in chunk
        )
        text = f"💎 <b>Flex & VIP</b>  <i>({page+1}/{pages})</i>\n◈ ━━━━━━ ⸙ ━━━━━━ ◈\n{lines}\n\n<i>Tap to view & buy</i>"
        await edit(text, flex_page_keyboard(page))
        return

    # ── Weapon Detail ──────────────────────────────────────────
    if data.startswith("shop_witem_"):
        await query.answer()
        key  = data[len("shop_witem_"):]
        item = WEAPONS.get(key)
        if not item:
            return

        udata = await get_user(user.id, group_id, user.first_name)
        owned = udata.get("inventory", {}).get(key, {})
        owned_str = ""
        if owned.get("qty", 0) > 0 and owned.get("expires_at"):
            rem = int(owned["expires_at"] - time.time())
            if rem > 0:
                owned_str = f"\n✅ <b>You own this!</b> Expires in {rem//3600}h {(rem%3600)//60}m"
            else:
                owned_str = "\n⏰ <b>Your copy expired.</b>"

        text = f"""{item['emoji']} <b>{item['name']}</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
📖 {item['desc']}
◈ ━━━━━━ ⸙ ━━━━━━ ◈
💰 Price: {fmt(item['price'])}
🌟 Rarity: {get_rarity(item['price'])}
💥 Kill Loot Bonus: +{int(item['kill_loot_bonus']*100)}%
⏱️ Duration: {item['lifetime_hours']}h
◈ ━━━━━━ ⸙ ━━━━━━ ◈
👛 Your wallet: {fmt(udata['balance'])}{owned_str}"""
        await edit(text, item_action_keyboard(key, "w"))
        return

    # ── Flex Detail ────────────────────────────────────────────
    if data.startswith("shop_fitem_"):
        await query.answer()
        key  = data[len("shop_fitem_"):]
        item = FLEX_ITEMS.get(key)
        if not item:
            return

        udata = await get_user(user.id, group_id, user.first_name)
        owned_qty = udata.get("inventory", {}).get(key, {}).get("qty", 0)
        owned_str = f"\n✅ <b>You own {owned_qty}x</b>" if owned_qty > 0 else ""

        text = f"""{item['emoji']} <b>{item['name']}</b>
◈ ━━━━━━ ⸙ ━━━━━━ ◈
📖 {item['desc']}
◈ ━━━━━━ ⸙ ━━━━━━ ◈
💰 Price: {fmt(item['price'])}
🌟 Rarity: {get_rarity(item['price'])}
⏱️ Duration: ♾️ Permanent
◈ ━━━━━━ ⸙ ━━━━━━ ◈
👛 Your wallet: {fmt(udata['balance'])}{owned_str}"""
        await edit(text, item_action_keyboard(key, "f"))
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

        udata = await get_user(user.id, group_id, user.first_name)
        if udata["balance"] < item["price"]:
            await query.answer(
                f"❌ Not enough coins!\nNeed: {fmt(item['price'])} | Have: {fmt(udata['balance'])}",
                show_alert=True
            )
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
        await query.answer(f"✅ {item['name']} purchased!", show_alert=True)

        try:
            await context.bot.send_message(
                chat_id=group_id,
                text=f"""🛍️ <b>New Purchase!</b>
👤 <b>{user.first_name}</b> bought <b>{item['name']}</b>
💸 Paid: {fmt(item['price'])}""",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    group_id = update.effective_chat.id

    if not context.args:
        lines = "\n".join(f"<code>/sell {k}</code> — {v['name']}" for k, v in list(FLEX_ITEMS.items())[:5])
        await update.message.reply_text(
            f"❌ Usage: <code>/sell [item_key]</code>\n\nExamples:\n{lines}",
            parse_mode="HTML"
        )
        return

    ikey = context.args[0].lower()
    item = FLEX_ITEMS.get(ikey)

    if not item:
        await update.message.reply_text(
            "❌ Only Flex & VIP items can be sold!\nCheck /shop for item keys.",
            parse_mode="HTML"
        )
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
◈ ━━━━━━ ⸙ ━━━━━━ ◈
🛍️ {item['name']}
💰 Received: {fmt(sell_price)} (85% of buy price)
👛 Balance: {fmt(new_balance)}""",
        parse_mode="HTML"
    )
