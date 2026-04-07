from fastapi import APIRouter
from google_auth_oauthlib.flow import Flow
import os

router = APIRouter()

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

@router.get("/login")
def login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=os.getenv("REDIRECT_URI"),
    )

    auth_url, _ = flow.authorization_url(prompt="consent")
    return {"url": auth_url}