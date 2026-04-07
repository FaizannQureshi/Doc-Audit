"""
Compliance-oriented document taxonomy, folder layout, and naming rules.

These definitions are the single source of truth for deterministic classification
(AI can use the same labels and patterns). Adjust per program/jurisdiction.
"""

from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class DocumentType:
    """A required document category with matching and validity rules."""

    id: str
    label: str
    # Regex patterns matched against lowercased filename (basename only).
    filename_patterns: tuple[str, ...]
    # If a date is parsed as *issue* date, add this many months for soft expiry.
    # None = do not infer expiry from issue date alone (still allow explicit exp. in name).
    validity_months_from_issue: Optional[int] = None
    # Expected folder segment (case-insensitive) for structure checks; None = any.
    subfolder_hint: Optional[str] = None


# Default program requirements — customize per deployment.
REQUIRED_DOCUMENT_TYPES: tuple[DocumentType, ...] = (
    DocumentType(
        id="passport",
        label="Passport",
        filename_patterns=(
            r"passport",
            r"travel[\s_-]*doc",
            r"\b(id|identity)[\s_-]*(card|document)\b",
        ),
        validity_months_from_issue=120,
        subfolder_hint="01_identity",
    ),
    DocumentType(
        id="police_clearance",
        label="Police Clearance",
        filename_patterns=(
            r"police",
            r"criminal[\s_-]*record",
            r"background[\s_-]*check",
            r"clearance",
        ),
        validity_months_from_issue=None,
        subfolder_hint="02_background",
    ),
    DocumentType(
        id="medical",
        label="Medical",
        filename_patterns=(
            r"medical",
            r"health",
            r"tb[\s_-]*(test|screen)",
            r"immunization",
            r"vaccin",
        ),
        validity_months_from_issue=12,
        subfolder_hint="03_health",
    ),
)

# Warn when expiry falls within this many days (automation / monitoring).
EXPIRY_WARNING_DAYS = 90

# Folder template for operators and AI prompts (not enforced mechanically beyond hints).
FOLDER_STRUCTURE_TEMPLATE = """
Recommended client folder layout (customize labels to your org):

  {client_name}/
    01_Identity/          — Passport, national ID, visa
    02_Background/        — Police / criminal background checks
    03_Health/            — Medical exams, immunizations, TB tests
    04_Employment/        — Optional: contracts, references
    _Audit_Log/           — Optional: exported audit snapshots

Naming convention (machine-friendly):
  <DocType>_<OptionalStatus>_YYYY-MM-DD_<free-text>.pdf
  Examples:
    Passport_active_2030-01-15.pdf
    Police_clearance_issued_2024-06-01.pdf
    Medical_exam_exp_2026-03-01.pdf

Explicit expiry or issue markers (any of): exp, expiry, expires, issued, issue
Dates: YYYY-MM-DD preferred; also accepted MM-DD-YYYY, DD-MM-YYYY (ambiguous months 1-12 only).
"""


def compiled_patterns() -> dict[str, list[re.Pattern[str]]]:
    out: dict[str, list[re.Pattern[str]]] = {}
    for dt in REQUIRED_DOCUMENT_TYPES:
        out[dt.id] = [re.compile(p, re.I) for p in dt.filename_patterns]
    return out


COMPILED = compiled_patterns()
