from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from app.services.client_context import (
    answer_client_not_connected,
    get_client_from_message,
)
from app.handlers.categories import clear_add_subcategory_session
from app.keyboards.start import (
    ADD_SUBCATEGORIES_BUTTON,
    BACK_TO_MENU_BUTTON,
    CATEGORIES_BUTTON,
    HELP_BUTTON,
    SHEET_BUTTON,
    START_HERE_BUTTON,
    get_main_menu_keyboard,
    get_start_keyboard,
)
from app.services.access import deny_if_not_allowed
from app.services.google_sheets import get_categories


router = Router()
def get_main_menu_text() -> str:
    return (
        "Главное меню\n\n"
        "Что можно сделать:\n"
        "📋 Категории — посмотреть доступные подкатегории\n"
        "➕ Добавить подкатегории — добавить новые статьи в существующую категорию\n"
        "📊 Таблица — открыть Google-таблицу\n"
        "❓ Помощь — посмотреть инструкцию\n\n"
        "Чтобы добавить расход, просто напишите:\n"
        "25 000 Реклама май"
    )


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
        "Привет! Я финансовый помощник для учета расходов бизнеса.\n\n"
        "Я помогу быстро фиксировать траты в Google Sheets.\n\n"
        "Нажмите кнопку ниже, чтобы понять, как начать.",
        reply_markup=get_start_keyboard(),
    )

@router.message(F.text == START_HERE_BUTTON)
async def start_here_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await message.answer(
        "Как начать:\n\n"
        "1. Для вас будет создана Google-таблица для учета расходов.\n"
        "Открыть таблицу можно командой:\n"
        "/sheet\n\n"
        "2. Сначала нужно настроить категории расходов.\n"
        "Я пока учусь и не создаю новые категории самостоятельно, "
        "поэтому с настройкой категорий помогает Владимир: @vova_ah\n\n"
        "3. После настройки категорий вы можете сами добавлять подкатегории командой:\n"
        "/add_subcategories\n\n"
        "4. Когда категории и подкатегории настроены, просто напишите расход:\n"
        "25 000 Реклама май\n\n"
        "Можно отправить несколько расходов списком:\n"
        "1200 Связь май\n"
        "3000 Хостинг сайт\n\n"
        "5. Если вы начали действие и хотите выйти, нажмите ↩️ Назад в меню.\n\n"
        "Посмотреть доступные подкатегории:\n"
        "/categories\n\n"
        "Полная инструкция:\n"
        "/help",
        reply_markup=get_main_menu_keyboard(),
    )

@router.message(Command("menu"))
async def menu_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await message.answer(
        get_main_menu_text(),
        reply_markup=get_main_menu_keyboard(),
    )

@router.message(F.text == BACK_TO_MENU_BUTTON)
async def back_to_menu_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    user_id = message.from_user.id if message.from_user else None
    clear_add_subcategory_session(user_id)

    await message.answer(
        "Вернулся в главное меню ✅",
        reply_markup=get_main_menu_keyboard(),
    )

@router.message(Command("cancel"))
async def cancel_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    user_id = message.from_user.id if message.from_user else None
    was_cancelled = clear_add_subcategory_session(user_id)

    if was_cancelled:
        await message.answer(
            "Действие отменено ✅\n\n"
            "Чтобы открыть главное меню, напишите /menu"
        )
        return

    await message.answer(
        "Сейчас нет активного действия для отмены.\n\n"
        "Чтобы открыть главное меню, напишите /menu"
    )


@router.message(Command("categories"))
@router.message(F.text == CATEGORIES_BUTTON)
async def categories_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    client = get_client_from_message(message)

    if not client:
        await answer_client_not_connected(message)
        return

    spreadsheet_id = client["spreadsheet_id"]

    try:
        categories = get_categories(spreadsheet_id)

        if not categories:
            await message.answer(
                "Категории пока не добавлены.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        grouped_categories = {}

        for item in categories:
            group = item["group"]
            category = item["category"]
            subcategory = item["subcategory"]

            if group not in grouped_categories:
                grouped_categories[group] = {}

            if category not in grouped_categories[group]:
                grouped_categories[group][category] = []

            grouped_categories[group][category].append(subcategory)

        text = "Доступные подкатегории:\n\n"

        for group, categories_by_group in grouped_categories.items():
            text += f"{group}\n\n"

            for category, subcategories in categories_by_group.items():
                text += f"{category}:\n"

                for subcategory in subcategories:
                    text += f"- {subcategory}\n"

                text += "\n"

        text += (
            "Чтобы добавить расход, используйте подкатегорию:\n"
            "25 000 Реклама май"
        )

        await message.answer(
            text.strip(),
            reply_markup=get_main_menu_keyboard(),
        )

    except Exception as error:
        print(f"Ошибка при получении категорий: {error}")
        await message.answer(
            "Ошибка ❌. Не удалось получить список категорий.",
            reply_markup=get_main_menu_keyboard(),
        )


@router.message(Command("help"))
@router.message(F.text == HELP_BUTTON)
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
        "/menu — главное меню\n"
        "/categories — список доступных подкатегорий\n"
        "/add_subcategories — добавить подкатегории\n"
        "/sheet — ссылка на Google-таблицу\n"
        "/whoami — узнать свой Telegram ID\n"
        "/cancel — отменить текущее действие\n"
        "/help — помощь"
    )


@router.message(Command("sheet"))
@router.message(F.text == SHEET_BUTTON)
async def sheet_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    client = get_client_from_message(message)

    if not client:
        await answer_client_not_connected(message)
        return

    await message.answer(
        "Ваша Google-таблица:\n\n"
        f"{client['spreadsheet_url']}",
        reply_markup=get_main_menu_keyboard(),
    )