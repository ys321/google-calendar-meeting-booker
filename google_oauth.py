from __future__ import annotations

import os
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_OAUTH_TOKEN_FILE,
)

# Scopes: Calendar + Meet conferences
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.events.readonly",
]

def _client_config():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI):
        raise ValueError(
            "Google OAuth env vars missing. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI."
        )
    return {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

def create_flow(state: Optional[str] = None) -> Flow:
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    if state:
        flow.state = state
    return flow

def save_credentials(creds: Credentials) -> None:
    os.makedirs(os.path.dirname(GOOGLE_OAUTH_TOKEN_FILE), exist_ok=True)
    with open(GOOGLE_OAUTH_TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

def load_credentials() -> Optional[Credentials]:
    if not os.path.exists(GOOGLE_OAUTH_TOKEN_FILE):
        return None
    creds = Credentials.from_authorized_user_file(
        GOOGLE_OAUTH_TOKEN_FILE, scopes=SCOPES
    )
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)
    return creds
