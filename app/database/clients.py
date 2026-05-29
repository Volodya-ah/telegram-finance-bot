from datetime import datetime

from app.database.db import get_connection, init_db


def build_spreadsheet_url(spreadsheet_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def create_or_update_client(
    telegram_id: int,
    spreadsheet_id: str,
    username: str | None = None,
    first_name: str | None = None,
    status: str = "active",
    plan: str = "test",
    custom_mode: str = "core",
) -> dict:
    """
    Создает клиента или обновляет его, если telegram_id уже существует.
    """

    init_db()

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    spreadsheet_url = build_spreadsheet_url(spreadsheet_id)

    with get_connection() as connection:
        existing_client = connection.execute(
            "SELECT * FROM clients WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()

        if existing_client:
            connection.execute(
                """
                UPDATE clients
                SET
                    username = ?,
                    first_name = ?,
                    spreadsheet_id = ?,
                    spreadsheet_url = ?,
                    status = ?,
                    plan = ?,
                    custom_mode = ?,
                    updated_at = ?
                WHERE telegram_id = ?
                """,
                (
                    username,
                    first_name,
                    spreadsheet_id,
                    spreadsheet_url,
                    status,
                    plan,
                    now,
                    telegram_id,
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO clients (
                    telegram_id,
                    username,
                    first_name,
                    spreadsheet_id,
                    spreadsheet_url,
                    status,
                    plan,
                    custom_mode,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    telegram_id,
                    username,
                    first_name,
                    spreadsheet_id,
                    spreadsheet_url,
                    status,
                    plan,
                    custom_mode,
                    now,
                    now,
                ),
            )

        connection.commit()

        client = connection.execute(
            "SELECT * FROM clients WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()

    return dict(client)


def get_client_by_telegram_id(telegram_id: int) -> dict | None:
    """
    Возвращает клиента по Telegram ID.
    """

    init_db()

    with get_connection() as connection:
        client = connection.execute(
            "SELECT * FROM clients WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()

    if not client:
        return None

    return dict(client)