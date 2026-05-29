from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.clients import get_client_by_telegram_id
from app.keyboards.start import OPEN_ORDERS_BUTTON, get_main_menu_keyboard
from app.services.nikita_reports import (
    format_open_orders_report,
    get_open_orders,
)


router = Router()


@router.message(Command("open_orders"))
@router.message(F.text == OPEN_ORDERS_BUTTON)
async def open_orders_command(message: Message) -> None:
    client = get_client_by_telegram_id(message.from_user.id)
    
    if not client:
        await message.answer(
            "У вас пока нет подключенной таблицы.\n\n"
            "Напишите /start, чтобы начать работу."
        )
        return

    custom_mode = client.get("custom_mode", "core")
    
    if custom_mode != "nikita":
        await message.answer(
            "Этот раздел пока недоступен для вашего режима работы.",
            reply_markup=get_main_menu_keyboard(custom_mode),
        )
        return

    spreadsheet_id = client["spreadsheet_id"]

    try:
        orders = get_open_orders(spreadsheet_id)
    except Exception:
        await message.answer(
            "Не удалось получить открытые заявки из таблицы.\n\n"
            "Проверьте, что в таблице есть лист «Анализ заявок» "
            "и нужные заголовки."
        )
        return

    report_text = format_open_orders_report(orders)
    await message.answer(
        report_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(custom_mode),
    )