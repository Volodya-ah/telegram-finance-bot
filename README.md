# Telegram Finance Bot

MVP Telegram-бота для учета расходов бизнеса.

## Что умеет

- принимает расходы в Telegram

- парсит сумму и комментарий

- ищет подкатегорию в Google Sheets

- записывает операцию в Журнал операций

- поддерживает команды /help, /categories, /sheet, /whoami

- ограничивает доступ через whitelist Telegram ID

## Стек

- Python

- aiogram

- Google Sheets API

- gspread

- python-dotenv