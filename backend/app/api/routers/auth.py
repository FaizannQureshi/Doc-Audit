import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from app.state import tokens

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]


def _client_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in environment.",
        )
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _flow():
    redirect_uri = os.getenv("REDIRECT_URI")
    if not redirect_uri:
        raise HTTPException(
            status_code=500,
            detail="Missing REDIRECT_URI in environment.",
        )
    # PKCE verifier is generated per Flow instance; /login and /callback use
    # separate instances, so PKCE breaks unless we persist the verifier. For a
    # confidential "web" client we use client_secret at the token endpoint instead.
    return Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=False,
    )


@router.get("/login")
def login():
    flow = _flow()
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return {"url": auth_url}


@router.get("/callback")
def oauth_callback(code: str):
    flow = _flow()
    flow.fetch_token(code=code)
    tokens.drive_credentials = flow.credentials
    frontend = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    return RedirectResponse(url=f"{frontend}/dashboard")
