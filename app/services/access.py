from aiogram.types import Message

from app.config import ALLOWED_USER_IDS_RAW


def get_allowed_user_ids() -> set[int]:
    """
    Читаем список разрешенных Telegram ID из .env.

    Пример:
    ALLOWED_USER_IDS=123456789,987654321

    Если список пустой — бот доступен всем.
    """

    if not ALLOWED_USER_IDS_RAW.strip():
        return set()

    user_ids = set()

    for item in ALLOWED_USER_IDS_RAW.split(","):
        item = item.strip()

        if item.isdigit():
            user_ids.add(int(item))

    return user_ids


ALLOWED_USER_IDS = get_allowed_user_ids()


def is_user_allowed(user_id: int | None) -> bool:
    """
    Если ALLOWED_USER_IDS пустой — разрешаем всем.
    Если заполнен — разрешаем только пользователям из списка.
    """

    if not ALLOWED_USER_IDS:
        return True

    if user_id is None:
        return False

    return user_id in ALLOWED_USER_IDS


async def deny_if_not_allowed(message: Message) -> bool:
    """
    Возвращает True, если доступ запрещен.
    Возвращает False, если доступ разрешен.
    """

    user_id = message.from_user.id if message.from_user else None

    if is_user_allowed(user_id):
        return False

    await message.answer(
        "Доступ ограничен.\n"
        "Обратитесь к администратору."
    )

    return True