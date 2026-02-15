"""Azure Blob Storage container management.

This module provides functions for creating and managing containers
in Azure Blob Storage.
"""

import logging

from azure.core.exceptions import AzureError, ResourceExistsError
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)


def create_container_if_not_exists(
    blob_service_client: BlobServiceClient,
    container_name: str,
) -> bool:
    """Create a container in Azure Blob Storage if it doesn't exist.

    Checks if the specified container exists and creates it if not.
    This is idempotent - calling multiple times has no adverse effects.

    Args:
        blob_service_client: Authenticated BlobServiceClient instance.
        container_name: Name for the container. Must follow Azure naming rules:
            - 3-63 characters
            - Lowercase letters, numbers, and hyphens only
            - Must start with a letter or number

    Returns:
        True if the container exists or was created successfully,
        False if an error occurred.

    Example:
        >>> client = BlobServiceClient.from_connection_string(conn_str)
        >>> if create_container_if_not_exists(client, "backups"):
        ...     print("Container ready")
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)

        if container_client.exists():
            logger.debug("Container %s already exists", container_name)
            return True

        container_client.create_container()
        logger.info("Container %s created successfully", container_name)
        return True

    except ResourceExistsError:
        # Race condition: container was created between exists check and create
        logger.debug("Container %s was created concurrently", container_name)
        return True
    except AzureError as error:
        logger.error("Azure error creating container %s: %s", container_name, error)
        return False
    except Exception as error:
        logger.error("Unexpected error creating container %s: %s", container_name, error)
        return False


def delete_container(
    blob_service_client: BlobServiceClient,
    container_name: str,
) -> bool:
    """Delete a container from Azure Blob Storage.

    Permanently removes the container and all blobs within it.
    Use with caution as this operation cannot be undone.

    Args:
        blob_service_client: Authenticated BlobServiceClient instance.
        container_name: Name of the container to delete.

    Returns:
        True if the container was deleted or didn't exist,
        False if an error occurred.

    Example:
        >>> delete_container(client, "old-backups")
        True
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)

        if not container_client.exists():
            logger.debug("Container %s does not exist", container_name)
            return True

        container_client.delete_container()
        logger.info("Container %s deleted successfully", container_name)
        return True

    except AzureError as error:
        logger.error("Azure error deleting container %s: %s", container_name, error)
        return False
    except Exception as error:
        logger.error("Unexpected error deleting container %s: %s", container_name, error)
        return False


def list_containers(blob_service_client: BlobServiceClient) -> list[str]:
    """List all containers in the storage account.

    Args:
        blob_service_client: Authenticated BlobServiceClient instance.

    Returns:
        List of container names, or empty list on error.

    Example:
        >>> containers = list_containers(client)
        >>> for name in containers:
        ...     print(f"Found container: {name}")
    """
    try:
        containers = blob_service_client.list_containers()
        names = [c["name"] for c in containers]
        logger.debug("Found %d containers", len(names))
        return names

    except AzureError as error:
        logger.error("Azure error listing containers: %s", error)
        return []
    except Exception as error:
        logger.error("Unexpected error listing containers: %s", error)
        return []
