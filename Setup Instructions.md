# Setup Instructions

This guide walks you through setting up the Google Drive to Azure Blob Storage sync solution.

## Prerequisites

- Azure subscription
- Google Cloud Platform account
- Python 3.10+ installed
- Azure CLI installed (optional, for easier setup)

## Azure Setup

### 1. Create an Azure Storage Account

1. Navigate to the [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** > **Storage** > **Storage account**
3. Configure:
   - **Subscription**: Select your subscription
   - **Resource group**: Create new or select existing
   - **Storage account name**: Choose a unique name (e.g., `gdrivebackup2024`)
   - **Region**: Select your preferred region
   - **Performance**: Standard
   - **Redundancy**: LRS (or higher for production)
4. Click **Review + create** > **Create**
5. After deployment, go to **Access keys** and copy the **Connection string**

### 2. Create an Azure Key Vault

1. In Azure Portal, click **Create a resource** > **Key Vault**
2. Configure:
   - **Key vault name**: Choose a unique name (e.g., `gdrive-backup-kv`)
   - **Region**: Same as your storage account
   - **Pricing tier**: Standard
3. Click **Review + create** > **Create**
4. After deployment, note the **Vault name** (not the full URI)

### 3. Configure Key Vault Access

#### Option A: Using Managed Identity (Recommended for Azure hosting)

1. Enable managed identity on your compute resource (VM, Function App, etc.)
2. In Key Vault, go to **Access policies** > **Add Access Policy**
3. Configure:
   - **Secret permissions**: Get, List
   - **Select principal**: Search for your managed identity
4. Click **Add** > **Save**

#### Option B: Using Service Principal (For local development)

1. Register an application in Azure AD:

   ```bash
   az ad app create --display-name "GDrive-Backup-App"
   ```

2. Create a service principal:

   ```bash
   az ad sp create --id <app-id>
   ```

3. Assign Key Vault access (see step 3 above)

4. Set environment variables:

   ```bash
   export AZURE_CLIENT_ID=<app-id>
   export AZURE_CLIENT_SECRET=<client-secret>
   export AZURE_TENANT_ID=<tenant-id>
   ```

### 4. Store Google Credentials in Key Vault

After completing the Google setup below, store the credentials:

```bash
# Using Azure CLI
az keyvault secret set \
  --vault-name "gdrive-backup-kv" \
  --name "google-drive-credentials" \
  --file "service-account.json"
```

Or via Azure Portal:

1. Go to your Key Vault > **Secrets** > **Generate/Import**
2. **Name**: `google-drive-credentials`
3. **Value**: Paste the entire content of your service account JSON
4. Click **Create**

## Google Cloud Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Select a project** > **New Project**
3. Enter a project name and click **Create**
4. Note your **Project ID**

### 2. Enable the Google Drive API

1. In your project, go to **APIs & Services** > **Library**
2. Search for "Google Drive API"
3. Click **Enable**

### 3. Create a Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service account**
3. Configure:
   - **Service account name**: `gdrive-backup`
   - **Service account ID**: Auto-generated
4. Click **Create and Continue**
5. Skip the optional steps, click **Done**

### 4. Generate Service Account Key

1. Click on the service account you just created
2. Go to **Keys** tab > **Add Key** > **Create new key**
3. Select **JSON** format
4. Click **Create** - the key file will download
5. **Important**: Store this file securely, then upload to Azure Key Vault

### 5. Share the Google Drive Folder

1. Open Google Drive
2. Right-click the folder you want to backup
3. Click **Share**
4. Add the service account email (e.g., `gdrive-backup@project-id.iam.gserviceaccount.com`)
5. Set permission to **Viewer**
6. Click **Send**

### 6. Get the Folder ID

1. Open the folder in Google Drive

2. Copy the ID from the URL:

   ```
   https://drive.google.com/drive/folders/[THIS_IS_THE_FOLDER_ID]
   ```

## Application Setup

### 1. Clone and Install

```bash
git clone https://github.com/elliottfairhall/Google-Drive-to-Azure-Blob-Storage.git
cd Google-Drive-to-Azure-Blob-Storage

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_CONTAINER=gdrive-backup
KEY_VAULT_NAME=gdrive-backup-kv
GOOGLE_APPLICATION_CREDENTIALS_SECRET_NAME=google-drive-credentials
FOLDER_ID=your_folder_id_here
INCREMENTAL_SYNC_ENABLED=true
```

### 3. Test the Connection

```bash
python main.py
```

## Deployment Options

### Azure Functions (Serverless)

1. Create an Azure Function App (Python runtime)
2. Enable managed identity
3. Configure Key Vault access for the managed identity
4. Deploy the code using VS Code Azure Functions extension or CLI
5. Set up a Timer trigger for scheduled execution

### Azure VM / Container Instance

1. Deploy to a VM or container
2. Use managed identity or service principal for authentication
3. Set up a cron job or scheduled task

### Local/On-Premises

1. Run on any machine with Python 3.10+
2. Use service principal authentication
3. Schedule with cron (Linux) or Task Scheduler (Windows)

## Verification

After setup, verify everything works:

1. Check logs in `logs/sync.log`
2. Verify files appear in Azure Blob Storage
3. Confirm incremental sync only transfers changed files

## Troubleshooting

### "DefaultAzureCredential failed"

- Ensure Azure CLI is logged in: `az login`
- Or set service principal environment variables

### "Folder not found" error

- Verify the folder ID is correct
- Ensure the service account has access to the folder

### "Permission denied" in Azure Storage

- Check the connection string is correct
- Verify the container exists or can be created

## Cost Estimation

| Service            | Usage                 | Estimated Cost  |
| ------------------ | --------------------- | --------------- |
| Azure Blob Storage | Per GB stored         | ~$0.02/GB/month |
| Azure Key Vault    | Per 10,000 operations | ~$0.03          |
| Google Drive API   | Free tier             | $0              |

Total: Minimal for small-to-medium backups (\< $5/month typically)
