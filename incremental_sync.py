import os
from datetime import datetime
from googleapiclient.discovery import build


def is_file_updated(service: build, file_id: str, last_sync_time: datetime) -> bool:
    """
    This function checks if a file has been updated since the last sync.
    """
    try:
        # Retrieve file metadata
        file_metadata = service.files().get(fileId=file_id, fields='modifiedTime').execute()
        modified_time = datetime.fromisoformat(file_metadata['modifiedTime'][:-1])

        return modified_time > last_sync_time

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def get_local_modified_time(file_id: str) -> datetime:
    """
    This function retrieves the local modified time of a file.
    """
    try:
        # Get local modified time of file
        file_path = os.path.join(os.environ['LOCAL_FOLDER'], file_id)
        local_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

        return local_modified_time

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return datetime.min
