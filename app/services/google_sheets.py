import re

import gspread
from google.oauth2.service_account import Credentials

from app.config import SPREADSHEET_ID


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
def get_unique_categories() -> list[dict]:
    """
    Возвращает уникальные пары:
    Группа + Категория

    Нужно для выбора категории при добавлении подкатегорий.
    """

    categories = get_categories()
    unique_items = {}

    for item in categories:
        key = item["category"].lower()

        if key not in unique_items:
            unique_items[key] = {
                "group": item["group"],
                "category": item["category"],
            }

    return list(unique_items.values())


def find_category_by_name(category_name: str) -> dict | None:
    """
    Ищем категорию по названию без учета регистра.
    """

    if not category_name:
        return None

    category_name_lower = category_name.strip().lower()
    unique_categories = get_unique_categories()

    for item in unique_categories:
        if item["category"].lower() == category_name_lower:
            return item

    return None


def get_subcategories_for_category(category_name: str) -> list[str]:
    """
    Возвращает список подкатегорий для категории.
    """

    categories = get_categories()
    result = []

    for item in categories:
        if item["category"].lower() == category_name.lower():
            result.append(item["subcategory"])

    return result


def append_category_row(group: str, category: str, subcategory: str) -> None:
    """
    Добавляет строку в лист 'Категории'.
    """

    worksheet = get_worksheet("Категории")

    row = [
        group,
        category,
        subcategory,
    ]

    worksheet.append_row(row, value_input_option="USER_ENTERED")