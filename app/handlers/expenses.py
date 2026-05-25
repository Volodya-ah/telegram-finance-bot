from datetime import datetime

from aiogram import Router
from aiogram.types import Message

from app.services.access import deny_if_not_allowed
from app.services.client_context import (
    answer_client_not_connected,
    get_client_from_message,
)
from app.keyboards.start import get_main_menu_keyboard
from app.services.google_sheets import (
    append_operation_to_sheet,
    find_category_by_comment,
)
from app.services.parser import (
    format_amount_for_google_sheets,
    format_amount_for_user,
    parse_expense,
)


router = Router()


def build_operation(parsed_expense: dict, spreadsheet_id: str) -> dict:
    now = datetime.now()
    operation_id = f"exp_{now.strftime('%Y%m%d_%H%M%S_%f')}"

    original_comment = parsed_expense["comment"]
    matched_category = find_category_by_comment(original_comment, spreadsheet_id)

    group = ""
    category = ""
    subcategory = ""
    comment = original_comment

    if matched_category:
        group = matched_category["group"]
        category = matched_category["category"]
        subcategory = matched_category["subcategory"]
        comment = matched_category["comment"]

    return {
        "id": operation_id,
        "date": now.strftime("%d.%m.%Y"),
        "month": now.month,
        "year": now.year,
        "type": "Расход",

        "group": group,
        "category": category,
        "subcategory": subcategory,

        "amount": parsed_expense["amount"],
        "amount_for_google": format_amount_for_google_sheets(parsed_expense["amount"]),
        "comment": comment,

        "recognition_start": "",
        "recognition_end": "",
        "allocation_months": "",

        "created_at": now.strftime("%d.%m.%Y %H:%M:%S"),
    }


def split_expense_lines(text: str) -> list[str]:
    if not text:
        return []

    lines = []

    for line in text.splitlines():
        clean_line = line.strip()

        if clean_line:
            lines.append(clean_line)

    return lines


def build_success_summary(operations: list[dict], failed_lines: list[str]) -> str:
    if len(operations) == 1 and not failed_lines:
        operation = operations[0]

        return (
            "Транзакция записана ✅\n\n"
            f"Дата: {operation['date']}\n"
            f"Сумма: {format_amount_for_user(operation['amount'])}\n"
            f"Группа: {operation['group']}\n"
            f"Статья: {operation['category']}\n"
            f"Подстатья: {operation['subcategory']}\n"
            f"Комментарий: {operation['comment']}"
        )

    text = ""

    if operations:
        text += f"Записано операций: {len(operations)} ✅\n"

    if failed_lines:
        if text:
            text += "\n"

        text += "Не удалось записать:\n"

        for line in failed_lines:
            text += f"- {line}\n"

        text += (
            "\nПроверьте незаписанные строки:\n"
            "— сумма должна быть в начале строки;\n"
            "— подстатья должна быть в списке «📋 Статьи»."
        )

    return text.strip()


@router.message()
async def expense_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    if message.text and message.text.startswith("/"):
        await message.answer(
           "Не понял команду.\n\n"
           "Чтобы открыть главное меню, напишите /menu",
           reply_markup=get_main_menu_keyboard(),
        )
        return    

    client = get_client_from_message(message)

    if not client:
        await answer_client_not_connected(message)
        return

    spreadsheet_id = client["spreadsheet_id"]
    expense_lines = split_expense_lines(message.text)

    if not expense_lines:
        await message.answer(
            "Не понял расход ❌\n\n"
            "Напишите сумму в начале строки, затем подстатью и комментарий.\n\n"
            "Примеры:\n"
            "100 Кофе\n"
            "1200 Связь май\n"
            "25000 Реклама май\n\n"
            "Если нужной подстатьи нет, добавьте ее через «➕ Добавить подстатьи».",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    successful_operations = []
    failed_lines = []

    for line in expense_lines:
        parsed_expense = parse_expense(line)

        if not parsed_expense:
            failed_lines.append(line)
            continue

        try:
            operation = build_operation(parsed_expense, spreadsheet_id)

            if not operation["subcategory"]:
                failed_lines.append(line)
                continue

            append_operation_to_sheet(operation, spreadsheet_id)
            successful_operations.append(operation)

        except Exception as error:
            print(f"Ошибка при обработке операции: {error}")
            failed_lines.append(line)

    if not successful_operations and failed_lines:
        await message.answer(
            "Не удалось записать расход ❌\n\n"
            "Проверьте:\n"
            "— сумма стоит первой;\n"
            "— подстатья есть в списке «📋 Статьи»;\n"
            "— если подстатьи нет, добавьте ее через «➕ Добавить подстатьи».\n\n"
            "Пример правильной записи:\n"
            "100 Кофе",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await message.answer(
       build_success_summary(successful_operations, failed_lines),
       reply_markup=get_main_menu_keyboard(),
    )