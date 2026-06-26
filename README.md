# google-drive-rag-mcp

A local MCP server that lets LLMs (Claude, etc.) securely search and read files within a single, designated Google Drive folder.

## Overview

- Scoped to a single folder — never accesses files outside `TARGET_FOLDER_ID`
- Authenticated via Google Service Account (no personal OAuth required)
- Read-only access (`drive.readonly`, `documents.readonly`)
- Built with [FastMCP](https://gofastmcp.com) on Python 3.11+

### MCP Tools

| Tool                     | Description                                                  |
| ------------------------ | ------------------------------------------------------------ |
| `list_files(query)`      | List files in the target folder, optionally filtered by name |
| `read_document(file_id)` | Read text content of a Google Doc or plain text file         |

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-drive-rag": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/path/to/google-drive-rag-mcp",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "TARGET_FOLDER_ID": "your_google_drive_folder_id_here"
      }
    }
  }
}
```

## Setup

### Step 1 — Create a GCP Project and Enable APIs

1. Open [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services > Library**
4. Search for and enable the following APIs:
   - **Google Drive API**
   - **Google Docs API**

### Step 2 — Create a Service Account and Download the JSON Key

1. Navigate to **APIs & Services > Credentials**
2. Click **Create Credentials > Service Account**
3. Enter a name (e.g., `drive-rag-reader`) and click **Done**
4. Click the created service account, go to the **Keys** tab
5. Click **Add Key > Create new key**, select **JSON**, and download the file
6. Save the file to a secure location (e.g., `~/.config/gcp/drive-rag-key.json`)

> **Note**: Never commit this file to Git. It is excluded by `.gitignore`.

### Step 3 — Share the Target Google Drive Folder

1. Open [Google Drive](https://drive.google.com)
2. Right-click the target folder and select **Share**
3. Enter the service account email address (e.g., `drive-rag-reader@your-project.iam.gserviceaccount.com`)
   - Found in **GCP Console > IAM & Admin > Service Accounts**
4. Set the role to **Viewer** and click **Send**

> The folder ID is the last part of the folder URL:  
> `https://drive.google.com/drive/folders/`**`THIS_IS_THE_FOLDER_ID`**

### Step 4 — Local Setup and Launch

```bash
# 1. Clone the repository
git clone https://github.com/your-username/google-drive-rag-mcp.git
cd google-drive-rag-mcp

# 2. Install dependencies
uv sync

# 3. Configure environment variables
cp .env.example .env
```

Edit `.env`:

```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
TARGET_FOLDER_ID=your_google_drive_folder_id_here
```

```bash
# 4. Start the MCP server
uv run python main.py
```

## Development

```bash
# Run the server
uv run python main.py

# Add a dependency
uv add <package>
```

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Support

If you find this helpful, consider supporting the work:

[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/asamiile)

## Author

[Asami.K](https://asami.tokyo/)
