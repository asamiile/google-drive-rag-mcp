import json
import os

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from dotenv import load_dotenv
import fitz
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

SCOPES =[
	"https://www.googleapis.com/auth/drive.readonly",
	"https://www.googleapis.com/auth/documents.readonly",
]

_drive_service = None

def _get_drive_service():
	global _drive_service
	if _drive_service is not None:
		return _drive_service
	credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
	if not credentials_path:
		raise ToolError("GOOGLE_APPLICATION_CREDENTIALS is not set.")
	if not os.path.exists(credentials_path):
		raise ToolError(f"Credentials file not found: {credentials_path}")
	credentials = service_account.Credentials.from_service_account_file(
		credentials_path, scopes=SCOPES
	)
	_drive_service = build("drive", "v3", credentials=credentials)
	return _drive_service

def _get_target_folder_ids() -> list[str]:
	raw = os.environ.get("TARGET_FOLDER_IDS", "")
	ids = [fid.strip() for fid in raw.split(",") if fid.strip()]
	if not ids:
		raise ToolError("TARGET_FOLDER_IDS is not set or empty.")
	return ids

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

	files = _get_drive_service().files().list(
		q=file_q, fields="files(id, name, mimeType)", pageSize=100
	).execute().get("files", [])

	if recursive:
		folder_q = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
		folders = _get_drive_service().files().list(
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
	folders = _get_drive_service().files().list(
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
		meta = _get_drive_service().files().get(fileId=file_id, fields="parents").execute()
	except Exception:
		return False
	parents = meta.get("parents", [])
	if any(fid in parents for fid in _get_target_folder_ids()):
		return True
	return any(_is_in_target_folder(p) for p in parents)

# --- File content reading ---
def _read_file_content(file_id: str, mime_type: str) -> str:
	if mime_type == "application/vnd.google-apps.spreadsheet":
		return _get_drive_service().files().export(fileId=file_id, mimeType="text/csv").execute().decode("utf-8")
	if mime_type == "application/vnd.google-apps.document":
		return _get_drive_service().files().export(fileId=file_id, mimeType="text/plain").execute().decode("utf-8")
	if mime_type.startswith("text/"):
		return _get_drive_service().files().get_media(fileId=file_id).execute().decode("utf-8")
	if mime_type == "application/pdf":
		pdf_bytes = _get_drive_service().files().get_media(fileId=file_id).execute()
		doc = fitz.open(stream=pdf_bytes, filetype="pdf")
		text = "\n".join(str(page.get_text()) for page in doc)
		doc.close()
		return text
	raise ToolError(f"Unsupported file type '{mime_type}'.")

# --- Snippet extraction ---
def _extract_snippet(content: str, query: str, context_chars: int = 200) -> str:
	idx = content.lower().find(query.lower())
	if idx == -1:
		return ""
	start = max(0, idx - context_chars)
	end = min(len(content), idx + len(query) + context_chars)
	snippet = content[start:end]
	if start > 0:
		snippet = "…" + snippet
	if end < len(content):
		snippet = snippet + "…"
	return snippet

# --- FastMCP server ---
mcp = FastMCP("Google Drive RAG")

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def list_files(query: str = "", recursive: bool = False, folder_id: str = "", file_type: str = "") -> str:
	"""
	List files in the target Google Drive folders. Use this to discover files before reading them.

	Returns a JSON array of objects with 'id', 'name', and 'mimeType'. Pass the 'id' to
	read_file to retrieve file contents.

	Args:
			query:     Filter by filename substring (case-insensitive). Empty string returns all files.
			folder_id: Scope to a specific subfolder ID (obtain from list_folders). Defaults to all target folders.
			recursive: If True, searches nested subfolders. Recommended when folder_id is set. Defaults to False.
			file_type: Filter by type — 'document', 'spreadsheet', 'pdf', 'image', or 'text'.

	Returns "No files found." if no files match the criteria.
	"""
	target_ids = [folder_id] if folder_id else _get_target_folder_ids()
	files = []
	for fid in target_ids:
		files.extend(_collect_files(fid, query, recursive=recursive, file_type=file_type))
	if not files:
		return "No files found."
	return json.dumps(files, ensure_ascii=False, indent=2)

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def list_folders(recursive: bool = False) -> str:
	"""
	List subfolders within the target Google Drive folders.

	Use this before list_files when you need to scope a search to a specific subfolder.
	Returns a JSON array of objects with 'id' and 'name'. Pass a folder 'id' to list_files
	as folder_id to narrow the search scope.

	Args:
			recursive: If True, includes nested subfolders. Defaults to False (top-level only).

	Returns "No folders found." if the target folders contain no subfolders.
	"""
	folders = []
	for folder_id in _get_target_folder_ids():
		folders.extend(_collect_folders(folder_id, recursive=recursive))
	if not folders:
		return "No folders found."
	return json.dumps(folders, ensure_ascii=False, indent=2)

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def read_file(file_id: str) -> str:
	"""
	Read and return the full text content of a file in the target Google Drive folder.

	Typical workflow: call list_files to find the file and obtain its 'id', then pass that id here.

	Supported formats:
		- Google Docs      → exported as plain text
		- Google Sheets    → exported as CSV
		- PDF              → text extracted via PyMuPDF
		- Plain text files → read directly

	Args:
			file_id: The Google Drive file ID (obtained from list_files).

	Raises ToolError if the file is outside the target folder (access denied) or if the
	file type is unsupported.
	"""
	if not _is_in_target_folder(file_id):
		raise ToolError(f"File '{file_id}' is not in the target folder. Access denied.")

	file_meta = _get_drive_service().files().get(fileId=file_id, fields="id, name, mimeType").execute()	
	return _read_file_content(file_id, file_meta.get("mimeType", ""))

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def search_content(query: str, file_type: str = "", recursive: bool = False, max_results: int = 10) -> str:
	"""
	Search for a keyword or phrase within the content of files in the target Google Drive folders.

	Unlike list_files (which filters by filename), this tool searches inside file contents and
	returns matching files with a surrounding context snippet.

	Typical workflow: use this to find which files mention a topic, then call read_file on
	specific files for the full content.

	Args:
			query:       The keyword or phrase to search for (case-insensitive).
			file_type:   Narrow the scope before searching — 'document', 'spreadsheet', 'pdf', or 'text'.
										Omit to search all supported types.
			recursive:   If True, searches nested subfolders. Defaults to False.
			max_results: Maximum number of matching files to return. Defaults to 10.

	Returns a JSON array of objects with 'id', 'name', 'mimeType', and 'snippet'.
	Returns "No matches found." if no files contain the query.

	Note: Reads each file sequentially; use file_type to narrow scope for faster results.
	"""
	READABLE_MIMES = {
		"application/vnd.google-apps.document",
		"application/vnd.google-apps.spreadsheet",
		"application/pdf",		
	}
	searchable_type = file_type if file_type in FILE_TYPE_MAP and file_type != "image" else ""

	candidates = []
	for fid in _get_target_folder_ids():
		candidates.extend(_collect_files(fid, "", recursive=recursive, file_type=searchable_type))

	candidates = [
		f for f in candidates
		if f["mimeType"] in READABLE_MIMES or f["mimeType"].startswith("text/")
	]

	results = []
	for f in candidates:
		if len(results) >= max_results:
			break
		try:
			content = _read_file_content(f["id"], f["mimeType"])
		except Exception:
			continue
		snippet = _extract_snippet(content, query)
		if snippet:
			results.append({"id": f["id"], "name": f["name"], "mimeType": f["mimeType"], "snippet": snippet})

	if not results:
		return "No matches found."
	return json.dumps(results, ensure_ascii=False, indent=2)

if __name__ == "__main__":
	mcp.run()
