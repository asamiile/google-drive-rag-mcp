# Google Drive RAG MCP — Agent Instructions

## Project Overview

A local MCP server that lets LLMs (Claude, etc.) securely search and read files
within a **single, designated Google Drive folder** — nothing outside it.

- **Framework**: FastMCP (`fastmcp` package) on Python 3.11+
- **Package manager**: `uv`
- **Auth**: Google Service Account (JSON key file)
- **Access control**: strictly scoped to `TARGET_FOLDER_ID`

## Key Files

| File                 | Purpose                              |
| -------------------- | ------------------------------------ |
| `main.py`            | FastMCP server — all tools live here |
| `pyproject.toml`     | Dependencies managed by uv           |
| `.env`               | Runtime secrets (never commit)       |
| `.env.example`       | Template — commit this               |
| `README.md`          | User-facing setup guide              |
| `.agents/roadmap.md` | Development roadmap                  |

## Running the Server

```bash
# Install dependencies
uv sync

# Copy and fill in env vars
cp .env.example .env

# Start the MCP server
uv run python main.py
```

## Development Rules

1. **Never access files outside `TARGET_FOLDER_ID`** — always verify `parents` before reading.
2. **Fail loudly at startup** — missing env vars must call `sys.exit()` with a clear message.
3. **Return strings from tools** — FastMCP tools must return `str` (JSON-serialized when returning structured data).
4. **Read-only scopes only** — use `drive.readonly` and `documents.readonly`; never request write access.
5. **No secrets in code** — credentials path and folder ID come from env vars only.
6. **Do not commit** `.env` or `*.json` (service account keys) — `.gitignore` enforces this.

## Environment Variables

| Variable                         | Description                                    |
| -------------------------------- | ---------------------------------------------- |
| `GOOGLE_APPLICATION_CREDENTIALS` | Absolute path to service account JSON key      |
| `TARGET_FOLDER_ID`               | Google Drive folder ID to scope all operations |

## MCP Tools

| Tool             | Signature                                                                                  | Description                                                                |
| ---------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| `list_files`     | `(query: str = "") -> str`                                                                 | Lists files in target folder, optional name filter                         |
| `read_file`      | `(file_id: str) -> str`                                                                    | Reads text content of a file (Docs or plain text)                          |
| `search_content` | `(query: str, file_type: str = "", recursive: bool = False, max_results: int = 10) -> str` | Searches file contents for a keyword; returns matching files with snippets |
