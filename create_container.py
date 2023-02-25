from azure.storage.blob import ContainerClient
from upload_logging import logger


def create_container_if_not_exists(blob_service_client, container_name):
    """
    Creates a container in Azure Blob Storage if it does not already exist.
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)
        if container_client.exists():
            logger.info(f"Container {container_name} already exists")
        else:
            container_client.create_container()
            logger.info(f"Container {container_name} created successfully")
    except Exception as e:
        logger.error(f"Error creating container {container_name}: {str(e)}")
