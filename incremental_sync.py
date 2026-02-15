"""Incremental synchronization utilities.

This module provides functions for determining which files need to be
synchronized based on modification times, enabling efficient incremental
backups.
"""

import logging
from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def is_file_updated(
    service: Resource,
    file_id: str,
    last_sync_time: datetime,
) -> bool:
    """Check if a file has been modified since the last sync.

    Compares the file's modification time from Google Drive with the
    provided last sync timestamp to determine if the file needs updating.

    Args:
        service: Authenticated Google Drive API service resource.
        file_id: The unique identifier of the file to check.
        last_sync_time: The datetime of the last successful sync.

    Returns:
        True if the file has been modified since last_sync_time,
        False otherwise (including on error).

    Example:
        >>> if is_file_updated(service, file_id, last_sync):
        ...     # File needs to be synced
        ...     download_and_upload(file_id)
    """
    try:
        # Retrieve file metadata
        file_metadata = (
            service.files()
            .get(
                fileId=file_id,
                fields="modifiedTime",
            )
            .execute()
        )

        # Parse ISO format timestamp from Google (ends with 'Z' for UTC)
        mod_time_str = file_metadata["modifiedTime"]
        # Convert 'Z' suffix to '+00:00' for fromisoformat compatibility
        mod_time_str = mod_time_str.replace("Z", "+00:00")
        modified_time = datetime.fromisoformat(mod_time_str)

        # Make comparison timezone-naive if last_sync_time is naive
        if last_sync_time.tzinfo is None:
            modified_time = modified_time.replace(tzinfo=None)

        is_updated = modified_time > last_sync_time

        if is_updated:
            logger.debug(
                "File %s modified at %s (after %s)",
                file_id,
                modified_time,
                last_sync_time,
            )

        return is_updated

    except HttpError as error:
        logger.error("Google Drive API error checking file %s: %s", file_id, error)
        return False
    except KeyError:
        logger.error("File %s missing modifiedTime field", file_id)
        return False
    except ValueError as error:
        logger.error("Invalid timestamp format for file %s: %s", file_id, error)
        return False
    except Exception as error:
        logger.error("Unexpected error checking file %s: %s", file_id, error)
        return False


def get_local_modified_time(file_path: Path | str) -> datetime:
    """Get the local modification time of a file.

    Retrieves the modification timestamp of a local file, useful for
    comparing with remote file timestamps.

    Args:
        file_path: Path to the local file.

    Returns:
        The datetime of the file's last modification, or datetime.min
        if the file doesn't exist or cannot be accessed.

    Example:
        >>> local_time = get_local_modified_time("/backups/file.txt")
        >>> if remote_time > local_time:
        ...     # Remote file is newer
        ...     sync_file()
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            return datetime.min

        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime)

    except OSError as error:
        logger.debug("Could not get modification time for %s: %s", file_path, error)
        return datetime.min


def get_files_to_sync(
    service: Resource,
    files: list[dict],
    last_sync_time: datetime,
) -> list[dict]:
    """Filter a list of files to only those needing synchronization.

    Checks each file against the last sync time and returns only those
    that have been modified since then.

    Args:
        service: Authenticated Google Drive API service resource.
        files: List of file metadata dictionaries from Google Drive.
        last_sync_time: The datetime of the last successful sync.

    Returns:
        List of file metadata dictionaries for files that need syncing.

    Example:
        >>> all_files = get_folder_files(service, folder_id)
        >>> files_to_sync = get_files_to_sync(service, all_files, last_sync)
        >>> print(f"{len(files_to_sync)} files need updating")
    """
    files_to_sync = []

    for file in files:
        file_id = file.get("id")
        file_name = file.get("name", "unknown")

        if not file_id:
            logger.warning("File entry missing ID: %s", file)
            continue

        if is_file_updated(service, file_id, last_sync_time):
            files_to_sync.append(file)
            logger.debug("File %s marked for sync", file_name)

    logger.info(
        "%d of %d files need synchronization",
        len(files_to_sync),
        len(files),
    )

    return files_to_sync
