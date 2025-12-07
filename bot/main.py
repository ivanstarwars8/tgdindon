import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import Config, load_config
from bot.database.queries import Database
from bot.handlers import booking, lessons, start
from bot.utils.google_calendar import build_calendar_service
from bot.utils.scheduler import build_scheduler

logging.basicConfig(level=logging.INFO)


def register_routers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(lessons.router)


async def main() -> None:
    config: Config = load_config()
    bot = Bot(token=config.bot_token, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    db = Database(config.database_path)
    await db.setup()

    calendar_service = build_calendar_service(config.credentials_file)
    scheduler = build_scheduler(bot, config.timezone)

    bot["config"] = config
    bot["db"] = db
    bot["calendar_service"] = calendar_service
    bot["scheduler"] = scheduler

    register_routers(dp)

    logging.info("Bot is starting")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
