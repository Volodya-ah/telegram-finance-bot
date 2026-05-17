import argparse

from app.database.db import get_connection, init_db


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Удалить клиента из clients.db по Telegram ID"
    )

    parser.add_argument(
        "--telegram-id",
        type=int,
        required=True,
        help="Telegram ID клиента",
    )

    args = parser.parse_args()

    init_db()

    with get_connection() as connection:
        client = connection.execute(
            "SELECT * FROM clients WHERE telegram_id = ?",
            (args.telegram_id,),
        ).fetchone()

        if not client:
            print("Клиент не найден ⚠️")
            print(f"Telegram ID: {args.telegram_id}")
            return

        print("Найден клиент:")
        print(f"ID в базе: {client['id']}")
        print(f"Telegram ID: {client['telegram_id']}")
        print(f"Username: {client['username']}")
        print(f"First name: {client['first_name']}")
        print(f"Spreadsheet URL: {client['spreadsheet_url']}")

        connection.execute(
            "DELETE FROM clients WHERE telegram_id = ?",
            (args.telegram_id,),
        )

        connection.commit()

    print("\nКлиент удален из clients.db ✅")


if __name__ == "__main__":
    main()