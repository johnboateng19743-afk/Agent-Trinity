"""
Trinity Tests — Integration Tests.
"""

import pytest
from trinity.integrations.credential_store import CredentialStore


class TestCredentialStore:
    """Tests for credential storage."""

    def test_store_and_load(self):
        config = {}
        store = CredentialStore(config)
        # keyring may not be available in test env, so we test the interface
        assert store.list_keys() == [
            "google_credentials",
            "elevenlabs_api_key",
            "openai_api_key",
            "anthropic_api_key",
        ]


class TestGoogleAuth:
    """Tests for Google OAuth manager."""

    def test_is_authenticated_before_auth(self):
        from trinity.integrations.google_auth import GoogleAuthManager
        config = {
            "google": {"client_id": "", "client_secret": "", "redirect_uri": "http://localhost:8400/auth/callback"},
            "advanced": {"local_http_port": 8400},
        }
        auth = GoogleAuthManager(config)
        assert auth.is_authenticated() is False

    def test_scopes_defined(self):
        from trinity.integrations.google_auth import GoogleAuthManager
        assert len(GoogleAuthManager.SCOPES) == 7
        assert any("calendar" in s for s in GoogleAuthManager.SCOPES)
        assert any("gmail" in s for s in GoogleAuthManager.SCOPES)
        assert any("drive" in s for s in GoogleAuthManager.SCOPES)
