import json
import os
import sys

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from dotenv import load_dotenv
import fitz
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

# --- Startup validation ---
CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
TARGET_FOLDER_IDS_RAW = os.environ.get("TARGET_FOLDER_IDS")

if not CREDENTIALS_PATH:
	sys.exit("ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set in .env")
if not os.path.exists(CREDENTIALS_PATH):
	sys.exit(f"ERROR: Credentials file not found: {CREDENTIALS_PATH}")
if not TARGET_FOLDER_IDS_RAW:
	sys.exit("ERROR: TARGET_FOLDER_IDS is not set in .env")

TARGET_FOLDER_IDS = [fid.strip() for fid in TARGET_FOLDER_IDS_RAW.split(",") if fid.strip()]
if not TARGET_FOLDER_IDS:
	sys.exit("ERROR: TARGET_FOLDER_IDS is empty in .env")

# --- Google API client initialization ---
SCOPES =[
	"https://www.googleapis.com/auth/drive.readonly",
	"https://www.googleapis.com/auth/documents.readonly",
]

credentials = service_account.Credentials.from_service_account_file(
	CREDENTIALS_PATH, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)

FILE_TYPE_MAP = {
	"document":    "mimeType = 'application/vnd.google-apps.document'",
	"spreadsheet": "mimeType = 'application/vnd.google-apps.spreadsheet'",
	"pdf":         "mimeType = 'application/pdf'",
	"image":       "mimeType contains 'image/'",
	"text":        "mimeType = 'text/plain'",
}

# --- File collection　---
def _collect_files(folder_id: str, query: str, _depth: int = 0, recursive: bool = True, file_type: str = "") -> list:
	if _depth > 5:
		return []

	file_q = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
	if query:
		file_q += f" and name contains '{query}'"
	if file_type and file_type in FILE_TYPE_MAP:
		file_q += f" and ({FILE_TYPE_MAP[file_type]})"

	files = drive_service.files().list(
		q=file_q, fields="files(id, name, mimeType)", pageSize=100
	).execute().get("files", [])

	if recursive:
		folder_q = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
		folders = drive_service.files().list(
			q=folder_q, fields="files(id)", pageSize=100
		).execute().get("files", [])
		for folder in folders:
			files.extend(_collect_files(folder["id"], query, _depth + 1, recursive, file_type))
	return files

# --- Folder collection ---
def _collect_folders(folder_id: str, _depth: int = 0, recursive: bool = False) -> list:
	if _depth > 5:
		return []

	folder_q = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
	folders = drive_service.files().list(
		q=folder_q, fields="files(id, name)", pageSize=100
	).execute().get("files", [])

	result = list(folders)
	if recursive:
		for folder in folders:
			result.extend(_collect_folders(folder["id"], _depth + 1, recursive))
	return result

# --- Security check　---
def _is_in_target_folder(file_id: str) -> bool:
	try:
		meta = drive_service.files().get(fileId=file_id, fields="parents").execute()
	except Exception:
		return False
	parents = meta.get("parents", [])
	if any(fid in parents for fid in TARGET_FOLDER_IDS):
		return True
	return any(_is_in_target_folder(p) for p in parents)

# --- FastMCP server ---
mcp = FastMCP("Google Drive RAG")

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def list_files(query: str = "", recursive: bool = False, folder_id: str = "", file_type: str = "") -> str:
	"""List files in the target Google Drive folders. Optionally filter by name.
	- folder_id: scope to a specific folder (use list_folders to find IDs)
	- recursive: set True to include subfolders — recommended when folder_id is specified or files may be nested
	- file_type: filter by type — 'document', 'spreadsheet', 'pdf', 'image', 'text'	
	"""
	target_ids = [folder_id] if folder_id else TARGET_FOLDER_IDS
	files = []
	for fid in target_ids:
		files.extend(_collect_files(fid, query, recursive=recursive, file_type=file_type))
	if not files:
		return "No files found."
	return json.dumps(files, ensure_ascii=False, indent=2)

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def list_folders(recursive: bool = False) -> str:
	"""List folders in the target Google Drive folders. Set recursive=True to include subfolders."""
	folders = []
	for folder_id in TARGET_FOLDER_IDS:
		folders.extend(_collect_folders(folder_id, recursive=recursive))
	if not folders:
		return "No folders found."
	return json.dumps(folders, ensure_ascii=False, indent=2)

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def read_document(file_id: str) -> str:
	"""Read the text content of a file in the target Google Drive folder."""
	# Security check
	if not _is_in_target_folder(file_id):
		raise ToolError(f"File '{file_id}' is not in the target folder. Access denied.")

	file_meta = (
		drive_service.files()
		.get(fileId=file_id, fields="id, name, mimeType")
		.execute()
	)
	
	mime_type = file_meta.get("mimeType", "")

	if mime_type == "application/vnd.google-apps.spreadsheet":
		content = (
			drive_service.files()
			.export(fileId=file_id, mimeType="text/csv")
			.execute()
		)
		return content.decode("utf-8")

	if mime_type == "application/vnd.google-apps.document":
		content = (
			drive_service.files()
			.export(fileId=file_id, mimeType="text/plain")
			.execute()
		)
		return content.decode("utf-8")
	
	if mime_type.startswith("text/"):
		content = drive_service.files().get_media(fileId=file_id).execute()
		return content.decode("utf-8")

	if mime_type == "application/pdf":
		pdf_bytes = drive_service.files().get_media(fileId=file_id).execute()
		doc = fitz.open(stream=pdf_bytes, filetype="pdf")
		text = "\n".join(str(page.get_text()) for page in doc)
		doc.close()
		return text

	raise ToolError(f"Unsupported file type '{mime_type}'. Only Google Docs and plain text files are supported.")

if __name__ == "__main__":
  mcp.run()
