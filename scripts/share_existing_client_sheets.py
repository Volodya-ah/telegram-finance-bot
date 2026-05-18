from app.database.db import get_connection, init_db
from app.services.google_drive import get_oauth_drive_service


def main() -> None:
    init_db()

    service = get_oauth_drive_service()

    with get_connection() as connection:
        clients = connection.execute(
            """
            SELECT telegram_id, username, first_name, spreadsheet_id, spreadsheet_url
            FROM clients
            WHERE spreadsheet_id IS NOT NULL
            """
        ).fetchall()

    if not clients:
        print("Клиенты не найдены.")
        return

    print(f"Найдено таблиц: {len(clients)}")

    for client in clients:
        telegram_id = client["telegram_id"]
        username = client["username"]
        first_name = client["first_name"]
        spreadsheet_id = client["spreadsheet_id"]

        try:
            service.permissions().create(
                fileId=spreadsheet_id,
                body={
                    "type": "anyone",
                    "role": "reader",
                },
            ).execute()

            print(
                "Доступ открыт ✅ "
                f"telegram_id={telegram_id} "
                f"username={username} "
                f"first_name={first_name} "
                f"spreadsheet_id={spreadsheet_id}"
            )

        except Exception as error:
            print(
                "Ошибка ❌ "
                f"telegram_id={telegram_id} "
                f"spreadsheet_id={spreadsheet_id} "
                f"{error}"
            )


if __name__ == "__main__":
    main()