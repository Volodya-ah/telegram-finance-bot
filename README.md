# Telegram Finance Bot

MVP Telegram-бота для учета расходов бизнеса через Telegram и Google Sheets.

## Что умеет

- принимает расходы в Telegram;
- парсит сумму и комментарий;
- определяет подстатью расхода;
- записывает операции в Google Sheets;
- создает отдельную Google-таблицу для каждого клиента;
- связывает клиента по `telegram_id`;
- поддерживает команды `/start`, `/menu`, `/categories`, `/add_subcategories`, `/sheet`, `/whoami`, `/cancel`, `/help`.

## Текущая архитектура

- `main.py` — точка входа;
- `app/handlers/` — Telegram handlers;
- `app/services/` — бизнес-логика и интеграции;
- `app/database/` — работа с клиентской базой;
- `scripts/` — вспомогательные скрипты;
- Google Drive OAuth используется для создания копий таблицы-шаблона;
- Google Sheets service account используется для записи данных в таблицы.

## Среды

### TEST / локальный ПК

Используется для разработки и проверки.

Ожидаемые значения:

```text
тестовый BOT_TOKEN
clients_test.db
Finance Bot Test Clients
