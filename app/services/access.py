from aiogram.types import Message


async def deny_if_not_allowed(message: Message) -> bool:
    """
    Раньше здесь был whitelist через ALLOWED_USER_IDS.

    Сейчас бот открыт для знакомства:
    - /start
    - /whoami
    - /help
    - /menu
    - onboarding

    Рабочие действия защищаются через clients.db:
    если клиента нет в базе, бот не даст писать расходы
    и покажет понятное сообщение о подключении таблицы.
    """

    return False