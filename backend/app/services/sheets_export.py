"""Append audit rows to Google Sheets (Phase 1 reporting surface)."""

from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from app.domain.audit_engine import AuditResult


def get_sheets_service(credentials: Credentials):
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def ensure_header_row(service, spreadsheet_id: str, sheet_name: str = "Audit_Log") -> None:
    """Create sheet tab if missing and write header row once."""
    meta = (
        service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties")
        .execute()
    )
    titles = {
        s["properties"]["title"]
        for s in meta.get("sheets", [])
        if s.get("properties", {}).get("title")
    }
    if sheet_name not in titles:
        body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {"frozenRowCount": 1},
                        }
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()

    range_a1 = f"'{sheet_name}'!A1:H1"
    existing = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_a1)
        .execute()
    )
    if not existing.get("values"):
        header = [
            [
                "Scanned At (UTC)",
                "Client / Caregiver",
                "Folder Link",
                "Missing Documents",
                "Expired Documents",
                "Expiring Soon",
                "Mislabeled / Flags",
                "Status",
            ]
        ]
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_a1,
            valueInputOption="RAW",
            body={"values": header},
        ).execute()


def append_audit_row(
    credentials: Credentials,
    spreadsheet_id: str,
    result: AuditResult,
) -> dict[str, Any]:
    service = get_sheets_service(credentials)
    sheet_name = "Audit_Log"
    ensure_header_row(service, spreadsheet_id, sheet_name)

    def summarize(items: list[dict[str, Any]], key: str) -> str:
        if not items:
            return ""
        parts = []
        for it in items[:12]:
            parts.append(it.get(key) or it.get("document") or str(it))
        extra = len(items) - 12
        s = "; ".join(parts)
        if extra > 0:
            s += f" … (+{extra} more)"
        return s

    missing = ", ".join(result.missing_documents) if result.missing_documents else ""
    expired = summarize(result.expired_documents, "file")
    soon = summarize(result.expiring_soon, "file")
    flags = summarize(result.mislabeled_or_suspicious, "file")

    row = [
        [
            result.scanned_at,
            result.client_name,
            result.folder_url,
            missing,
            expired,
            soon,
            flags,
            result.status,
        ]
    ]

    range_a1 = f"'{sheet_name}'!A:H"
    return (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_a1,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": row},
        )
        .execute()
    )


def create_audit_spreadsheet(
    credentials: Credentials, title: str = "Document Audit Log"
) -> str:
    service = get_sheets_service(credentials)
    body = {
        "properties": {"title": title},
        "sheets": [{"properties": {"title": "Audit_Log"}}],
    }
    created = (
        service.spreadsheets()
        .create(body=body, fields="spreadsheetId,spreadsheetUrl")
        .execute()
    )
    sid = created["spreadsheetId"]
    ensure_header_row(service, sid, "Audit_Log")
    return sid
