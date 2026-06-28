"""
Trinity Skill — Application Launcher.
"""

import subprocess
import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)


class ApplicationLauncher(BaseSkill):
    """Launch applications and games by voice."""

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute application launch."""
        raw_text = entities.get("raw_text", "")
        return self._confirm(f"Launch application: {raw_text}?")

    async def launch_steam_game(self, game_name: str) -> SkillResult:
        """Launch a Steam game."""
        # Steam URI: steam://rungameid/<appid>
        try:
            subprocess.Popen(["steam://rungameid/" + game_name], shell=True)
            return self._success(f"Launching {game_name}...")
        except Exception as e:
            return self._error(f"Error launching game: {str(e)}")

    async def launch_app(self, app_name: str) -> SkillResult:
        """Launch a Windows application."""
        try:
            # Try common locations
            subprocess.Popen(["cmd", "/c", "start", "", app_name])
            return self._success(f"Opening {app_name}...")
        except Exception as e:
            return self._error(f"Error opening {app_name}: {str(e)}")
