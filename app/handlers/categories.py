import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards.start import (
    ADD_SUBCATEGORIES_BUTTON,
    get_main_menu_keyboard,
    get_scenario_keyboard,
)

from app.services.client_context import (
    answer_client_not_connected,
    get_client_from_message,
)

from app.services.access import deny_if_not_allowed
from app.services.google_sheets import (
    append_category_row,
    find_category_by_name,
    get_subcategories_for_category,
    get_unique_categories,
)


router = Router()


add_subcategory_sessions = {}
def has_add_subcategory_session(user_id: int | None) -> bool:
    if user_id is None:
        return False

    return user_id in add_subcategory_sessions


def clear_add_subcategory_session(user_id: int | None) -> bool:
    if user_id is None:
        return False

    if user_id in add_subcategory_sessions:
        del add_subcategory_sessions[user_id]
        return True

    return False


def build_categories_list_text(spreadsheet_id: str) -> str:
    categories = get_unique_categories(spreadsheet_id)

    if not categories:
        return "Статьи пока не добавлены."

    text = "Выберите статью из списка:\n\n"

    for item in categories:
        text += f"- {item['category']}\n"

    return text.strip()


def parse_subcategories(text: str) -> list[str]:
    """
    Поддерживаем ввод:
    Курьер, Почта
    или:
    Курьер
    Почта
    """

    if not text:
        return []

    parts = re.split(r"[,\n]+", text)

    subcategories = []

    for part in parts:
        value = part.strip()

        if value:
            subcategories.append(value)

    return subcategories


@router.message(Command("add_subcategories"))
@router.message(lambda message: message.text == ADD_SUBCATEGORIES_BUTTON)
async def add_subcategories_start_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    client = get_client_from_message(message)

    if not client:
        await answer_client_not_connected(message)
        return

    spreadsheet_id = client["spreadsheet_id"]

    user_id = message.from_user.id if message.from_user else None

    if user_id is None:
        await message.answer("Ошибка ❌. Не удалось определить пользователя.")
        return

    add_subcategory_sessions[user_id] = {
    "step": "waiting_category",
    "spreadsheet_id": spreadsheet_id,
    }

    await message.answer(
        "Добавление подстатей.\n\n"
        f"{build_categories_list_text(spreadsheet_id)}\n\n"
        "Напишите название статьи, куда нужно добавить подстатьи.",
        reply_markup=get_scenario_keyboard(),
    )


@router.message(lambda message: message.from_user and message.from_user.id in add_subcategory_sessions)
async def add_subcategories_flow_handler(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None

    if user_id is None:
        return

    session = add_subcategory_sessions.get(user_id)

    spreadsheet_id = session["spreadsheet_id"]

    if not session:
        return

    if await deny_if_not_allowed(message):
        return

    text = message.text.strip() if message.text else ""

    if session["step"] == "waiting_category":
        category = find_category_by_name(text, spreadsheet_id)

        if not category:
            await message.answer(
                "Ошибка ❌. Такая статья не найдена.\n\n"
                f"{build_categories_list_text(spreadsheet_id)}"
            )
            return

        session["step"] = "waiting_subcategories"
        session["group"] = category["group"]
        session["category"] = category["category"]

        await message.answer(
            f"Статья выбрана: {category['category']}\n\n"
            "Введите подстатьи через запятую или с новой строки:\n\n"
            "Например:\n"
            "Курьер, Почта",
            reply_markup=get_scenario_keyboard(),
        )
        return

    if session["step"] == "waiting_subcategories":
        group = session["group"]
        category = session["category"]

        new_subcategories = parse_subcategories(text)

        if not new_subcategories:
            await message.answer(
                "Ошибка ❌. Не удалось распознать подстатьи.\n\n"
                "Введите одну или несколько подстатей через запятую.",
            )
            return

        existing_subcategories = get_subcategories_for_category(category, spreadsheet_id)
        existing_lower = {item.lower() for item in existing_subcategories}

        added = []
        skipped = []

        for subcategory in new_subcategories:
            if subcategory.lower() in existing_lower:
                skipped.append(subcategory)
                continue

            append_category_row(spreadsheet_id, group, category, subcategory)
            added.append(subcategory)
            existing_lower.add(subcategory.lower())

        del add_subcategory_sessions[user_id]

        response = ""

        if added:
            response += "Добавлено ✅\n\n"
            response += f"Статья: {category}\n"
            for item in added:
                response += f"- {item}\n"

        if skipped:
            if response:
                response += "\n"

            response += "Уже существовали и не были добавлены:\n"
            for item in skipped:
                response += f"- {item}\n"

        await message.answer(
           response.strip(),
           reply_markup=get_main_menu_keyboard(),
        )