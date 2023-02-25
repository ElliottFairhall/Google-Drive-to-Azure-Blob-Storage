import os
from dotenv import load_dotenv
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Load the enviroment variables
load_dotenv()

# Use the enviroment variables
google_application_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
azure_account_name = os.getenv("AZURE_ACCOUNT_NAME")
azure_account_key = os.getenv("AZURE_ACCOUNT_KEY")
azure_container = os.getenv("AZURE_CONTAINER")
event_hub_connection_string = os.getenv("EVENT_HUB_CONNECTION_STRING")
event_hub_name = os.getenv("EVENT_HUB_NAME")

def get_credentials():
    credential = DefaultAzureCredential()
    kv_name = os.environ["KEY_VAULT_NAME"]
    secret_name = os.environ["GOOGLE_APPLICATION_CREDENTIALS_SECRET_NAME"]
    key_vault_uri = f"https://{kv_name}.vault.azure.net"
    client = SecretClient(vault_url=key_vault_uri, credential=credential)
    secret = client.get_secret(secret_name)
    return secret.value
