import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from app.config import BOT_TOKEN
from app.handlers.commands import router as commands_router
from app.handlers.categories import router as categories_router
from app.handlers.expenses import router as expenses_router


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="categories", description="Список статей и подстатей"),
        BotCommand(command="add_subcategories", description="Добавить подстатьи"),
        BotCommand(command="sheet", description="Открыть Google-таблицу"),
        BotCommand(command="whoami", description="Узнать Telegram ID"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
    ]

    await bot.set_my_commands(commands)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(commands_router)
    dp.include_router(categories_router)
    dp.include_router(expenses_router)

    await set_bot_commands(bot)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())