"""Authentication utilities for Google Drive and Azure services.

This module provides functions for authenticating with Google Drive API
using credentials stored in Azure Key Vault.
"""

import json
import logging
import os
from pathlib import Path
from typing import cast

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def get_key_vault_client() -> SecretClient:
    """Create an Azure Key Vault client using default credentials.

    Uses DefaultAzureCredential which supports multiple authentication
    methods including managed identity, environment variables, and Azure CLI.

    Returns:
        SecretClient configured to access the Key Vault specified by
        the KEY_VAULT_NAME environment variable.

    Raises:
        KeyError: If KEY_VAULT_NAME environment variable is not set.
        azure.core.exceptions.ClientAuthenticationError: If authentication fails.

    Example:
        >>> client = get_key_vault_client()
        >>> secret = client.get_secret("my-secret")
    """
    credential = DefaultAzureCredential()
    kv_name = os.environ["KEY_VAULT_NAME"]
    key_vault_uri = f"https://{kv_name}.vault.azure.net"

    logger.debug("Connecting to Key Vault: %s", kv_name)
    return SecretClient(vault_url=key_vault_uri, credential=credential)


def get_credentials() -> ServiceAccountCredentials:
    """Retrieve Google Drive API credentials from Azure Key Vault.

    Fetches the Google service account credentials JSON from Azure Key Vault
    and creates a credentials object for the Google Drive API.

    Returns:
        Google ServiceAccountCredentials object configured with Drive API scope.

    Raises:
        KeyError: If required environment variables are not set.
        ValueError: If the secret value is not valid JSON.
        azure.core.exceptions.ResourceNotFoundError: If the secret doesn't exist.

    Environment Variables:
        KEY_VAULT_NAME: Name of the Azure Key Vault.
        GOOGLE_APPLICATION_CREDENTIALS_SECRET_NAME: Name of the secret
            containing the Google service account JSON.

    Example:
        >>> creds = get_credentials()
        >>> service = build('drive', 'v3', credentials=creds)
    """
    secret_name = os.environ["GOOGLE_APPLICATION_CREDENTIALS_SECRET_NAME"]

    logger.info("Retrieving Google credentials from Key Vault")
    client = get_key_vault_client()
    secret = client.get_secret(secret_name)

    # Parse the service account JSON
    credentials_info = json.loads(secret.value)

    # Create credentials with Drive API scope
    credentials = ServiceAccountCredentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )

    logger.info("Google Drive credentials loaded successfully")
    return cast("ServiceAccountCredentials", credentials)


def get_credentials_from_file(credentials_path: Path | str) -> ServiceAccountCredentials:
    """Load Google Drive API credentials from a local file.

    Alternative authentication method using a local service account
    JSON file instead of Azure Key Vault.

    Args:
        credentials_path: Path to the service account JSON file.

    Returns:
        Google ServiceAccountCredentials object configured with Drive API scope.

    Raises:
        FileNotFoundError: If the credentials file doesn't exist.
        ValueError: If the file is not valid JSON.

    Example:
        >>> creds = get_credentials_from_file("service-account.json")
        >>> service = build('drive', 'v3', credentials=creds)
    """
    credentials_path = Path(credentials_path)

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

    logger.info("Loading Google credentials from file: %s", credentials_path)

    credentials = ServiceAccountCredentials.from_service_account_file(
        str(credentials_path),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )

    logger.info("Google Drive credentials loaded from file successfully")
    return cast("ServiceAccountCredentials", credentials)
