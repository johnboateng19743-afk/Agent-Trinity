"""
Trinity Integrations — Google OAuth Authentication.
"""

import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class GoogleAuthManager:
    """Manages Google OAuth authentication flow."""

    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self, config: dict, credential_store=None):
        self.config = config
        self.credential_store = credential_store
        self.client_id = config["google"]["client_id"]
        self.client_secret = config["google"]["client_secret"]
        self.redirect_uri = config["google"]["redirect_uri"]
        self.credentials = None

        # Try to load existing credentials on init
        if self.credential_store and self.client_id:
            self._load_credentials()

    def _load_credentials(self):
        """Try to load stored credentials."""
        try:
            stored = self.credential_store.load("google_credentials")
            if stored:
                from google.oauth2.credentials import Credentials
                import json
                self.credentials = Credentials.from_authorized_user_info(json.loads(stored))
                logger.info("google_auth.credentials_loaded")
        except Exception as e:
            logger.debug("google_auth.no_stored_credentials", error=str(e))

    async def authenticate(self) -> bool:
        """Run the OAuth authentication flow."""
        if not self.client_id or not self.client_secret:
            logger.error("google_auth.missing_credentials")
            return False

        try:
            from google_auth_oauthlib.flow import InstalledAppFlow

            client_config = {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            }

            flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
            self.credentials = flow.run_local_server(
                port=self.config["advanced"]["local_http_port"],
                authorization_prompt_message="🔐 Opening browser to sign in to Google...",
            )

            # Store credentials securely
            if self.credential_store:
                self.credential_store.store("google_credentials", self.credentials.to_json())

            logger.info("google_auth.authenticated")
            return True

        except Exception as e:
            logger.error("google_auth.authentication_failed", error=str(e))
            return False

    def get_calendar_service(self):
        """Get an authenticated Google Calendar service."""
        return self._build_service("calendar", "v3")

    def get_gmail_service(self):
        """Get an authenticated Gmail service."""
        return self._build_service("gmail", "v1")

    def get_drive_service(self):
        """Get an authenticated Google Drive service."""
        return self._build_service("drive", "v3")

    def _build_service(self, api_name: str, version: str):
        """Build an authenticated Google API service."""
        if not self.credentials:
            logger.warning("google_auth.not_authenticated", api=api_name)
            return None

        # Refresh expired token
        if self.credentials.expired and self.credentials.refresh_token:
            try:
                from google.auth.transport.requests import Request
                self.credentials.refresh(Request())
                if self.credential_store:
                    self.credential_store.store("google_credentials", self.credentials.to_json())
            except Exception as e:
                logger.error("google_auth.refresh_failed", error=str(e))
                return None

        try:
            from googleapiclient.discovery import build
            service = build(api_name, version, credentials=self.credentials)
            logger.info("google_auth.service_created", api=api_name)
            return service
        except Exception as e:
            logger.error("google_auth.service_creation_failed", api=api_name, error=str(e))
            return None

    def is_authenticated(self) -> bool:
        """Check if Google is authenticated."""
        if not self.credentials:
            return False
        if self.credentials.expired and not self.credentials.refresh_token:
            return False
        return True
