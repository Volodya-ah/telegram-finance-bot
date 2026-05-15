import re
from decimal import Decimal, InvalidOperation


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