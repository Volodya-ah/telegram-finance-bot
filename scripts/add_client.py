import argparse

from app.database.clients import create_or_update_client


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Добавить или обновить клиента в clients.db"
    )

    parser.add_argument(
        "--telegram-id",
        type=int,
        required=True,
        help="Telegram ID клиента",
    )

    parser.add_argument(
        "--spreadsheet-id",
        type=str,
        required=True,
        help="Google Spreadsheet ID клиента",
    )

    parser.add_argument(
        "--username",
        type=str,
        default=None,
        help="Telegram username клиента без @",
    )

    parser.add_argument(
        "--first-name",
        type=str,
        default=None,
        help="Имя клиента из Telegram",
    )

    args = parser.parse_args()

    client = create_or_update_client(
        telegram_id=args.telegram_id,
        username=args.username,
        first_name=args.first_name,
        spreadsheet_id=args.spreadsheet_id,
    )

    print("Клиент добавлен/обновлен ✅")
    print(f"ID в базе: {client['id']}")
    print(f"Telegram ID: {client['telegram_id']}")
    print(f"Username: {client['username']}")
    print(f"First name: {client['first_name']}")
    print(f"Spreadsheet ID: {client['spreadsheet_id']}")
    print(f"Spreadsheet URL: {client['spreadsheet_url']}")
    print(f"Status: {client['status']}")
    print(f"Plan: {client['plan']}")


if __name__ == "__main__":
    main()