# google-drive-rag-mcp

[![google-drive-rag-mcp MCP server](https://glama.ai/mcp/servers/asamiile/google-drive-rag-mcp/badges/card.svg)](https://glama.ai/mcp/servers/asamiile/google-drive-rag-mcp)

A local MCP server that lets LLMs (Claude, etc.) securely search and read files within a single, designated Google Drive folder.

## Overview

- Scoped to specified folders — never accesses files outside `TARGET_FOLDER_IDS`
- Authenticated via Google Service Account (no personal OAuth required)
- Read-only access (`drive.readonly`, `documents.readonly`)
- Built with [FastMCP](https://gofastmcp.com) on Python 3.11+

## Use Cases

- **Research**: Ask Claude to find and summarize documents stored in a shared Google Drive folder
- **Team knowledge base**: Search internal documents, reports, or meeting notes by keyword
- **Study notes**: Retrieve lecture notes or course materials from a Drive folder and ask questions about them
- **Document Q&A**: "What does the report from last month say about X?" — Claude reads and answers

## MCP Tools

| Tool                 | Description                                                  |
| -------------------- | ------------------------------------------------------------ |
| `list_files(query)`  | List files in the target folder, optionally filtered by name |
| `read_file(file_id)` | Read text content of a supported file                        |

### Supported File Formats

| Format        | MIME Type                                 | How it's read              |
| ------------- | ----------------------------------------- | -------------------------- |
| Google Docs   | `application/vnd.google-apps.document`    | Exported as plain text     |
| Google Sheets | `application/vnd.google-apps.spreadsheet` | Exported as CSV            |
| PDF           | `application/pdf`                         | Text extracted via PyMuPDF |
| Plain text    | `text/*`                                  | Read directly              |

## MCP Setup

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

> **Tip — Multiple folders**: You can share a parent folder with the service account and set individual subfolders in `TARGET_FOLDER_IDS`. Access to subfolders is inherited from the parent.
>
> ```
> Parent Folder        ← Share with the service account (Viewer)
> ├── Project A        ← Add this folder ID to TARGET_FOLDER_IDS
> └── Project B        ← Add this folder ID to TARGET_FOLDER_IDS
> ```
>
> `.env` example:
>
> ```
> TARGET_FOLDER_IDS=project_a_folder_id,project_b_folder_id
> ```

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
TARGET_FOLDER_IDS=folder_id_1,folder_id_2
```

### Step 5 — Connect to Claude

#### Claude Desktop

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
        "TARGET_FOLDER_IDS": "folder_id_1,folder_id_2"
      }
    }
  }
}
```

Restart Claude Desktop to apply the changes.

#### Claude Code

```bash
claude mcp add google-drive-rag \
  -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json \
  -e TARGET_FOLDER_IDS=folder_id_1,folder_id_2 \
  -- uv run python /path/to/google-drive-rag-mcp/main.py
```

To make it available across all projects, add `--scope user`:

```bash
claude mcp add --scope user google-drive-rag \
  -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json \
  -e TARGET_FOLDER_IDS=folder_id_1,folder_id_2 \
  -- uv run python /path/to/google-drive-rag-mcp/main.py
```

Verify the registration:

```bash
claude mcp list
```

This command only needs to be run once. The configuration is saved and loaded automatically on every Claude Code startup.

Re-run it only if you:

- Change environment variables (folder IDs or credentials path)
- Move `main.py` to a different path
- Need to reset the registration (`claude mcp remove google-drive-rag`)

## Development

- Run the server

```bash
uv run python main.py
```

- Start the MCP server

```bash
uv run python main.py
```

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Support

If you find this helpful, consider supporting the work:

[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/asamiile)

## Author

[Asami.K](https://asami.tokyo/)
