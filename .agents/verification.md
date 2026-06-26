# Verification Checklist

## End-to-End Testing

### How to Run Tests

```bash
# List registered tools
uv run fastmcp list main.py

# Call a tool — arguments are passed as key=value pairs
uv run fastmcp call main.py list_files
uv run fastmcp call main.py list_files query="report"
uv run fastmcp call main.py read_document file_id="<FILE_ID>"

# Open interactive inspector (requires npm)
# Fix npm permissions if needed: sudo chown -R 501:20 "/Users/asami/.npm"
uv run fastmcp dev inspector main.py
```

---

### Startup Validation

- [ ] Run without `.env` → `ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set in .env`
- [ ] Set a non-existent path for `GOOGLE_APPLICATION_CREDENTIALS` → `ERROR: Credentials file not found: ...`
- [ ] Unset `TARGET_FOLDER_ID` only → `ERROR: TARGET_FOLDER_ID is not set in .env`
- [x] Run with a valid `.env` → server starts successfully

### `list_files` Tool

- [x] Call with no arguments → returns JSON list of files in the target folder
- [ ] Call with a `query` argument → returns only files matching the name
- [ ] Call against an empty folder → returns `"No files found."`

### `read_document` Tool

- [x] Pass a Google Doc file ID → returns plain text content
- [ ] Pass a plain text file ID → returns file content
- [ ] Pass an unsupported MIME type file ID → `ToolError: Unsupported file type ...`

### Security Check

- [ ] Pass a file ID outside the target folder → `ToolError: File '...' is not in the target folder. Access denied.`
