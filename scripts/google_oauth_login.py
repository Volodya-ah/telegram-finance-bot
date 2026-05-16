from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

OAUTH_CREDENTIALS_PATH = Path("oauth_credentials.json")
TOKEN_PATH = Path("token.json")


def main() -> None:
    credentials = None

    if TOKEN_PATH.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_PATH),
            SCOPES,
        )

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        if not OAUTH_CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                "Не найден oauth_credentials.json. "
                "Скачай OAuth Client JSON из Google Cloud и положи в корень проекта."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(OAUTH_CREDENTIALS_PATH),
            SCOPES,
        )

        credentials = flow.run_local_server(port=0)

    TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")

    print("OAuth авторизация завершена ✅")
    print("Файл token.json создан/обновлен.")


if __name__ == "__main__":
    main()