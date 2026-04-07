"""Google Drive listing with folder paths (for structure checks)."""

from __future__ import annotations

from typing import Any, Optional

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def get_drive_service(credentials: Credentials):
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def folder_web_link(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"


def list_files_recursive(
    service,
    root_folder_id: str,
    *,
    path_prefix: str = "",
) -> list[tuple[dict[str, Any], str]]:
    """
    Depth-first walk of all non-folder files under root_folder_id.
    Returns list of (file_metadata, relative_path) where path uses / separators.
    """
    out: list[tuple[dict[str, Any], str]] = []

    def walk(folder_id: str, rel_path: str) -> None:
        page_token: Optional[str] = None
        q = f"'{folder_id}' in parents and trashed = false"
        while True:
            resp = (
                service.files()
                .list(
                    q=q,
                    pageSize=100,
                    pageToken=page_token,
                    fields=(
                        "nextPageToken, files(id, name, mimeType, parents, "
                        "modifiedTime, webViewLink, shortcutDetails)"
                    ),
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            for f in resp.get("files", []):
                name = f.get("name") or ""
                mime = f.get("mimeType") or ""
                combined = "/".join(p for p in (rel_path, name) if p)
                if mime == "application/vnd.google-apps.folder":
                    walk(f["id"], combined)
                else:
                    out.append((f, combined))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

    walk(root_folder_id, path_prefix.strip("/"))
    return out
