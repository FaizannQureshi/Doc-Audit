"""
Drive file audit: missing docs, expiry, mislabels, expiring soon.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from app.standards import (
    EXPIRY_WARNING_DAYS,
    REQUIRED_DOCUMENT_TYPES,
    DocumentType,
    COMPILED,
)


_DATE_PATTERNS = [
    re.compile(r"(?:20\d{2}|19\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])"),
    re.compile(r"(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](20\d{2}|19\d{2})"),
]
_EXPIRY_HINT = re.compile(
    r"(?:^|[_\s-])(?:exp|expiry|expires?)(?:[_\s-]|$)", re.I
)
_ISSUE_HINT = re.compile(
    r"(?:^|[_\s-])(?:issued?|issue)(?:[_\s-]|$)", re.I
)


@dataclass
class ClassifiedFile:
    drive_id: str
    name: str
    mime_type: str
    path: str
    web_link: Optional[str]
    modified_time: Optional[str]
    matched_type_ids: list[str] = field(default_factory=list)
    primary_type_id: Optional[str] = None
    explicit_expiry: Optional[date] = None
    issue_date: Optional[date] = None
    inferred_expiry: Optional[date] = None


@dataclass
class AuditResult:
    client_name: str
    folder_id: str
    folder_url: str
    status: str  # Complete | Incomplete
    missing_documents: list[str]
    expired_documents: list[dict[str, Any]]
    expiring_soon: list[dict[str, Any]]
    mislabeled_or_suspicious: list[dict[str, Any]]
    classified_files: list[dict[str, Any]]
    scanned_at: str
    standards_version: str = "1.0"


def _parse_dates_in_name(name: str) -> list[date]:
    base = name.rsplit(".", 1)[0]
    found: list[date] = []
    for pat in _DATE_PATTERNS:
        for m in pat.finditer(base):
            try:
                g = m.group(0).replace("/", "-")
                parts = re.split(r"[-/]", g)
                if len(parts) != 3:
                    continue
                if len(parts[0]) == 4:
                    y, mo, d = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    # Assume MM-DD-YYYY when first part <= 12
                    mo, d, y = int(parts[0]), int(parts[1]), int(parts[2])
                found.append(date(y, mo, d))
            except (ValueError, IndexError):
                continue
    return found


def _classify_name(name: str) -> list[str]:
    lower = name.lower()
    matched: list[str] = []
    for dt in REQUIRED_DOCUMENT_TYPES:
        for rx in COMPILED[dt.id]:
            if rx.search(lower):
                matched.append(dt.id)
                break
    return matched


def _norm_segment(seg: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", seg.lower()).strip("_")


def _folder_structure_flag(
    path: str, doc_type: DocumentType
) -> Optional[str]:
    if not doc_type.subfolder_hint:
        return None
    parts = [_norm_segment(p) for p in path.split("/") if p.strip()]
    hint = doc_type.subfolder_hint.lower()
    if any(hint in p or p.startswith(hint) for p in parts):
        return None
    return (
        f'"{doc_type.label}" is usually filed under folder containing '
        f'"{doc_type.subfolder_hint}"; file path: {path or "(root)"}'
    )


def _infer_expiry(
    name: str,
    doc_type: Optional[DocumentType],
    dates: list[date],
    today: date,
) -> tuple[Optional[date], Optional[date], Optional[date]]:
    """Returns explicit_expiry, issue_date, inferred_expiry."""
    base = name.rsplit(".", 1)[0]
    explicit: Optional[date] = None
    issue: Optional[date] = None

    if dates:
        if _EXPIRY_HINT.search(base):
            explicit = max(dates) if dates else None
        elif _ISSUE_HINT.search(base):
            issue = min(dates)
        elif len(dates) == 1:
            if doc_type and doc_type.validity_months_from_issue:
                issue = dates[0]
            else:
                explicit = dates[0]
        else:
            explicit = max(dates)

    inferred: Optional[date] = None
    if issue and doc_type and doc_type.validity_months_from_issue:
        approx = issue + timedelta(days=int(doc_type.validity_months_from_issue * 30.4375))
        inferred = approx

    if explicit is None and inferred is not None:
        explicit = inferred

    return explicit, issue, inferred


def classify_drive_file(
    file_row: dict[str, Any],
    path: str,
) -> ClassifiedFile:
    name = file_row.get("name") or ""
    fid = file_row.get("id") or ""
    mime = file_row.get("mimeType") or ""
    modified = file_row.get("modifiedTime")
    web_link = file_row.get("webViewLink")

    matched = _classify_name(name)
    primary: Optional[str] = None
    if len(matched) == 1:
        primary = matched[0]
    elif len(matched) > 1:
        primary = matched[0]

    dates = _parse_dates_in_name(name)
    doc_type_obj = next(
        (d for d in REQUIRED_DOCUMENT_TYPES if d.id == (primary or "")),
        None,
    )
    exp, iss, inf = _infer_expiry(name, doc_type_obj, dates, date.today())

    return ClassifiedFile(
        drive_id=fid,
        name=name,
        mime_type=mime,
        path=path,
        web_link=web_link,
        modified_time=modified,
        matched_type_ids=matched,
        primary_type_id=primary,
        explicit_expiry=exp,
        issue_date=iss,
        inferred_expiry=inf,
    )


def run_folder_audit(
    *,
    client_name: str,
    folder_id: str,
    folder_url: str,
    files: list[tuple[dict[str, Any], str]],
) -> AuditResult:
    today = datetime.now(timezone.utc).date()
    warn_before = today + timedelta(days=EXPIRY_WARNING_DAYS)

    classified: list[ClassifiedFile] = []
    for file_row, path in files:
        classified.append(classify_drive_file(file_row, path))

    by_type: dict[str, ClassifiedFile] = {}
    for cf in classified:
        if cf.primary_type_id and cf.primary_type_id not in by_type:
            by_type[cf.primary_type_id] = cf

    missing: list[str] = []
    for dt in REQUIRED_DOCUMENT_TYPES:
        if dt.id not in by_type:
            missing.append(dt.label)

    expired: list[dict[str, Any]] = []
    expiring: list[dict[str, Any]] = []
    mislabeled: list[dict[str, Any]] = []

    for cf in classified:
        dt_obj = next(
            (d for d in REQUIRED_DOCUMENT_TYPES if d.id == cf.primary_type_id),
            None,
        )
        exp_date = cf.explicit_expiry or cf.inferred_expiry

        if len(cf.matched_type_ids) > 1:
            mislabeled.append(
                {
                    "file": cf.name,
                    "drive_id": cf.drive_id,
                    "path": cf.path,
                    "reason": "Filename matches multiple document categories; rename using one primary type keyword.",
                    "matched": cf.matched_type_ids,
                }
            )

        if dt_obj:
            struct_msg = _folder_structure_flag(cf.path, dt_obj)
            if struct_msg:
                mislabeled.append(
                    {
                        "file": cf.name,
                        "drive_id": cf.drive_id,
                        "path": cf.path,
                        "reason": struct_msg,
                        "matched": [dt_obj.id],
                    }
                )

        if cf.mime_type and "shortcut" in cf.mime_type.lower():
            mislabeled.append(
                {
                    "file": cf.name,
                    "drive_id": cf.drive_id,
                    "path": cf.path,
                    "reason": "Shortcut — verify target document is stored, not only linked.",
                    "matched": cf.matched_type_ids,
                }
            )

        if exp_date:
            if exp_date < today:
                expired.append(
                    {
                        "document": dt_obj.label if dt_obj else cf.primary_type_id or "Unknown",
                        "file": cf.name,
                        "expiry_date": exp_date.isoformat(),
                        "drive_id": cf.drive_id,
                        "path": cf.path,
                    }
                )
            elif exp_date <= warn_before:
                expiring.append(
                    {
                        "document": dt_obj.label if dt_obj else cf.primary_type_id or "Unknown",
                        "file": cf.name,
                        "expiry_date": exp_date.isoformat(),
                        "days_remaining": (exp_date - today).days,
                        "drive_id": cf.drive_id,
                        "path": cf.path,
                    }
                )

    status = (
        "Complete"
        if not missing and not expired and not mislabeled
        else "Incomplete"
    )

    scanned = datetime.now(timezone.utc).isoformat()

    return AuditResult(
        client_name=client_name,
        folder_id=folder_id,
        folder_url=folder_url,
        status=status,
        missing_documents=missing,
        expired_documents=expired,
        expiring_soon=expiring,
        mislabeled_or_suspicious=mislabeled,
        classified_files=[
            {
                "name": c.name,
                "path": c.path,
                "primary_type_id": c.primary_type_id,
                "matched_type_ids": c.matched_type_ids,
                "expiry": (
                    (c.explicit_expiry or c.inferred_expiry).isoformat()
                    if (c.explicit_expiry or c.inferred_expiry)
                    else None
                ),
                "drive_id": c.drive_id,
                "web_link": c.web_link,
            }
            for c in classified
        ],
        scanned_at=scanned,
    )
