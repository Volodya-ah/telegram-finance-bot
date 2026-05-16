from aiogram.types import Message

from app.database.clients import get_client_by_telegram_id


CLIENT_NOT_CONNECTED_TEXT = (
    "Я пока не нашел вашу таблицу для учета.\n\n"
    "Чтобы я мог записывать расходы именно в вашу таблицу, "
    "отправьте Владимиру ваш Telegram ID.\n\n"
    "Узнать Telegram ID можно командой:\n"
    "/whoami\n\n"
    "Владимир: @vova_ah\n\n"
    "Когда всё будет готово к работе, Владимир сообщит вам об этом."
)


def get_telegram_id_from_message(message: Message) -> int | None:
    if not message.from_user:
        return None

    return message.from_user.id


def get_client_from_message(message: Message) -> dict | None:
    telegram_id = get_telegram_id_from_message(message)

    if telegram_id is None:
        return None

    return get_client_by_telegram_id(telegram_id)


async def answer_client_not_connected(message: Message) -> None:
    await message.answer(CLIENT_NOT_CONNECTED_TEXT)