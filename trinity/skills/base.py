"""
Trinity Skills — Base Skill class.
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SkillResult:
    """Result from a skill execution."""
    success: bool
    response: str
    data: dict | None = None
    requires_confirmation: bool = False
    confirmation_message: str = ""


class BaseSkill(ABC):
    """Base class for all Trinity skills."""

    def __init__(self, config: dict):
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute the skill with the given entities."""
        pass

    def _confirm(self, message: str) -> SkillResult:
        """Return a result that requires confirmation."""
        return SkillResult(
            success=False,
            response="",
            requires_confirmation=True,
            confirmation_message=message,
        )

    def _success(self, response: str, data: dict | None = None) -> SkillResult:
        """Return a successful result."""
        return SkillResult(success=True, response=response, data=data)

    def _error(self, message: str) -> SkillResult:
        """Return an error result."""
        return SkillResult(success=False, response=message)

    def _resolve_path(self, path_str: str) -> str:
        """Resolve a path string to an absolute path."""
        from pathlib import Path
        path = Path(path_str).expanduser()

        # Handle common aliases
        aliases = {
            "desktop": Path.home() / "Desktop",
            "documents": Path.home() / "Documents",
            "downloads": Path.home() / "Downloads",
            "pictures": Path.home() / "Pictures",
            "music": Path.home() / "Music",
            "videos": Path.home() / "Videos",
            "home": Path.home(),
        }

        lower = path_str.lower().strip()
        if lower in aliases:
            return str(aliases[lower])

        if not path.is_absolute():
            path = Path.home() / path

        return str(path)
