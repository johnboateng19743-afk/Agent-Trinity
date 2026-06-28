"""
Trinity Tests — Integration Tests.
"""

import pytest
from trinity.integrations.credential_store import CredentialStore


class TestCredentialStore:
    """Tests for credential storage."""

    def test_store_and_load_interface(self):
        config = {}
        store = CredentialStore(config)
        # The interface should exist even if keyring is not available
        result = store.load("nonexistent_key")
        # Should return None for non-existent keys
        assert result is None


class TestGoogleAuth:
    """Tests for Google OAuth manager."""

    def test_is_authenticated_before_auth(self):
        from trinity.integrations.google_auth import GoogleAuthManager
        config = {
            "google": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "http://localhost:8400/auth/callback",
            },
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

    def test_missing_credentials(self):
        from trinity.integrations.google_auth import GoogleAuthManager
        config = {
            "google": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "http://localhost:8400/auth/callback",
            },
            "advanced": {"local_http_port": 8400},
        }
        auth = GoogleAuthManager(config)
        assert auth.client_id == ""
        assert auth.client_secret == ""
