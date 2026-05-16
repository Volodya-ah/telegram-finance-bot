import re

import gspread
from google.oauth2.service_account import Credentials


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


def get_worksheet(spreadsheet_id: str, sheet_name: str):
    client = get_google_client()
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet.worksheet(sheet_name)


def get_categories(spreadsheet_id: str) -> list[dict]:
    worksheet = get_worksheet(spreadsheet_id, "Категории")
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


def find_category_by_comment(comment: str, spreadsheet_id: str) -> dict | None:
    if not comment:
        return None

    categories = get_categories(spreadsheet_id)

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


def append_operation_to_sheet(operation: dict, spreadsheet_id: str) -> None:
    worksheet = get_worksheet(spreadsheet_id, "Журнал операций")

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


def get_unique_categories(spreadsheet_id: str) -> list[dict]:
    categories = get_categories(spreadsheet_id)
    unique_items = {}

    for item in categories:
        key = item["category"].lower()

        if key not in unique_items:
            unique_items[key] = {
                "group": item["group"],
                "category": item["category"],
            }

    return list(unique_items.values())


def find_category_by_name(category_name: str, spreadsheet_id: str) -> dict | None:
    if not category_name:
        return None

    category_name_lower = category_name.strip().lower()
    unique_categories = get_unique_categories(spreadsheet_id)

    for item in unique_categories:
        if item["category"].lower() == category_name_lower:
            return item

    return None


def get_subcategories_for_category(
    category_name: str,
    spreadsheet_id: str,
) -> list[str]:
    categories = get_categories(spreadsheet_id)
    result = []

    for item in categories:
        if item["category"].lower() == category_name.lower():
            result.append(item["subcategory"])

    return result


def append_category_row(
    spreadsheet_id: str,
    group: str,
    category: str,
    subcategory: str,
) -> None:
    worksheet = get_worksheet(spreadsheet_id, "Категории")

    row = [
        group,
        category,
        subcategory,
    ]

    worksheet.append_row(row, value_input_option="USER_ENTERED")