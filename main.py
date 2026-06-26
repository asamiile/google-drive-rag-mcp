import json
import os
import sys

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

# --- Startup validation ---
CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
TARGET_FOLDER_ID = os.environ.get("TARGET_FOLDER_ID")

if not CREDENTIALS_PATH:
	sys.exit("ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set in .env")
if not os.path.exists(CREDENTIALS_PATH):
	sys.exit(f"ERROR: Credentials file not found: {CREDENTIALS_PATH}")
if not TARGET_FOLDER_ID:
	sys.exit("ERROR: TARGET_FOLDER_ID is not set in .env")

# --- Google API client initialization ---
SCOPES =[
	"https://www.googleapis.com/auth/drive.readonly",
	"https://www.googleapis.com/auth/documents.readonly",
]

credentials = service_account.Credentials.from_service_account_file(
	CREDENTIALS_PATH, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)

# --- ---
def _collect_files(folder_id: str, query: str, _depth: int = 0) -> list:
	if _depth > 5:
		return []

	folder_q = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
	file_q = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
	if query:
		file_q += f" and name contains '{query}'"

	folders = drive_service.files().list(
		q=folder_q, fields="files(id)", pageSize=100
	).execute().get("files", [])

	files = drive_service.files().list(
		q=file_q, fields="files(id, name, mimeType)", pageSize=100
	).execute().get("files", [])

	for folder in folders:
		files.extend(_collect_files(folder["id"], query, _depth + 1))
	return files

# --- ---
def _is_in_target_folder(file_id: str) -> bool:
	try:
		meta = drive_service.files().get(fileId=file_id, fields="parents").execute()
	except Exception:
		return False
	parents = meta.get("parents", [])
	if TARGET_FOLDER_ID in parents:
		return True
	return any(_is_in_target_folder(p) for p in parents)
	
# --- FastMCP server ---
mcp = FastMCP("Google Drive RAG")

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def list_files(query: str = "") -> str:
	"""List all files in the target Google Drive folder (including subfolders). Optionally filter by name."""
	files = _collect_files(TARGET_FOLDER_ID or "", query)
	if not files:
		return "No files found."
	return json.dumps(files, ensure_ascii=False, indent=2)

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

	raise ToolError(f"Unsupported file type '{mime_type}'. Only Google Docs and plain text files are supported.")

if __name__ == "__main__":
  mcp.run()
