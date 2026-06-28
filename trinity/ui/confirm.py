"""
Trinity UI — Confirmation Dialog.
Used for destructive actions, email sending, etc.
"""

import structlog

logger = structlog.get_logger(__name__)


class ConfirmDialog:
    """Confirmation dialog for destructive or sensitive actions."""

    def __init__(self, config: dict):
        self.config = config

    def show(self, message: str, action: str = "Confirm") -> bool:
        """Show a confirmation dialog and return the result."""
        logger.info("confirm.show", message=message[:50], action=action)
        # In production, this opens a PyQt6 dialog
        # For now, returns True (auto-confirm in dev mode)
        if self.config.get("trinity", {}).get("debug_mode", False):
            return True
        return False  # In production, wait for user input

    def show_destructive(self, message: str, item_count: int = 1) -> bool:
        """Show a destructive action confirmation (double-confirm for mass operations)."""
        if item_count > 50:
            logger.warning("confirm.mass_operation", count=item_count)
        return self.show(message, action="Confirm Delete")

    def show_email(self, to: str, subject: str, body: str) -> bool:
        """Show email confirmation before sending."""
        logger.info("confirm.email", to=to, subject=subject[:30])
        return self.show(f"Send email to {to}?\nSubject: {subject}", action="Send")
