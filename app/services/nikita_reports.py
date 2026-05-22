from app.services.google_sheets import get_worksheet


OPEN_ORDER_STATUSES = {
    "Открыта",
    "Частично закрыта",
}


def _format_money(value) -> str:
    if value in (None, ""):
        return "0"

    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except ValueError:
        return str(value)

    if number.is_integer():
        return f"{int(number):,}".replace(",", " ")

    return f"{number:,.2f}".replace(",", " ")


def get_open_orders(spreadsheet_id: str) -> list[dict]:
    worksheet = get_worksheet(spreadsheet_id, "Анализ заявок")
    rows = worksheet.get_all_values()

    orders = []

    # Пропускаем строку заголовков
    for row in rows[1:]:
        # Защита от коротких/пустых строк
        row = row + [""] * 14

        order_id = str(row[0]).strip()
        status = str(row[12]).strip()

        if not order_id:
            continue

        if status not in OPEN_ORDER_STATUSES:
            continue

        orders.append(
            {
                "order_id": order_id,
                "pin": row[1],
                "date": row[2],
                "office": row[3],
                "client": row[4],
                "accepted_rub": row[5],
                "issued_rub": row[6],
                "remaining_rub": row[7],
                "used_as_source": row[8],
                "status": status,
            }
        )

    return orders


def format_open_orders_report(orders: list[dict], limit: int = 20) -> str:
    if not orders:
        return "📌 Открытых заявок нет."

    visible_orders = orders[:limit]

    text_parts = [
        "📌 Открытые заявки",
    ]

    for order in visible_orders:
        text_parts.append(
            f"{order['order_id']} · PIN {order['pin'] or '—'}\n"
            f"Клиент: {order['client'] or '—'}\n"
            f"Офис: {order['office'] or '—'}\n"
            f"Приняли: {_format_money(order['accepted_rub'])} RUB\n"
            f"Выдали: {_format_money(order['issued_rub'])} RUB\n"
            f"Остаток: {_format_money(order['remaining_rub'])} RUB\n"
            f"Использовано как источник: {_format_money(order['used_as_source'])} RUB\n"
            f"Статус: {order['status']}"
        )

    if len(orders) > limit:
        text_parts.append(
            f"Показано {limit} из {len(orders)} заявок. "
            "Остальные можно посмотреть в таблице."
        )

    return "\n\n".join(text_parts)