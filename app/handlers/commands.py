from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from app.config import SPREADSHEET_ID
from app.services.access import deny_if_not_allowed
from app.services.google_sheets import get_categories


router = Router()


@router.message(Command("whoami"))
async def whoami_handler(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else None

    if username:
        await message.answer(
            "Ваш Telegram ID:\n\n"
            f"{user_id}\n\n"
            f"Username: @{username}"
        )
    else:
        await message.answer(
            "Ваш Telegram ID:\n\n"
            f"{user_id}"
        )


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await message.answer(
        "Привет! Я финансовый бот для учета расходов.\n\n"
        "MVP запущен 🚀\n\n"
        "Напиши расход в формате:\n"
        "1500 аренда\n"
        "10 000 реклама\n"
        "10000,50 кофе"
    )


@router.message(Command("categories"))
async def categories_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    try:
        categories = get_categories()

        if not categories:
            await message.answer("Категории пока не добавлены.")
            return

        grouped_categories = {}

        for item in categories:
            group = item["group"]
            category = item["category"]
            subcategory = item["subcategory"]

            key = f"{group} / {category}"

            if key not in grouped_categories:
                grouped_categories[key] = []

            grouped_categories[key].append(subcategory)

        text = "Доступные подкатегории:\n\n"

        for key, subcategories in grouped_categories.items():
            text += f"{key}:\n"

            for subcategory in subcategories:
                text += f"- {subcategory}\n"

            text += "\n"

        await message.answer(text.strip())

    except Exception as error:
        print(f"Ошибка при получении категорий: {error}")
        await message.answer("Ошибка ❌. Не удалось получить список категорий.")


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await message.answer(
        "Как добавить расход:\n\n"
        "Напиши сумму и подкатегорию:\n"
        "25 000 Реклама май\n"
        "10 000 Аренда офиса\n"
        "1500 Кофе встреча с клиентом\n\n"
        "Важно:\n"
        "- сумма должна быть в начале сообщения\n"
        "- подкатегория должна совпадать с одной из подкатегорий в таблице\n"
        "- комментарий можно писать после подкатегории\n\n"
        "Команды:\n"
        "/start — запуск бота\n"
        "/categories — список доступных подкатегорий\n"
        "/add_subcategories — добавить подкатегории\n"
        "/sheet — ссылка на Google-таблицу\n"
        "/whoami — узнать свой Telegram ID\n"
        "/help — помощь"
    )


@router.message(Command("sheet"))
async def sheet_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    sheet_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"

    await message.answer(
        "Ваша Google-таблица:\n\n"
        f"{sheet_url}"
    )