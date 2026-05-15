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


@router.message()
async def expense_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return

    parsed_expense = parse_expense(message.text)

    if not parsed_expense:
        await message.answer("Ошибка ❌. Проверьте запись или обратитесь в поддержку!")
        return

    try:
        operation = build_operation(parsed_expense)

        if not operation["subcategory"]:
            await message.answer(
                "Ошибка ❌. Не нашел подкатегорию в сообщении.\n\n"
                "Проверьте доступные подкатегории командой /categories"
            )
            return

        append_operation_to_sheet(operation)

        await message.answer(
            "Транзакция записана ✅\n\n"
            f"Дата: {operation['date']}\n"
            f"Сумма: {format_amount_for_user(operation['amount'])}\n"
            f"Группа: {operation['group']}\n"
            f"Категория: {operation['category']}\n"
            f"Подкатегория: {operation['subcategory']}\n"
            f"Комментарий: {operation['comment']}"
        )

    except Exception as error:
        print(f"Ошибка при обработке операции: {error}")
        await message.answer("Ошибка ❌. Проверьте запись или обратитесь в поддержку!")