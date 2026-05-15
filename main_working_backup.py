import asyncio
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

import gspread
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_USER_IDS", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверь файл .env")

if not SPREADSHEET_ID:
    raise ValueError("SPREADSHEET_ID не найден. Проверь файл .env")


dp = Dispatcher()
def get_allowed_user_ids() -> set[int]:
    """
    Читаем список разрешенных Telegram ID из .env.

    Пример:
    ALLOWED_USER_IDS=123456789,987654321

    Если список пустой — бот доступен всем.
    """

    if not ALLOWED_USER_IDS_RAW.strip():
        return set()

    user_ids = set()

    for item in ALLOWED_USER_IDS_RAW.split(","):
        item = item.strip()

        if item.isdigit():
            user_ids.add(int(item))

    return user_ids


ALLOWED_USER_IDS = get_allowed_user_ids()


def is_user_allowed(user_id: int | None) -> bool:
    """
    Если ALLOWED_USER_IDS пустой — разрешаем всем.
    Если заполнен — разрешаем только пользователям из списка.
    """

    if not ALLOWED_USER_IDS:
        return True

    if user_id is None:
        return False

    return user_id in ALLOWED_USER_IDS


async def deny_if_not_allowed(message: Message) -> bool:
    """
    Возвращает True, если доступ запрещен.
    Возвращает False, если доступ разрешен.
    """

    user_id = message.from_user.id if message.from_user else None

    if is_user_allowed(user_id):
        return False

    await message.answer(
        "Доступ ограничен.\n"
        "Обратитесь к администратору."
    )

    return True


def parse_expense(text: str) -> dict | None:
    if not text:
        return None

    text = text.strip()

    match = re.match(r"^([\d\s]+(?:[,.]\d{1,2})?)\s*(.*)$", text)

    if not match:
        return None

    raw_amount = match.group(1)
    comment = match.group(2).strip()

    normalized_amount = raw_amount.replace(" ", "")
    normalized_amount = normalized_amount.replace(",", ".")

    try:
        amount = Decimal(normalized_amount)
    except InvalidOperation:
        return None

    if amount <= 0:
        return None

    return {
        "amount": amount,
        "comment": comment,
    }


def format_amount_for_user(amount: Decimal) -> str:
    if amount == amount.to_integral():
        return f"{int(amount):,}".replace(",", " ")

    integer_part, decimal_part = f"{amount:.2f}".split(".")
    integer_part = f"{int(integer_part):,}".replace(",", " ")

    return f"{integer_part},{decimal_part}"


def format_amount_for_google_sheets(amount: Decimal) -> str:
    if amount == amount.to_integral():
        return str(int(amount))

    return str(amount).replace(".", ",")


def get_google_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scopes,
    )

    return gspread.authorize(credentials)


def get_worksheet(sheet_name: str):
    client = get_google_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet(sheet_name)


def get_categories() -> list[dict]:
    worksheet = get_worksheet("Категории")
    rows = worksheet.get_all_records()

    categories = []

    for row in rows:
        group = str(row.get("Группа", "")).strip()
        category = str(row.get("Категория", "")).strip()
        subcategory = str(row.get("Подкатегория", "")).strip()

        if not group or not category or not subcategory:
            continue

        categories.append(
            {
                "group": group,
                "category": category,
                "subcategory": subcategory,
            }
        )

    return categories


def find_category_by_comment(comment: str) -> dict | None:
    """
    Ищем подкатегорию в комментарии.

    Примеры:
    "Реклама" -> Подкатегория: Реклама, Комментарий: ""
    "Реклама май" -> Подкатегория: Реклама, Комментарий: "май"
    """

    if not comment:
        return None

    categories = get_categories()

    for item in categories:
        subcategory = item["subcategory"]

        pattern = re.compile(re.escape(subcategory), re.IGNORECASE)
        match = pattern.search(comment)

        if match:
            cleaned_comment = pattern.sub("", comment, count=1).strip()
            cleaned_comment = re.sub(r"\s+", " ", cleaned_comment)

            return {
                "group": item["group"],
                "category": item["category"],
                "subcategory": item["subcategory"],
                "comment": cleaned_comment,
            }

    return None


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


def append_operation_to_sheet(operation: dict) -> None:
    worksheet = get_worksheet("Журнал операций")

    row = [
        operation["id"],
        operation["date"],
        operation["month"],
        operation["year"],
        operation["type"],
        operation["group"],
        operation["category"],
        operation["subcategory"],
        operation["amount_for_google"],
        operation["comment"],
        operation["recognition_start"],
        operation["recognition_end"],
        operation["allocation_months"],
        operation["created_at"],
    ]

    worksheet.append_row(row, value_input_option="USER_ENTERED")


@dp.message(Command("whoami"))
async def whoami_handler(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else None

    await message.answer(
        "Ваш Telegram ID:\n\n"
        f"{user_id}\n\n"
        f"Username: @{username}" if username else f"Ваш Telegram ID:\n\n{user_id}"
    )

@dp.message(CommandStart())
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

@dp.message(Command("categories"))
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

@dp.message(Command("help"))
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
        "/sheet — ссылка на Google-таблицу\n"
        "/help — помощь"
    )

@dp.message(Command("sheet"))
async def sheet_handler(message: Message) -> None:
    if await deny_if_not_allowed(message):
        return
    sheet_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"

    await message.answer(
        "Ваша Google-таблица:\n\n"
        f"{sheet_url}"
    )

@dp.message()
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


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())