import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bot.logging.logger import bot_logger

from dotenv import load_dotenv

load_dotenv('env')


def get_drive_config():
    """
    Возвращает параметры для подключения к Google Drive API.
    
    :return: Кортеж из пути к файлу учетных данных и списка областей доступа.
    """
    SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT')
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    return SERVICE_ACCOUNT_FILE, SCOPES

def create_drive_service(service_account_file, scopes):
    """
    Создает объект сервиса Google Drive с использованием учетных данных из файла.

    :param service_account_file: Путь к файлу учетных данных сервиса.
    :param scopes: Список областей доступа.
    :return: Объект сервиса Google Drive.
    """
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=scopes
    )
    service = build('drive', 'v3', credentials=credentials)
    return service

async def find_folder_id(service, folder_name, suffix=None):
    """
    Находит ID папки по имени с возможным фильтром по окончанию.

    :param service: Объект сервиса Google Drive.
    :param folder_name: Имя папки для поиска.
    :param suffix: Окончание имени папки для фильтрации (например, 'FWS' или 'FWD').
    :return: ID папки или None, если папка не найдена.
    """
    try:
        # Формируем основное условие для запроса
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        
        # Добавляем условие для окончания, если оно задано
        if suffix:
            query += f" and name contains '{suffix}'"

        folder_results = service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()
        
        folders = folder_results.get('files', [])
        return folders[0]['id'] if folders else None

    except HttpError as e:
        bot_logger.log('error', f'Ошибка при поиске папки: {e}')
        return None
    
async def list_files_in_folder(service, folder_id):
    """
    Получает список файлов в указанной папке.

    :param service: Объект сервиса Google Drive.
    :param folder_id: ID папки для поиска файлов.
    :return: Список файлов или пустой список, если файлов не найдено.
    """
    try:
        query = f"'{folder_id}' in parents"
        results = service.files().list(
            pageSize=10,
            fields="nextPageToken, files(id, name, mimeType)",
            q=query
        ).execute()
        
        return results.get('files', [])
    
    except HttpError as e:
        bot_logger.log('error', f'Ошибка при получении файлов в папке: {e}')
        return []

def format_files_response(files):
    """
    Форматирует ответ с информацией о файлах.

    :param files: Список файлов.
    :return: Строка с отформатированным ответом или сообщение об отсутствии файлов.
    """
    if files:
        response_text = "📂 Файлы в папке:\n"
        for file in files:
            file_id = file['id']
            file_name = file['name']
            download_link = f"https://drive.google.com/uc?id={file_id}"
            response_text += (
                f"📄 <b>{file_name}</b>: [Скачать]({download_link})\n"
            )
        return response_text
    else:
        return "🚫 Файлы не найдены. 😞"
async def get_files_from_folder(service, folder_name, suffix):
    """
    Получает список файлов из указанной папки на Google Drive.
    
    :param service: Объект сервиса Google Drive.
    :param folder_name: Имя папки для поиска файлов.
    :return: Список файлов или сообщение об ошибке.
    """
    try:
        folder_id = await find_folder_id(service, folder_name, suffix)

        if not folder_id:
            return "Папка не найдена. 🥺", None

        files = await list_files_in_folder(service, folder_id)
        response_text = format_files_response(files)
        
        return response_text, None

    except Exception as e:
        bot_logger.log('error', f'Ошибка при получении файлов из папки: {e}')
        return "Произошла ошибка при получении файлов. Пожалуйста, попробуйте позже.", None
