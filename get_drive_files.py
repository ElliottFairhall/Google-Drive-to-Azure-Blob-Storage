from typing import List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def is_folder(drive_service: build, folder_id: str) -> bool:
    """
    This function checks if a folder exists in Google Drive.
    """
    try:
        # Check if folder exists
        query = f"mimeType='application/vnd.google-apps.folder' and trashed = false and id = '{folder_id}'"
        results = drive_service.files().list(q=query, fields="nextPageToken, files(id)").execute()
        items = results.get("files", [])
        if items:
            return True
        else:
            return False
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False


def get_all_files(drive_service: build) -> List[dict]:
    """
    This function retrieves all files in a user's Google Drive.
    """
    try:
        # Retrieve all files
        query = "mimeType!='application/vnd.google-apps.folder'"
        results = (
            drive_service.files()
            .list(q=query, fields="nextPageToken, files(id, name, createdTime, modifiedTime, mimeType)")
            .execute()
        )
        files = results.get("files", [])

        return files

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def get_folder_files(drive_service: build, folder_id: str) -> List[dict]:
    """
    This function retrieves all the files in a folder in Google Drive.
    """
    try:
        # Retrieve all files in folder
        query = f"mimeType!='application/vnd.google-apps.folder' and parents in '{folder_id}'"
        results = (
            drive_service.files()
            .list(q=query, fields="nextPageToken, files(id, name, createdTime, modifiedTime, mimeType)")
            .execute()
        )
        files = results.get("files", [])

        return files

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
