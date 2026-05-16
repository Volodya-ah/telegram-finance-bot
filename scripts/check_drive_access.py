from googleapiclient.discovery import build

from app.config import CLIENTS_FOLDER_ID, TEMPLATE_SPREADSHEET_ID
from app.services.google_drive import get_oauth_credentials


def main() -> None:
    credentials = get_oauth_credentials()
    service = build("drive", "v3", credentials=credentials)

    print("Проверяю доступ OAuth к Google Drive...\n")

    print("TEMPLATE_SPREADSHEET_ID:")
    print(TEMPLATE_SPREADSHEET_ID)

    try:
        template = (
            service.files()
            .get(
                fileId=TEMPLATE_SPREADSHEET_ID,
                fields="id,name,mimeType,webViewLink,owners",
            )
            .execute()
        )

        print("Шаблон найден ✅")
        print(f"Name: {template.get('name')}")
        print(f"ID: {template.get('id')}")
        print(f"MimeType: {template.get('mimeType')}")
        print(f"Link: {template.get('webViewLink')}")
    except Exception as error:
        print("Шаблон НЕ найден ❌")
        print(error)

    print("\nCLIENTS_FOLDER_ID:")
    print(CLIENTS_FOLDER_ID)

    try:
        folder = (
            service.files()
            .get(
                fileId=CLIENTS_FOLDER_ID,
                fields="id,name,mimeType,webViewLink",
            )
            .execute()
        )

        print("Папка найдена ✅")
        print(f"Name: {folder.get('name')}")
        print(f"ID: {folder.get('id')}")
        print(f"MimeType: {folder.get('mimeType')}")
        print(f"Link: {folder.get('webViewLink')}")
    except Exception as error:
        print("Папка НЕ найдена ❌")
        print(error)


if __name__ == "__main__":
    main()