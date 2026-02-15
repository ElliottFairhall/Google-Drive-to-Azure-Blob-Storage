"""Google Drive file retrieval operations.

This module provides functions for listing and checking files and folders
in Google Drive using the Google Drive API v3.
"""

from typing import Any

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from upload_logging import logger


def is_folder(drive_service: Resource, folder_id: str) -> bool:
    """Check if a folder exists in Google Drive.

    Queries the Google Drive API to verify that a folder with the given ID
    exists and is not in the trash.

    Args:
        drive_service: Authenticated Google Drive API service resource.
        folder_id: The unique identifier of the folder to check.

    Returns:
        True if the folder exists and is accessible, False otherwise.

    Example:
        >>> service = build('drive', 'v3', credentials=creds)
        >>> if is_folder(service, "1abc123def456"):
        ...     print("Folder exists")
    """
    try:
        # Check if folder exists by querying for it directly
        file_metadata = (
            drive_service.files().get(fileId=folder_id, fields="id, mimeType, trashed").execute()
        )

        is_folder_type = file_metadata.get("mimeType") == "application/vnd.google-apps.folder"
        is_not_trashed = not file_metadata.get("trashed", False)

        return is_folder_type and is_not_trashed

    except HttpError as error:
        logger.error("Google Drive API error checking folder %s: %s", folder_id, error)
        return False
    except Exception as error:
        logger.error("Unexpected error checking folder %s: %s", folder_id, error)
        return False


def get_all_files(drive_service: Resource) -> list[dict[str, Any]]:
    """Retrieve all files in a user's Google Drive.

    Lists all non-folder files accessible by the authenticated user,
    handling pagination to retrieve complete results.

    Args:
        drive_service: Authenticated Google Drive API service resource.

    Returns:
        List of file metadata dictionaries containing:
            - id: File unique identifier
            - name: File name
            - createdTime: ISO timestamp of creation
            - modifiedTime: ISO timestamp of last modification
            - mimeType: MIME type of the file

    Example:
        >>> files = get_all_files(service)
        >>> for f in files:
        ...     print(f"{f['name']} - {f['mimeType']}")
    """
    try:
        all_files: list[dict[str, Any]] = []
        page_token = None

        while True:
            # Retrieve files (excluding folders)
            query = "mimeType != 'application/vnd.google-apps.folder' and trashed = false"
            results = (
                drive_service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name, createdTime, modifiedTime, mimeType)",
                    pageToken=page_token,
                    pageSize=100,
                )
                .execute()
            )

            files = results.get("files", [])
            all_files.extend(files)

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        logger.info("Retrieved %d files from Google Drive", len(all_files))
        return all_files

    except HttpError as error:
        logger.error("Google Drive API error retrieving all files: %s", error)
        return []
    except Exception as error:
        logger.error("Unexpected error retrieving all files: %s", error)
        return []


def get_folder_files(drive_service: Resource, folder_id: str) -> list[dict[str, Any]]:
    """Retrieve all files in a specific Google Drive folder.

    Lists all non-folder files within the specified folder,
    handling pagination to retrieve complete results.

    Args:
        drive_service: Authenticated Google Drive API service resource.
        folder_id: The unique identifier of the folder to list files from.

    Returns:
        List of file metadata dictionaries containing:
            - id: File unique identifier
            - name: File name
            - createdTime: ISO timestamp of creation
            - modifiedTime: ISO timestamp of last modification
            - mimeType: MIME type of the file

    Example:
        >>> files = get_folder_files(service, "1abc123def456")
        >>> print(f"Found {len(files)} files in folder")
    """
    try:
        all_files: list[dict[str, Any]] = []
        page_token = None

        while True:
            # Retrieve all files in folder (excluding subfolders)
            query = (
                f"mimeType != 'application/vnd.google-apps.folder' "
                f"and '{folder_id}' in parents "
                f"and trashed = false"
            )
            results = (
                drive_service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name, createdTime, modifiedTime, mimeType)",
                    pageToken=page_token,
                    pageSize=100,
                )
                .execute()
            )

            files = results.get("files", [])
            all_files.extend(files)

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        logger.info("Retrieved %d files from folder %s", len(all_files), folder_id)
        return all_files

    except HttpError as error:
        logger.error(
            "Google Drive API error retrieving files from folder %s: %s",
            folder_id,
            error,
        )
        return []
    except Exception as error:
        logger.error(
            "Unexpected error retrieving files from folder %s: %s",
            folder_id,
            error,
        )
        return []
