# Development Roadmap

## Phase 0 — Agent Files (current)

- [x] `AGENTS.md` — agent instructions
- [x] `.agents/roadmap.md` — this file
- [x] `settings.json` — MCP client config template

## Phase 1 — Project Scaffold

- [x] `pyproject.toml` — uv project with dependencies
- [x] `.env.example` — env var template
- [x] `.gitignore` — exclude secrets and caches

## Phase 2 — Server Implementation (`main.py`)

- [ ] Startup validation (`GOOGLE_APPLICATION_CREDENTIALS`, `TARGET_FOLDER_ID`)
- [ ] Google API client initialization (Drive v3, Docs v1)
- [ ] Tool: `list_files(query)` — search files in target folder
- [ ] Tool: `read_document(file_id)` — read Google Docs / plain text
- [ ] Security check in `read_document` — verify file is in target folder

## Phase 3 — Documentation (`README.md`)

- [ ] Overview + Claude Desktop / Glama config JSON
- [ ] Step 1: Create GCP project, enable Drive/Docs APIs
- [ ] Step 2: Create service account, download JSON key
- [ ] Step 3: Share target Drive folder with service account email
- [ ] Step 4: Local setup (`.env`) and launch command

## Phase 4 — Verification

- [ ] `uv sync` succeeds
- [ ] Server exits with clear error when `.env` is missing
- [ ] `list_files` returns files from target folder
- [ ] `read_document` returns text from a Google Doc
- [ ] `read_document` rejects a file outside the target folder
