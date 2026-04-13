import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from database import ensure_indexes

from handlers.economy import (
    bal, daily, claim, mine, farm,
    crime, give, transfer, toprich
)
from handlers.rpg import (
    kill, rob, protect, revive, heal,
    hp, profile, topkill, ranking
)
from handlers.bank import bank, deposit, withdraw, loan, repay
from handlers.shop import shop, buy, sell, items, item_info
from handlers.social import propose, marry, divorce, couple, crush, love
from handlers.admin import ping, open_economy, close_economy, start, button_handler
from handlers.war import war, war_button_handler, warlog, wanted

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application):
    await ensure_indexes()
    logger.info("✅ MongoDB indexes ensured.")


def main():
    app = ApplicationBuilder()\
        .token(BOT_TOKEN)\
        .post_init(post_init)\
        .build()

    # Admin / misc
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("open", open_economy))
    app.add_handler(CommandHandler("close", close_economy))

    # Economy
    app.add_handler(CommandHandler("bal", bal))
    app.add_handler(CommandHandler("balance", bal))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("claim", claim))
    app.add_handler(CommandHandler("mine", mine))
    app.add_handler(CommandHandler("farm", farm))
    app.add_handler(CommandHandler("crime", crime))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("toprich", toprich))

    # RPG
    app.add_handler(CommandHandler("kill", kill))
    app.add_handler(CommandHandler("rob", rob))
    app.add_handler(CommandHandler("protect", protect))
    app.add_handler(CommandHandler("revive", revive))
    app.add_handler(CommandHandler("heal", heal))
    app.add_handler(CommandHandler("hp", hp))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("topkill", topkill))
    app.add_handler(CommandHandler("ranking", ranking))

    # War
    app.add_handler(CommandHandler("war", war))
    app.add_handler(CommandHandler("warlog", warlog))
    app.add_handler(CommandHandler("wanted", wanted))

    # Bank
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("loan", loan))
    app.add_handler(CommandHandler("repay", repay))

    # Shop
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("items", items))
    app.add_handler(CommandHandler("item", item_info))

    # Social
    app.add_handler(CommandHandler("propose", propose))
    app.add_handler(CommandHandler("marry", marry))
    app.add_handler(CommandHandler("divorce", divorce))
    app.add_handler(CommandHandler("couple", couple))
    app.add_handler(CommandHandler("crush", crush))
    app.add_handler(CommandHandler("love", love))

    # Callback handlers
    app.add_handler(CallbackQueryHandler(war_button_handler, pattern="^war_"))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Bot started! Polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
