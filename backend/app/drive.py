from fastapi import APIRouter
from googleapiclient.discovery import build

router = APIRouter()

# TEMP: replace with real token storage later
ACCESS_TOKEN = None

@router.get("/files")
def list_files():
    service = build("drive", "v3", developerKey=ACCESS_TOKEN)

    results = service.files().list(
        pageSize=20,
        fields="files(id, name)"
    ).execute()

    return results.get("files", [])