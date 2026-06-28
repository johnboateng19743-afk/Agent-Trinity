"""
Trinity UI — Voice Overlay.
Semi-transparent always-on-top overlay for voice status and responses.

Note: Full PyQt6 implementation requires a display. This module provides
the structure for when Trinity runs on a Windows desktop.
"""

import structlog

logger = structlog.get_logger(__name__)


class VoiceOverlay:
    """Voice overlay — shows Trinity's status and responses."""

    def __init__(self, config: dict):
        self.config = config
        self.visible = False

    def show_listening(self):
        """Show listening state."""
        self.visible = True
        logger.info("overlay.show_listening")

    def show_processing(self):
        """Show processing state."""
        logger.info("overlay.show_processing")

    def show_response(self, text: str):
        """Show Trinity's response."""
        logger.info("overlay.show_response", text=text[:50])

    def show_error(self, message: str):
        """Show an error message."""
        logger.info("overlay.show_error", message=message[:50])

    def hide(self):
        """Hide the overlay."""
        self.visible = False
        logger.info("overlay.hide")


class SystemTrayIcon:
    """System tray icon with status indicator."""

    def __init__(self, config: dict):
        self.config = config
        self.state = "idle"  # idle, listening, processing, error, muted

    def set_state(self, state: str):
        """Update the tray icon state."""
        self.state = state
        color_map = {
            "idle": "green",
            "listening": "green",
            "processing": "blue",
            "error": "red",
            "muted": "gray",
        }
        logger.info("tray.state_changed", state=state, color=color_map.get(state, "gray"))
