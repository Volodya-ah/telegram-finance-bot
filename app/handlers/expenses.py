from datetime import datetime

from aiogram import Router
from aiogram.types import Message

from app.services.access import deny_if_not_allowed
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


def build_operation(parsed_expense: dict) -> dict:
    now = datetime.now()
    operation_id = f"exp_{now.strftime('%Y%m%d_%H%M%S_%f')}"

    original_comment = parsed_expense["comment"]
    matched_category = find_category_by_comment(original_comment)

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
    """
    Разбиваем сообщение на отдельные строки расходов.

    Пример:
    1200 Связь май
    3000 Хостинг сайт

    Вернет:
    ["1200 Связь май", "3000 Хостинг сайт"]
    """

    if not text:
        return []

    lines = []

    for line in text.splitlines():
        clean_line = line.strip()

        if clean_line:
            lines.append(clean_line)

    return lines


def build_success_summary(operations: list[dict], failed_lines: list[str]) -> str:
    """
    Формируем короткий ответ пользователю после обработки расходов.
    """

    if len(operations) == 1 and not failed_lines:
        operation = operations[0]

        return (
            "Транзакция записана ✅\n\n"
            f"Дата: {operation['date']}\n"
            f"Сумма: {format_amount_for_user(operation['amount'])}\n"
            f"Группа: {operation['group']}\n"
            f"Категория: {operation['category']}\n"
            f"Подкатегория: {operation['subcategory']}\n"
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

        text += "\nПроверьте формат записи или доступные подкатегории командой /categories"

    return text.strip()


@router.message()
async def expense_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    expense_lines = split_expense_lines(message.text)

    if not expense_lines:
        await message.answer("Ошибка ❌. Проверьте запись или обратитесь в поддержку!")
        return

    successful_operations = []
    failed_lines = []

    for line in expense_lines:
        parsed_expense = parse_expense(line)

        if not parsed_expense:
            failed_lines.append(line)
            continue

        try:
            operation = build_operation(parsed_expense)

            if not operation["subcategory"]:
                failed_lines.append(line)
                continue

            append_operation_to_sheet(operation)
            successful_operations.append(operation)

        except Exception as error:
            print(f"Ошибка при обработке операции: {error}")
            failed_lines.append(line)

    if not successful_operations and failed_lines:
        await message.answer(
            "Ошибка ❌. Не удалось записать операции.\n\n"
            "Проверьте формат записи или доступные подкатегории командой /categories"
        )
        return

    await message.answer(
        build_success_summary(successful_operations, failed_lines)
    )