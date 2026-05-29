import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


DATABASE_PATH = Path(os.getenv("CLIENTS_DB_PATH", "clients.db"))


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                first_name TEXT,
                spreadsheet_id TEXT NOT NULL,
                spreadsheet_url TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                plan TEXT NOT NULL DEFAULT 'test',
                custom_mode TEXT NOT NULL DEFAULT 'core',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = connection.execute("PRAGMA table_info(clients)").fetchall()
        column_names = [column["name"] for column in columns]

        if "custom_mode" not in column_names:
            connection.execute(
                "ALTER TABLE clients ADD COLUMN custom_mode TEXT NOT NULL DEFAULT 'core'"
            )

        connection.commit()