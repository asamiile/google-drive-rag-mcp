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

- [x] Startup validation (`GOOGLE_APPLICATION_CREDENTIALS`, `TARGET_FOLDER_ID`)
- [x] Google API client initialization (Drive v3, Docs v1)
- [x] Tool: `list_files(query)` — search files in target folder
- [x] Tool: `read_document(file_id)` — read Google Docs / plain text
- [x] Security check in `read_document` — verify file is in target folder

## Phase 3 — Documentation (`README.md`)

- [x] Overview + Claude Desktop / Glama config JSON
- [x] Step 1: Create GCP project, enable Drive/Docs APIs
- [x] Step 2: Create service account, download JSON key
- [x] Step 3: Share target Drive folder with service account email
- [x] Step 4: Local setup (`.env`) and launch command
- [x] Implement Google Sheets support (`export` as CSV via Drive API)
- [x] Implement PDF support (download binary + extract text with `pymupdf`)
- [x] Document supported file formats (Google Docs, plain text, Google Sheets, PDF)

## Phase 4 — Verification

- [x] `uv sync` succeeds
- [x] Server exits with clear error when `.env` is missing
- [x] `list_files` returns files from target folder
- [x] `read_document` returns text from a Google Doc
- [x] `read_document` rejects a file outside the target folder

## Phase 5 — Client Integration

- [ ] Configure Claude Desktop (add to `claude_desktop_config.json`)
- [ ] Configure Claude Code (`claude mcp add`)
- [ ] Verify tools are available in Claude

## Phase 6 — Publishing

- [x] Fix `pyproject.toml`: `requires-python = ">=3.11"` and proper description
- [x] Add `LICENSE` file (MIT)
- [x] Add `.github/dependabot.yml` — automated dependency updates
- [x] Add `.github/workflows/release.yml` — automated release workflow
- [ ] Push to GitHub (public repository)
- [ ] Submit to Glama
- [ ] Add Glama badge to `README.md`
