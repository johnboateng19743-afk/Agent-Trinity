"""
Trinity Skill — File System Deleter.
Deletes files and directories (to Recycle Bin, not permanent delete).
"""

import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)

BATCH_CONFIRM_THRESHOLD = 10  # Confirm if deleting more than this many files
SIZE_CONFIRM_THRESHOLD = 500 * 1024 * 1024  # 500MB


class FileSystemDeleter(BaseSkill):
    """Delete files and directories to Recycle Bin."""

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute delete operation."""
        path_str = entities.get("path", entities.get("raw_text", ""))
        path = Path(self._resolve_path(path_str))

        if not path.exists():
            return self._error(f"I couldn't find '{path_str}'.")

        # Check if this is a batch operation
        if path.is_dir():
            items = list(path.iterdir())
            if len(items) > BATCH_CONFIRM_THRESHOLD:
                return self._confirm(
                    f"You're about to delete {len(items)} items from {path.name}. "
                    "Files will go to the Recycle Bin. Are you sure?"
                )

        # Check size
        total_size = self._get_total_size(path)
        if total_size > SIZE_CONFIRM_THRESHOLD:
            return self._confirm(
                f"This will delete {self._format_size(total_size)}. "
                "Files will go to the Recycle Bin. Are you sure?"
            )

        return await self._delete(path)

    async def _delete(self, path: Path) -> SkillResult:
        """Move file/directory to Recycle Bin."""
        try:
            from send2trash import send2trash
            send2trash(str(path))
            logger.info("filesystem.deleted", path=str(path), method="recycle_bin")
            return self._success(
                f"Moved {path.name} to the Recycle Bin. You can say 'undo' within 60 seconds to restore it.",
                data={"action": "delete", "path": str(path)}
            )
        except ImportError:
            logger.warning("filesystem.send2trash_not_available")
            return self._confirm(
                f"send2trash is not installed. Permanent delete of {path.name}? "
                "This cannot be undone! Install send2trash with: pip install send2trash"
            )
        except Exception as e:
            return self._error(f"Error deleting {path.name}: {str(e)}")

    @staticmethod
    def _get_total_size(path: Path) -> int:
        """Calculate total size of file or directory."""
        if path.is_file():
            return path.stat().st_size
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        except Exception:
            pass
        return total

    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
