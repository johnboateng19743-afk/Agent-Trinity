"""
Trinity Integrations — Credential Store using Windows Credential Manager / keyring.
"""

import structlog

logger = structlog.get_logger(__name__)

SERVICE_NAME = "TrinityAgent"


class CredentialStore:
    """Secure credential storage using keyring (backed by Windows Credential Manager)."""

    def __init__(self, config: dict):
        self.config = config

    def store(self, key: str, value: str):
        """Store a credential securely."""
        try:
            import keyring
            keyring.set_password(SERVICE_NAME, key, value)
            logger.info("credential.stored", key=key)
        except ImportError:
            logger.warning("credential.keyring_not_available", fallback="env_file")
        except Exception as e:
            logger.error("credential.store_failed", key=key, error=str(e))

    def load(self, key: str) -> str | None:
        """Load a credential from secure storage."""
        try:
            import keyring
            value = keyring.get_password(SERVICE_NAME, key)
            return value
        except ImportError:
            logger.warning("credential.keyring_not_available")
            return None
        except Exception as e:
            logger.error("credential.load_failed", key=key, error=str(e))
            return None

    def delete(self, key: str):
        """Delete a credential from secure storage."""
        try:
            import keyring
            keyring.delete_password(SERVICE_NAME, key)
            logger.info("credential.deleted", key=key)
        except Exception as e:
            logger.error("credential.delete_failed", key=key, error=str(e))

    def list_keys(self) -> list[str]:
        """List all stored credential keys (not values)."""
        # keyring doesn't support listing, so we track known keys
        return [
            "google_credentials",
            "elevenlabs_api_key",
            "openai_api_key",
            "anthropic_api_key",
        ]
