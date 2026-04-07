from fastapi import APIRouter, HTTPException
from googleapiclient.discovery import build

from app.state import tokens

router = APIRouter()


@router.get("/files")
def list_files():
    if tokens.drive_credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Connect Google Drive first (complete OAuth from /auth/login).",
        )
    service = build("drive", "v3", credentials=tokens.drive_credentials)

    results = (
        service.files()
        .list(pageSize=20, fields="files(id, name)")
        .execute()
    )

    return results.get("files", [])
