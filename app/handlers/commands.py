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
from app.database.clients import create_or_update_client
from app.services.google_drive import copy_template_spreadsheet

from app.services.access import deny_if_not_allowed
from app.services.google_sheets import get_categories


router = Router()
def get_main_menu_text() -> str:
    return (
        "Главное меню\n\n"
        "Что можно сделать:\n"
        "📋 Статьи — посмотреть доступные статьи и подстатьи\n"
        "➕ Добавить подстатьи — добавить новые подстатьи\n"
        "📊 Таблица — открыть Google-таблицу и Фин отчет\n"
        "❓ Помощь — посмотреть инструкцию\n\n"
        "Чтобы добавить расход, напишите сумму в начале строки:\n"
        "25000 Реклама май\n\n"
        "Можно отправить несколько расходов списком:\n"
        "1200 Связь май\n"
        "3000 Кофе встреча"
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

    existing_client = get_client_from_message(message)

    if existing_client:
        await message.answer(
           "Готово ✅\n\n"
           "Я создал для вас Google-таблицу для учета расходов.\n\n"
           "Сейчас бот умеет записывать расходы в таблицу. "
           "Финансовый результат можно посмотреть на листе «Фин отчет».\n\n"
           "В таблицу уже добавлен базовый набор статей и подстатей, "
           "чтобы вы могли сразу попробовать учет.\n\n"
           "Что сделать дальше:\n"
           "1. Откройте таблицу кнопкой «📊 Таблица»\n"
           "2. Посмотрите доступные статьи через «📋 Статьи»\n"
           "3. Отправьте расход сообщением, начиная с суммы:\n"
           "25 000 Реклама май\n\n"
           "Можно отправить несколько расходов списком:\n"
           "1200 Связь май\n"
           "3000 Кофе встреча\n\n"
           "Если нужной подстатьи нет, нажмите «➕ Добавить подстатьи».\n\n"
           "Важно: доходы пока можно добавить вручную в таблице "
           "для проверки финансового результата.",
           reply_markup=get_main_menu_keyboard(existing_client.get("custom_mode", "core")),
        )
        return

    telegram_user = message.from_user

    if not telegram_user:
        await message.answer("Ошибка ❌. Не удалось определить пользователя.")
        return

    await message.answer(
        "Минутку, создаю Google-таблицу для вашего учета ⏳"
    )

    try:
        username = telegram_user.username
        first_name = telegram_user.first_name
        telegram_id = telegram_user.id

        client_name = first_name or "Client"

        if username:
            spreadsheet_title = f"Finance Bot — {client_name} (@{username}) — {telegram_id}"
        else:
            spreadsheet_title = f"Finance Bot — {client_name} — {telegram_id}"

        new_sheet = copy_template_spreadsheet(spreadsheet_title)

        client = create_or_update_client(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            spreadsheet_id=new_sheet["spreadsheet_id"],
        )

        await message.answer(
            "Готово ✅\n\n"
            "Я создал для вас Google-таблицу для учета расходов.\n\n"
            "В таблицу уже добавлен базовый набор статей и подстатей, "
            "чтобы вы могли сразу попробовать учет.\n\n"
            "Открыть таблицу можно кнопкой «📊 Таблица» или командой:\n"
            "/sheet\n\n"
            "Посмотреть доступные статьи и подстатьи:\n"
            "/categories\n\n"
            "Чтобы добавить новые подстатьи:\n"
            "/add_subcategories\n\n"
            "Когда статьи и подстатьи настроены, просто напишите расход:\n"
            "25 000 Реклама май\n\n"
            "Можно отправить несколько расходов списком:\n"
            "1200 Связь май\n"
            "3000 Кофе встреча\n\n"
            "Пока я учусь, группы и статьи помогает настраивать Владимир: @vova_ah",
            reply_markup=get_main_menu_keyboard(client.get("custom_mode", "core")),
        )

        print(
            "Новый клиент создан ✅ "
            f"telegram_id={client['telegram_id']} "
            f"spreadsheet_id={client['spreadsheet_id']}"
        )

    except Exception as error:
        print(f"Ошибка при создании клиентской таблицы: {error}")

        await message.answer(
            "Ошибка ❌. Не удалось создать таблицу автоматически.\n\n"
            "Пожалуйста, напишите Владимиру: @vova_ah"
        )

@router.message(Command("menu"))
async def menu_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    client = get_client_from_message(message)
    custom_mode = client.get("custom_mode", "core") if client else "core"

    await message.answer(
        get_main_menu_text(),
        reply_markup=get_main_menu_keyboard(custom_mode),
    )

@router.message(F.text == BACK_TO_MENU_BUTTON)
async def back_to_menu_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    user_id = message.from_user.id if message.from_user else None
    clear_add_subcategory_session(user_id)

    await message.answer(
        "Вернулся в главное меню ✅",
        reply_markup=get_main_menu_keyboard(existing_client.get("custom_mode", "core")),
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
                "Статьи пока не добавлены.",
                reply_markup=get_main_menu_keyboard(existing_client.get("custom_mode", "core")),
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

        text = "Доступные статьи и подстатьи:\n\n"

        for group, categories_by_group in grouped_categories.items():
            text += f"{group}\n\n"

            for category, subcategories in categories_by_group.items():
                text += f"{category}:\n"

                for subcategory in subcategories:
                    text += f"- {subcategory}\n"

                text += "\n"

        text += (
            "Чтобы добавить расход, напишите сумму в начале строки "
            "и используйте одну из подстатей выше:\n\n"
            "25 000 Реклама май"
        )

        await message.answer(
            text.strip(),
            reply_markup=get_main_menu_keyboard(existing_client.get("custom_mode", "core")),
        )

    except Exception as error:
        print(f"Ошибка при получении статей: {error}")
        await message.answer(
            "Ошибка ❌. Не удалось получить список статей.",
            reply_markup=get_main_menu_keyboard(existing_client.get("custom_mode", "core")),
        )


@router.message(Command("help"))
@router.message(F.text == HELP_BUTTON)
async def help_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    await message.answer(
        "❓ Помощь\n\n"
        "1. Как добавить расход\n"
        "Напишите сумму в начале строки:\n\n"
        "25 000 Реклама май\n"
        "10 000 Аренда офиса\n"
        "1500 Кофе встреча с клиентом\n\n"
        "2. Можно отправить несколько расходов сразу\n\n"
        "1200 Связь май\n"
        "3000 Хостинг сайт\n"
        "400 Кофе\n\n"
        "3. Если бот не понял расход\n"
        "Проверьте:\n"
        "— сумма стоит первой;\n"
        "— подстатья есть в списке «📋 Статьи»;\n"
        "— если подстатьи нет, добавьте ее через «➕ Добавить подстатьи».\n\n"
        "4. Где смотреть результат\n"
        "Откройте «📊 Таблица».\n"
        "Расходы попадают в «Журнал операций», а итог — в «Фин отчет».\n\n"
        "Важно: сейчас бот записывает расходы. "
        "Доходы можно добавить вручную в таблице для проверки финансового результата.",
        reply_markup=get_main_menu_keyboard(existing_client.get("custom_mode", "core")),
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
        reply_markup=get_main_menu_keyboard(existing_client.get("custom_mode", "core")),
    )