# Import required libraries
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from auth import get_credentials
from upload_logging import logger
from create_container import create_container_if_not_exists
from upload_blob import upload_blob
from get_drive_files import get_all_files, is_folder, get_folder_files
from incremental_sync import is_file_updated, get_local_modified_time
from azure.storage.blob import BlockBlobService

# Load the enviroment variables
load_dotenv()

# Use the enviroment variables
google_application_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
azure_account_name = os.getenv("AZURE_ACCOUNT_NAME")
azure_account_key = os.getenv("AZURE_ACCOUNT_KEY")
azure_container = os.getenv("AZURE_CONTAINER")
event_hub_connection_string = os.getenv("EVENT_HUB_CONNECTION_STRING")
event_hub_name = os.getenv("EVENT_HUB_NAME")


def main():

    logger.info("Starting Google Drive to Azure Blob Storage transfer...")

    # Get credentials for Google Drive API
    creds = get_credentials()

    # Set up Google Drive API client
    service = build('drive', 'v3', credentials=creds)

    # Set up Azure Blob Storage client
    blob_service_client = BlockBlobService(account_name=os.environ['AZURE_ACCOUNT_NAME'],
                                           account_key=os.environ['AZURE_ACCOUNT_KEY'])

    # Create container if it does not exist
    create_container_if_not_exists(blob_service_client, os.environ['AZURE_CONTAINER'])

    # Get all files in Google Drive
    drive_files = get_all_files(service)

    # Get folder ID for folder to sync
    folder_id = os.environ.get('FOLDER_ID')
    if not folder_id:
        logger.error("No folder ID provided")
        return

    # Check if the folder exists
    if not is_folder(service, folder_id):
        logger.error(f"Folder with ID {folder_id} does not exist in Google Drive")
        return

    # Get all files in the specified folder
    folder_files = get_folder_files(service, folder_id)

    # Set up incremental sync
    last_sync_time = datetime.strptime(os.environ.get('LAST_SYNC_TIME'), '%Y-%m-%d %H:%M:%S.%f') \
        if os.environ.get('LAST_SYNC_TIME') else datetime.min
    incremental_sync_enabled = os.environ.get('INCREMENTAL_SYNC_ENABLED') == 'True'

    # Upload all files in the specified folder
    for file in folder_files:
        file_name = file['name']
        file_id = file['id']
        file_mime_type = file['mimeType']
        local_modified_time = get_local_modified_time(file_id)

        if incremental_sync_enabled and not is_file_updated(service, file_id, last_sync_time):
            logger.info(f"Skipping file {file_name} as it has not been modified since last sync")
            continue

        logger.info(f"Uploading file {file_name}")
        try:
            upload_blob(blob_service_client, os.environ['AZURE_CONTAINER'], file_name, file_id, file_mime_type)
            logger.info(f"File {file_name} uploaded successfully")
        except Exception as e:
            logger.error(f"Error uploading file {file_name}: {str(e)}")

    # Log time of last sync
    if incremental_sync_enabled:
        os.environ['LAST_SYNC_TIME'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        logger.info(f"Last sync time logged: {os.environ['LAST_SYNC_TIME']}")

    logger.info("Google Drive to Azure Blob Storage transfer complete.")

if __name__ == '__main__':
    main()
