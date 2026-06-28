"""
Trinity UI — First-Run Setup Wizard.
"""

import structlog

logger = structlog.get_logger(__name__)


class SetupWizard:
    """First-run setup wizard for Trinity."""

    def __init__(self, config: dict):
        self.config = config
        self.steps = [
            "welcome",
            "microphone_test",
            "speaker_test",
            "wake_word_calibration",
            "google_account",
            "location_permission",
            "default_folders",
            "privacy_settings",
            "complete",
        ]
        self.current_step = 0

    def start(self):
        """Start the setup wizard."""
        self.current_step = 0
        logger.info("setup_wizard.started")

    def next_step(self) -> str:
        """Move to the next step."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
        return self.steps[self.current_step]

    def current(self) -> str:
        """Get the current step name."""
        return self.steps[self.current_step]

    def complete(self):
        """Mark setup as complete."""
        self.current_step = len(self.steps) - 1
        logger.info("setup_wizard.completed")
