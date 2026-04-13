from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user, update_user
from utils.helpers import check_economy, format_coins
from config import SHOP_ITEMS, WEAPON_REPAIR_COST


async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weapons = {k: v for k, v in SHOP_ITEMS.items() if v["type"] == "weapon"}
    armors = {k: v for k, v in SHOP_ITEMS.items() if v["type"] == "armor"}
    potions = {k: v for k, v in SHOP_ITEMS.items() if v["type"] == "potion"}

    text = "🏪 <b>Shop</b>\n━━━━━━━━━━━━━━━\n\n"

    text += "⚔️ <b>Weapons</b>\n"
    for key, item in weapons.items():
        text += (
            f"  {item['name']}\n"
            f"  💰 Price: {format_coins(item['price'])} | ⚔️ Damage: {item['damage']}\n"
            f"  📝 {item['description']}\n"
            f"  🛒 Buy: <code>/buy {key}</code>\n\n"
        )

    text += "🛡️ <b>Armor</b>\n"
    for key, item in armors.items():
        text += (
            f"  {item['name']}\n"
            f"  💰 Price: {format_coins(item['price'])} | 🛡️ Defense: {item['defense']} | ❤️ HP: +{item['hp_bonus']}\n"
            f"  📝 {item['description']}\n"
            f"  🛒 Buy: <code>/buy {key}</code>\n\n"
        )

    text += "🧪 <b>Potions</b>\n"
    for key, item in potions.items():
        text += (
            f"  {item['name']}\n"
            f"  💰 Price: {format_coins(item['price'])} | ❤️ HP Restore: +{item['hp_bonus']}\n"
            f"  📝 {item['description']}\n"
            f"  🛒 Buy: <code>/buy {key}</code>\n\n"
        )

    await update.message.reply_text(text, parse_mode="HTML")


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text("❌ Usage: <code>/buy [item_name]</code>\nCheck /shop for available items.", parse_mode="HTML")
        return

    item_key = context.args[0].lower()
    if item_key not in SHOP_ITEMS:
        await update.message.reply_text(f"❌ Item <code>{item_key}</code> not found! Check /shop.", parse_mode="HTML")
        return

    item = SHOP_ITEMS[item_key]
    data = await get_user(user.id, group_id, user.first_name)

    if data["balance"] < item["price"]:
        await update.message.reply_text(
            f"❌ Not enough coins!\n"
            f"💰 {item['name']} costs: {format_coins(item['price'])}\n"
            f"👛 Your balance: {format_coins(data['balance'])}",
            parse_mode="HTML"
        )
        return

    inventory = data.get("inventory", {})
    inventory[item_key] = inventory.get(item_key, 0) + 1
    new_balance = data["balance"] - item["price"]

    update_data = {"balance": new_balance, "inventory": inventory}

    # Auto equip if better
    if item["type"] == "weapon" and not data.get("equipped_weapon"):
        update_data["equipped_weapon"] = item_key
    if item["type"] == "armor" and not data.get("equipped_armor"):
        update_data["equipped_armor"] = item_key

    # Potions apply instantly
    if item["type"] == "potion":
        new_hp = min(data["hp"] + item["hp_bonus"], data["max_hp"])
        update_data["hp"] = new_hp

    await update_user(user.id, group_id, update_data)

    text = (
        f"✅ Purchased {item['name']}!\n"
        f"💸 Cost: {format_coins(item['price'])}\n"
        f"👛 Balance: {format_coins(new_balance)}\n"
    )
    if item["type"] == "potion":
        text += f"❤️ HP restored! Current HP: {update_data.get('hp', data['hp'])}"
    elif item["type"] in ["weapon", "armor"] and not data.get(f"equipped_{item['type']}"):
        text += f"🔧 Auto-equipped as your {item['type']}!"

    await update.message.reply_text(text, parse_mode="HTML")


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_economy(update):
        return
    user = update.effective_user
    group_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text("❌ Usage: <code>/sell [item_name]</code>", parse_mode="HTML")
        return

    item_key = context.args[0].lower()
    if item_key not in SHOP_ITEMS:
        await update.message.reply_text(f"❌ Item <code>{item_key}</code> not found!", parse_mode="HTML")
        return

    data = await get_user(user.id, group_id, user.first_name)
    inventory = data.get("inventory", {})

    if inventory.get(item_key, 0) <= 0:
        await update.message.reply_text(f"❌ You don't have <b>{SHOP_ITEMS[item_key]['name']}</b>!", parse_mode="HTML")
        return

    item = SHOP_ITEMS[item_key]
    sell_price = int(item["price"] * 0.5)
    inventory[item_key] -= 1
    if inventory[item_key] == 0:
        del inventory[item_key]

    new_balance = data["balance"] + sell_price
    update_data = {"balance": new_balance, "inventory": inventory}

    # Unequip if sold equipped item
    if data.get("equipped_weapon") == item_key and inventory.get(item_key, 0) == 0:
        update_data["equipped_weapon"] = None
    if data.get("equipped_armor") == item_key and inventory.get(item_key, 0) == 0:
        update_data["equipped_armor"] = None

    await update_user(user.id, group_id, update_data)
    await update.message.reply_text(
        f"💰 Sold {item['name']} for {format_coins(sell_price)}!\n"
        f"👛 Balance: {format_coins(new_balance)}",
        parse_mode="HTML"
    )


async def items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    data = await get_user(user.id, group_id, user.first_name)
    inventory = data.get("inventory", {})

    if not inventory:
        await update.message.reply_text("🎒 Your inventory is empty! Visit /shop to buy items.")
        return

    text = f"🎒 <b>{user.first_name}'s Inventory</b>\n━━━━━━━━━━━━━━━\n"
    equipped_weapon = data.get("equipped_weapon")
    equipped_armor = data.get("equipped_armor")

    for key, qty in inventory.items():
        if key not in SHOP_ITEMS:
            continue
        item = SHOP_ITEMS[key]
        equipped = ""
        if key == equipped_weapon:
            equipped = " ✅ [Equipped]"
        elif key == equipped_armor:
            equipped = " ✅ [Equipped]"
        text += f"  {item['name']} x{qty}{equipped}\n"

    text += f"\n⚔️ Weapon: {SHOP_ITEMS[equipped_weapon]['name'] if equipped_weapon and equipped_weapon in SHOP_ITEMS else 'None'}"
    text += f"\n🛡️ Armor: {SHOP_ITEMS[equipped_armor]['name'] if equipped_armor and equipped_armor in SHOP_ITEMS else 'None'}"

    await update.message.reply_text(text, parse_mode="HTML")


async def item_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: <code>/item [item_name]</code>", parse_mode="HTML")
        return

    item_key = context.args[0].lower()
    if item_key not in SHOP_ITEMS:
        await update.message.reply_text(f"❌ Item not found! Check /shop.", parse_mode="HTML")
        return

    item = SHOP_ITEMS[item_key]
    text = (
        f"{item['name']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 {item['description']}\n"
        f"💰 Price: {format_coins(item['price'])}\n"
        f"🔄 Sell: {format_coins(int(item['price'] * 0.5))}\n"
    )
    if item["damage"]:
        text += f"⚔️ Damage: {item['damage']}\n"
    if item["defense"]:
        text += f"🛡️ Defense: {item['defense']}\n"
    if item["hp_bonus"]:
        text += f"❤️ HP Bonus: +{item['hp_bonus']}\n"
    text += f"🔧 Weapon repair cost: {format_coins(WEAPON_REPAIR_COST)}"

    await update.message.reply_text(text, parse_mode="HTML")
