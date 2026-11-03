"""Google Drive to Azure Blob Storage synchronization.

This is the main entry point for the synchronization application.
It orchestrates the transfer of files from a Google Drive folder to
Azure Blob Storage, with optional incremental sync support.

Usage:
    python main.py

Environment Variables:
    AZURE_STORAGE_CONNECTION_STRING: Connection string for Azure Storage.
    AZURE_CONTAINER: Name of the target container.
    FOLDER_ID: Google Drive folder ID to sync.
    KEY_VAULT_NAME: Azure Key Vault name for credentials.
    GOOGLE_APPLICATION_CREDENTIALS_SECRET_NAME: Secret name in Key Vault.
    INCREMENTAL_SYNC_ENABLED: Set to 'true' for incremental sync.
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import get_credentials
from get_drive_files import get_folder_files, is_folder
from incremental_sync import is_file_updated
from state import get_last_sync_time, save_state
from upload_blob import upload_blob
from upload_logging import logger

# Load environment variables from .env file
load_dotenv()


def validate_environment() -> tuple[str, str, str] | None:
    """Validate required environment variables are set.

    Returns:
        Tuple of (connection_string, container_name, folder_id) if valid,
        None if any required variables are missing.
    """
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER")
    folder_id = os.getenv("FOLDER_ID")

    if not connection_string:
        logger.error("AZURE_STORAGE_CONNECTION_STRING environment variable not set")
        return None

    if not container_name:
        logger.error("AZURE_CONTAINER environment variable not set")
        return None

    if not folder_id:
        logger.error("FOLDER_ID environment variable not set")
        return None

    return connection_string, container_name, folder_id


def sync_file(
    service,
    file: dict,
    connection_string: str,
    container_name: str,
) -> bool:
    """Download a file from Google Drive and upload to Azure Blob Storage.

    Args:
        service: Authenticated Google Drive API service.
        file: File metadata dictionary from Google Drive API.
        connection_string: Azure Storage connection string.
        container_name: Target container name.

    Returns:
        True if sync was successful, False otherwise.
    """
    file_name = file.get("name", "unknown")
    file_id = file.get("id")
    mime_type = file.get("mimeType", "application/octet-stream")

    if not file_id:
        logger.error("File missing ID: %s", file_name)
        return False

    try:
        # Download file content from Google Drive
        logger.debug("Downloading %s from Google Drive", file_name)
        request = service.files().get_media(fileId=file_id)
        file_data = request.execute()

        # Upload to Azure Blob Storage
        logger.debug("Uploading %s to Azure Blob Storage", file_name)
        success = upload_blob(
            connection_string,
            container_name,
            file_name,
            file_data,
            mime_type,
        )

        if success:
            logger.info("Successfully synced: %s", file_name)
        else:
            logger.error("Failed to upload: %s", file_name)

        return success

    except HttpError as error:
        logger.error("Google Drive error downloading %s: %s", file_name, error)
        return False
    except Exception as error:
        logger.error("Error syncing %s: %s", file_name, error)
        return False


def main() -> int:
    """Execute the Google Drive to Azure Blob Storage synchronization.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    logger.info("Starting Google Drive to Azure Blob Storage sync")

    # Validate environment
    env_config = validate_environment()
    if not env_config:
        return 1

    connection_string, container_name, folder_id = env_config

    # Initialize Google Drive service
    try:
        logger.info("Authenticating with Google Drive API")
        creds = get_credentials()
        service = build("drive", "v3", credentials=creds)
    except Exception as error:
        logger.error("Failed to initialize Google Drive service: %s", error)
        return 1

    # Verify folder exists
    if not is_folder(service, folder_id):
        logger.error("Folder with ID %s does not exist or is not accessible", folder_id)
        return 1

    # Get files from the folder
    logger.info("Retrieving files from Google Drive folder")
    folder_files = get_folder_files(service, folder_id)

    if not folder_files:
        logger.info("No files found in folder %s", folder_id)
        return 0

    logger.info("Found %d files to process", len(folder_files))

    # Check incremental sync settings
    incremental_enabled = os.getenv("INCREMENTAL_SYNC_ENABLED", "false").lower() == "true"
    last_sync_time = get_last_sync_time()

    if incremental_enabled:
        logger.info("Incremental sync enabled. Last sync: %s", last_sync_time)
    else:
        logger.info("Full sync mode (incremental sync disabled)")

    # Process files
    success_count = 0
    error_count = 0

    for file in folder_files:
        file_name = file.get("name", "unknown")
        file_id = file.get("id")

        # Skip unchanged files in incremental mode
        if (
            incremental_enabled
            and file_id
            and not is_file_updated(service, file_id, last_sync_time)
        ):
            logger.debug("Skipping unchanged file: %s", file_name)
            continue

        # Sync the file
        if sync_file(service, file, connection_string, container_name):
            success_count += 1
        else:
            error_count += 1

    # Update sync state
    if incremental_enabled and success_count > 0:
        save_state(datetime.utcnow())
        logger.info("Sync state updated")

    # Summary
    logger.info(
        "Sync complete: %d succeeded, %d failed, %d total",
        success_count,
        error_count,
        len(folder_files),
    )

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
