import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # legacy, optional
ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_USER_IDS", "")
TEMPLATE_SPREADSHEET_ID = os.getenv("TEMPLATE_SPREADSHEET_ID")
ADMIN_GOOGLE_EMAIL = os.getenv("ADMIN_GOOGLE_EMAIL")
CLIENTS_FOLDER_ID = os.getenv("CLIENTS_FOLDER_ID")


if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверь файл .env")

if not TEMPLATE_SPREADSHEET_ID:
    raise ValueError("TEMPLATE_SPREADSHEET_ID не найден. Проверь файл .env")

if not ADMIN_GOOGLE_EMAIL:
    raise ValueError("ADMIN_GOOGLE_EMAIL не найден. Проверь файл .env")

if not CLIENTS_FOLDER_ID:
    raise ValueError("CLIENTS_FOLDER_ID не найден. Проверь файл .env")