import asyncio

from aiogram import Bot, Dispatcher

from app.config import BOT_TOKEN
from app.handlers.commands import router as commands_router
from app.handlers.expenses import router as expenses_router
from app.handlers.categories import router as categories_router


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(commands_router)
    dp.include_router(categories_router)
    dp.include_router(expenses_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())