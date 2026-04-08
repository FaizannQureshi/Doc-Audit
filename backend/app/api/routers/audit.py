import os
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from googleapiclient.errors import HttpError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import AuthedContext, get_authed_context, get_db
from app.domain.audit_engine import run_folder_audit
from app.domain.standards import (
    EXPIRY_WARNING_DAYS,
    FOLDER_STRUCTURE_TEMPLATE,
    REQUIRED_DOCUMENT_TYPES,
)
from app.services.drive_service import folder_web_link, get_drive_service, list_files_recursive
from app.services.sheets_export import append_audit_row, create_audit_spreadsheet
from app.state import tokens
from app.models import AuditRun, Finding

router = APIRouter()


class FileItem(BaseModel):
    name: str


class FolderAuditRequest(BaseModel):
    folder_id: str = Field(..., description="Google Drive folder ID to scan recursively")
    client_name: str = Field(
        default="",
        description="Client or caregiver name for reports (defaults to folder id prefix)",
    )
    spreadsheet_id: str | None = Field(
        default=None,
        description="Existing Google Sheet ID to append rows to (or set AUDIT_SPREADSHEET_ID)",
    )
    create_sheet_if_missing: bool = Field(
        default=False,
        description="If no spreadsheet is configured, create a new Sheet and return its ID",
    )


def _require_creds():
    if tokens.drive_credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Connect Google Drive first (complete OAuth from /auth/login).",
        )
    return tokens.drive_credentials


@router.get("/standards")
def get_standards():
    """Naming rules, folder template, and required document types for operators and integrations."""
    return {
        "required_documents": [
            {
                "id": d.id,
                "label": d.label,
                "subfolder_hint": d.subfolder_hint,
                "validity_months_from_issue": d.validity_months_from_issue,
            }
            for d in REQUIRED_DOCUMENT_TYPES
        ],
        "folder_structure_template": FOLDER_STRUCTURE_TEMPLATE.strip(),
        "expiry_warning_days": EXPIRY_WARNING_DAYS,
    }


@router.post("/folder")
def audit_folder(
    body: FolderAuditRequest,
    ctx: AuthedContext = Depends(get_authed_context),
    db: Session = Depends(get_db),
):
    """
    Scan a Drive folder tree: missing / expired / expiring / mislabeled files,
    optional append to Google Sheets (Phase 1 audit log).
    """
    # Auth + tenancy (Phase 2): context is used to persist audit history.
    # NOTE: Drive creds are still process-local in Phase 1; Phase 2+ will persist
    # per-org connections in the DB.
    creds = _require_creds()
    service = get_drive_service(creds)
    try:
        files = list_files_recursive(service, body.folder_id)
    except HttpError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Drive API error: {e.reason or e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Drive listing failed: {e}",
        ) from e

    client = (body.client_name or "").strip() or f"Folder {body.folder_id[:10]}"
    folder_url = folder_web_link(body.folder_id)
    result = run_folder_audit(
        client_name=client,
        folder_id=body.folder_id,
        folder_url=folder_url,
        files=files,
    )

    # Persist the run + findings (Phase 2)
    run = AuditRun(
        org_id=ctx.org.id,
        user_id=ctx.user.id,
        client_name=result.client_name,
        folder_id=result.folder_id,
        folder_url=result.folder_url,
        status=result.status,
    )
    db.add(run)
    db.flush()

    def add_finding(ftype: str, severity: str, message: str, metadata: dict):
        db.add(
            Finding(
                audit_run_id=run.id,
                org_id=ctx.org.id,
                type=ftype,
                severity=severity,
                message=message,
                details=metadata,
            )
        )

    for m in result.missing_documents:
        add_finding("missing", "critical", f"Missing required document: {m}", {"document": m})
    for row in result.expired_documents:
        add_finding("expired", "critical", "Expired document detected", row)
    for row in result.expiring_soon:
        add_finding("expiring_soon", "warning", "Document expiring soon", row)
    for row in result.mislabeled_or_suspicious:
        add_finding("flag", "warning", "Naming/structure flag", row)

    sheet_url: str | None = None
    sheet_error: str | None = None
    new_spreadsheet_id: str | None = None

    spreadsheet_target = body.spreadsheet_id or os.getenv("AUDIT_SPREADSHEET_ID")

    if spreadsheet_target:
        try:
            append_audit_row(creds, spreadsheet_target.strip(), result)
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_target.strip()}"
        except HttpError as e:
            sheet_error = e.reason or str(e)
        except Exception as e:
            sheet_error = str(e)
    elif body.create_sheet_if_missing:
        try:
            new_spreadsheet_id = create_audit_spreadsheet(creds)
            append_audit_row(creds, new_spreadsheet_id, result)
            sheet_url = f"https://docs.google.com/spreadsheets/d/{new_spreadsheet_id}"
        except HttpError as e:
            sheet_error = e.reason or str(e)
        except Exception as e:
            sheet_error = str(e)

    return {
        "audit": asdict(result),
        "audit_run_id": run.id,
        "sheet_url": sheet_url,
        "sheet_error": sheet_error,
        "new_spreadsheet_id": new_spreadsheet_id,
    }


@router.post("/run")
def run_audit_sample(files: list[FileItem]):
    """Manual smoke test without Drive: pass file names only (no paths)."""
    fake: list[tuple[dict, str]] = []
    for f in files:
        fake.append(
            (
                {
                    "id": f"stub-{abs(hash(f.name)) % 10**9}",
                    "name": f.name,
                    "mimeType": "application/pdf",
                    "webViewLink": None,
                    "modifiedTime": None,
                },
                "",
            )
        )
    result = run_folder_audit(
        client_name="Sample (manual)",
        folder_id="manual",
        folder_url="",
        files=fake,
    )
    return asdict(result)


@router.get("/automation-notes")
def automation_notes():
    """
    How to move toward triggers and monitoring (not fully wired in Phase 1).
    """
    return {
        "repeatable_audit": "POST /audit/folder on a schedule (Cloud Scheduler, cron, GitHub Actions).",
        "drive_push": "Drive changes.watch + webhook requires HTTPS endpoint and domain verification; Pub/Sub is typical for production.",
        "file_added_trigger": "Use Google Apps Script on-folder onChange, or poll folder modifiedTime, or Workspace Events API where available.",
        "upcoming_expirations": "Response fields expiring_soon + expiry_warning_days in /audit/standards.",
    }
