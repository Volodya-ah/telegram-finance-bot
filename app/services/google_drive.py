from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import (
    ADMIN_GOOGLE_EMAIL,
    CLIENTS_FOLDER_ID,
    TEMPLATE_SPREADSHEET_ID,
)


SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

OAUTH_CREDENTIALS_PATH = Path("oauth_credentials.json")
TOKEN_PATH = Path("token.json")
SERVICE_ACCOUNT_PATH = Path("credentials.json")


def get_oauth_credentials() -> OAuthCredentials:
    """
    OAuth-доступ от Google-аккаунта Владимира.
    Нужен, чтобы создавать копии таблиц именно в Google Drive Владимира.
    """

    credentials = None

    if TOKEN_PATH.exists():
        credentials = OAuthCredentials.from_authorized_user_file(
            str(TOKEN_PATH),
            SCOPES,
        )

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")

    if credentials and credentials.valid:
        return credentials

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

    return credentials


def get_oauth_drive_service():
    credentials = get_oauth_credentials()
    return build("drive", "v3", credentials=credentials)


def get_service_account_email() -> str:
    credentials = ServiceAccountCredentials.from_service_account_file(
        str(SERVICE_ACCOUNT_PATH),
        scopes=SCOPES,
    )

    return credentials.service_account_email


def copy_template_spreadsheet(title: str) -> dict:
    """
    Копирует Google Sheets-шаблон в Google Drive Владимира
    и дает service account доступ редактора к новой таблице.
    """

    service = get_oauth_drive_service()

    copied_file = (
        service.files()
        .copy(
            fileId=TEMPLATE_SPREADSHEET_ID,
            body={
                "name": title,
                "parents": [CLIENTS_FOLDER_ID],
            },
            fields="id,name,webViewLink",
        )
        .execute()
    )

    spreadsheet_id = copied_file["id"]
    service_account_email = get_service_account_email()

    service.permissions().create(
        fileId=spreadsheet_id,
        body={
            "type": "user",
            "role": "writer",
            "emailAddress": service_account_email,
        },
        sendNotificationEmail=False,
    ).execute()

    if ADMIN_GOOGLE_EMAIL:
        service.permissions().create(
            fileId=spreadsheet_id,
            body={
                "type": "user",
                "role": "writer",
                "emailAddress": ADMIN_GOOGLE_EMAIL,
            },
            sendNotificationEmail=False,
        ).execute()

    return {
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
        "name": copied_file["name"],
    }