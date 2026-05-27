from html import escape

from app.services.google_sheets import get_worksheet


OPEN_ORDER_STATUSES = {
    "Открыта",
    "Частично закрыта",
}


def _to_number(value) -> float:
    if value in (None, ""):
        return 0.0

    cleaned = str(value)
    cleaned = cleaned.replace("RUB", "")
    cleaned = cleaned.replace("₽", "")
    cleaned = cleaned.replace("\u00a0", "")
    cleaned = cleaned.replace("\u202f", "")
    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace(",", ".")
    cleaned = cleaned.strip()

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _format_money(value) -> str:
    number = _to_number(value)

    if number == 0:
        return "0"

    if number.is_integer():
        return f"{int(number):,}".replace(",", " ")

    return f"{number:,.2f}".replace(",", " ")

def _safe_text(value) -> str:
    if value in (None, ""):
        return "—"

    return escape(str(value).strip())

def get_open_orders(spreadsheet_id: str) -> list[dict]:
    worksheet = get_worksheet(spreadsheet_id, "Анализ заявок")
    rows = worksheet.get_all_values()

    orders = []

    # Пропускаем строку заголовков
    for row in rows[1:]:
        # Нужно минимум до колонки O включительно:
        # A=0 ... O=14
        row = row + [""] * 15

        order_id = str(row[0]).strip()
        status = str(row[12]).strip()

        if not order_id:
            continue

        if status not in OPEN_ORDER_STATUSES:
            continue

        remaining_rub = row[7]
        risk_gap = str(row[14]).strip()

        orders.append(
            {
                "order_id": order_id,
                "pin": row[1],
                "date": row[2],
                "office": row[3],
                "client": row[4],
                "accepted_rub": row[5],
                "issued_rub": row[6],
                "remaining_rub": remaining_rub,
                "risk_gap": risk_gap,
                "status": status,
                "remaining_value": _to_number(remaining_rub),
            }
        )

    orders.sort(key=lambda order: order["remaining_value"], reverse=True)

    return orders


def format_open_orders_report(orders: list[dict], limit: int = 20) -> str:
    if not orders:
        return "📌 Заявок в работе нет."

    visible_orders = orders[:limit]

    open_count = sum(1 for order in orders if order["status"] == "Открыта")
    partial_count = sum(1 for order in orders if order["status"] == "Частично закрыта")
    total_remaining = sum(order["remaining_value"] for order in orders)

    text_parts = [
        (
            "📌 Заявки в работе\n\n"
            f"Всего: {len(orders)}\n"
            f"Открытые: {open_count}\n"
            f"Частично закрытые: {partial_count}\n"
            f"Общий остаток к выдаче: {_format_money(total_remaining)} RUB"
        )
    ]

    for index, order in enumerate(visible_orders, start=1):
        order_lines = [
            (
                f"<u><b>{index}. "
                f"{_safe_text(order['order_id'])} · "
                f"PIN {_safe_text(order['pin'])} · "
                f"{_safe_text(order['date'])}"
                f"</b></u>"
            ),
            f"Клиент: {_safe_text(order['client'])}",
            f"Офис: {_safe_text(order['office'])}",
            f"- Приняли: {_format_money(order['accepted_rub'])} RUB",
            f"- Выдали: {_format_money(order['issued_rub'])} RUB",
            f"- Остаток к выдаче: {_format_money(order['remaining_rub'])} RUB",
        ]

        if order["risk_gap"]:
            order_lines.append(_safe_text(order["risk_gap"]))

        order_lines.append(f"Статус: {_safe_text(order['status'])}")

        text_parts.append("\n".join(order_lines))

    if len(orders) > limit:
        text_parts.append(
            f"Показано {limit} из {len(orders)} заявок.\n"
            "Полный список можно посмотреть в таблице."
        )

    return "\n\n".join(text_parts)