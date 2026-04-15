import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from config import BOT_TOKEN
from database import ensure_indexes
from handlers.economy import bal, bal_flex_button, daily, claim, mine, farm, crime, give, transfer, toprich, deduct
from handlers.rpg import kill, rob, protect, revive, hp, heal, profile, topkill, ranking
from handlers.bank import bank, deposit, withdraw, loan, repay
from handlers.shop import shop, shop_button_handler, sell
from handlers.social import propose, propose_button_handler, marry, divorce, couple, crush, love
from handlers.admin import ping, open_economy, close_economy, start, button_handler, addsudo, rmsudo, sudolist
from handlers.war import war_cmd, war_button_handler, warlog, wanted
from handlers.gift import gift_cmd, gift_button_handler, gift_message_handler

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)


async def post_init(app):
    await ensure_indexes()


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # ── Admin / Group ──────────────────────────────────────────
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("ping",     ping))
    app.add_handler(CommandHandler("open",     open_economy))
    app.add_handler(CommandHandler("close",    close_economy))

    # ── Owner / Sudo Management ────────────────────────────────
    app.add_handler(CommandHandler("addsudo",  addsudo))
    app.add_handler(CommandHandler("rmsudo",   rmsudo))
    app.add_handler(CommandHandler("sudolist", sudolist))
    app.add_handler(CommandHandler("deduct",   deduct))

    # ── Economy ────────────────────────────────────────────────
    app.add_handler(CommandHandler("bal",      bal))
    app.add_handler(CommandHandler("balance",  bal))
    app.add_handler(CommandHandler("daily",    daily))
    app.add_handler(CommandHandler("claim",    claim))
    app.add_handler(CommandHandler("mine",     mine))
    app.add_handler(CommandHandler("farm",     farm))
    app.add_handler(CommandHandler("crime",    crime))
    app.add_handler(CommandHandler("give",     give))
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("toprich",  toprich))

    # ── RPG ────────────────────────────────────────────────────
    app.add_handler(CommandHandler("kill",     kill))
    app.add_handler(CommandHandler("rob",      rob))
    app.add_handler(CommandHandler("protect",  protect))
    app.add_handler(CommandHandler("revive",   revive))
    app.add_handler(CommandHandler("heal",     heal))
    app.add_handler(CommandHandler("hp",       hp))
    app.add_handler(CommandHandler("profile",  profile))
    app.add_handler(CommandHandler("topkill",  topkill))
    app.add_handler(CommandHandler("ranking",  ranking))

    # ── War ────────────────────────────────────────────────────
    app.add_handler(CommandHandler("war",      war_cmd))
    app.add_handler(CommandHandler("warlog",   warlog))
    app.add_handler(CommandHandler("wanted",   wanted))

    # ── Bank ───────────────────────────────────────────────────
    app.add_handler(CommandHandler("bank",     bank))
    app.add_handler(CommandHandler("deposit",  deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("loan",     loan))
    app.add_handler(CommandHandler("repay",    repay))

    # ── Shop ───────────────────────────────────────────────────
    app.add_handler(CommandHandler("shop",     shop))
    app.add_handler(CommandHandler("sell",     sell))

    # ── Gift ───────────────────────────────────────────────────
    app.add_handler(CommandHandler("gift",     gift_cmd))
    # Capture text replies for gift message input
    # (only when user is in a gift flow — handler checks user_data internally)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        gift_message_handler
    ))

    # ── Social ─────────────────────────────────────────────────
    app.add_handler(CommandHandler("propose",  propose))
    app.add_handler(CommandHandler("marry",    marry))
    app.add_handler(CommandHandler("divorce",  divorce))
    app.add_handler(CommandHandler("couple",   couple))
    app.add_handler(CommandHandler("crush",    crush))
    app.add_handler(CommandHandler("love",     love))

    # ── Callbacks ──────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(war_button_handler,     pattern="^war_"))
    app.add_handler(CallbackQueryHandler(propose_button_handler, pattern="^prop_"))
    app.add_handler(CallbackQueryHandler(shop_button_handler,    pattern="^shop_"))
    app.add_handler(CallbackQueryHandler(gift_button_handler,    pattern="^gift_"))
    app.add_handler(CallbackQueryHandler(bal_flex_button,        pattern="^bal_flex_"))
    app.add_handler(CallbackQueryHandler(button_handler,         pattern="^(menu_|cmd_)"))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
