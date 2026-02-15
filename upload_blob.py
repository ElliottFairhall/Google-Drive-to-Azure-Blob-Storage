"""Azure Blob Storage upload operations.

This module provides functions for uploading files to Azure Blob Storage
with proper error handling and content type configuration.
"""

import logging

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient, ContentSettings

logger = logging.getLogger(__name__)


def upload_blob(
    connection_string: str,
    container_name: str,
    file_name: str,
    data: bytes,
    mime_type: str = "application/octet-stream",
) -> bool:
    """Upload data to Azure Blob Storage.

    Uploads binary data to a specified container in Azure Blob Storage,
    creating a block blob with the specified content type.

    Args:
        connection_string: Azure Storage account connection string.
        container_name: Name of the target container.
        file_name: Name for the blob (can include path-like structure).
        data: Binary content to upload.
        mime_type: MIME type for the blob content. Defaults to
            "application/octet-stream".

    Returns:
        True if upload was successful, False otherwise.

    Raises:
        No exceptions are raised; errors are logged and False is returned.

    Example:
        >>> with open("document.pdf", "rb") as f:
        ...     success = upload_blob(
        ...         conn_str,
        ...         "backups",
        ...         "docs/document.pdf",
        ...         f.read(),
        ...         "application/pdf"
        ...     )
    """
    try:
        # Create BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Get BlobClient for the target blob
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=file_name,
        )

        # Configure content settings
        content_settings = ContentSettings(content_type=mime_type)

        # Upload the blob (overwrite if exists)
        blob_client.upload_blob(
            data,
            blob_type="BlockBlob",
            content_settings=content_settings,
            overwrite=True,
        )

        logger.info("Successfully uploaded %s to %s", file_name, container_name)
        return True

    except AzureError as error:
        logger.error(
            "Azure Storage error uploading %s: %s",
            file_name,
            error,
        )
        return False
    except Exception as error:
        logger.error(
            "Unexpected error uploading %s: %s",
            file_name,
            error,
        )
        return False


def upload_blob_from_stream(
    connection_string: str,
    container_name: str,
    file_name: str,
    stream,
    length: int,
    mime_type: str = "application/octet-stream",
) -> bool:
    """Upload a stream to Azure Blob Storage.

    Uploads data from a file-like stream object, useful for large files
    that shouldn't be loaded entirely into memory.

    Args:
        connection_string: Azure Storage account connection string.
        container_name: Name of the target container.
        file_name: Name for the blob.
        stream: File-like object supporting read().
        length: Total length of the stream in bytes.
        mime_type: MIME type for the blob content.

    Returns:
        True if upload was successful, False otherwise.

    Example:
        >>> with open("large_file.zip", "rb") as f:
        ...     size = os.path.getsize("large_file.zip")
        ...     upload_blob_from_stream(conn, "backup", "file.zip", f, size)
    """
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=file_name,
        )

        content_settings = ContentSettings(content_type=mime_type)

        blob_client.upload_blob(
            stream,
            length=length,
            blob_type="BlockBlob",
            content_settings=content_settings,
            overwrite=True,
        )

        logger.info("Successfully uploaded %s (%d bytes) to %s", file_name, length, container_name)
        return True

    except AzureError as error:
        logger.error("Azure Storage error uploading stream %s: %s", file_name, error)
        return False
    except Exception as error:
        logger.error("Unexpected error uploading stream %s: %s", file_name, error)
        return False
