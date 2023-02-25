import io
from azure.storage.blob import BlobServiceClient, BlobClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError


def upload_blob(connection_string: str, container_name: str, file_path: str, file_name: str):
    """
    This function uploads a file to Azure Blob Storage.
    """
    try:
        # Create BlobServiceClient object
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Get BlobClient object for uploading file
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

        # Read file into memory and upload to Blob Storage
        with open(file_path, "rb") as data:
            blob_client.upload_blob(
                data,
                blob_type="BlockBlob",
                content_settings=ContentSettings(content_type="application/octet-stream"),
                overwrite=True,
            )

    except ResourceNotFoundError as error:
        print(f"An error occurred: {error}")
