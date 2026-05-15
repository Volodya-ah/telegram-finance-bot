import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_USER_IDS", "")


if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверь файл .env")

if not SPREADSHEET_ID:
    raise ValueError("SPREADSHEET_ID не найден. Проверь файл .env")