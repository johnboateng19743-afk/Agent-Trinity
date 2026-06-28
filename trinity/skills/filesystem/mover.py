"""
Trinity Skill — File System Mover.
Moves, copies, and renames files and directories.
"""

import shutil
import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)


class FileSystemMover(BaseSkill):
    """Move, copy, and rename files and directories."""

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute move/copy/rename operation."""
        raw_text = entities.get("raw_text", "").lower()

        if "copy" in raw_text:
            return await self.copy(entities)
        if "rename" in raw_text:
            return await self.rename(entities)
        return await self.move(entities)

    async def move(self, entities: dict) -> SkillResult:
        """Move file or directory."""
        source_str = entities.get("from", entities.get("path", ""))
        dest_str = entities.get("to", entities.get("raw_text", ""))

        source = Path(self._resolve_path(source_str))
        dest = Path(self._resolve_path(dest_str))

        if not source.exists():
            return self._error(f"I couldn't find '{source_str}'.")

        # Ensure destination directory exists
        if dest.is_dir() or not dest.suffix:
            dest = dest / source.name

        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(source), str(dest))
            logger.info("filesystem.moved", src=str(source), dst=str(dest))
            return self._success(f"Moved {source.name} to {dest.parent}",
                                data={"action": "move", "from": str(source), "to": str(dest)})
        except Exception as e:
            return self._error(f"Error moving {source.name}: {str(e)}")

    async def copy(self, entities: dict) -> SkillResult:
        """Copy file or directory."""
        source_str = entities.get("from", entities.get("path", ""))
        dest_str = entities.get("to", entities.get("raw_text", ""))

        source = Path(self._resolve_path(source_str))
        dest = Path(self._resolve_path(dest_str))

        if not source.exists():
            return self._error(f"I couldn't find '{source_str}'.")

        try:
            if source.is_dir():
                shutil.copytree(str(source), str(dest / source.name))
            else:
                shutil.copy2(str(source), str(dest / source.name) if dest.is_dir() else str(dest))

            logger.info("filesystem.copied", src=str(source), dst=str(dest))
            return self._success(f"Copied {source.name} to {dest}",
                                data={"action": "copy", "from": str(source), "to": str(dest)})
        except Exception as e:
            return self._error(f"Error copying {source.name}: {str(e)}")

    async def rename(self, entities: dict) -> SkillResult:
        """Rename file or directory."""
        path_str = entities.get("path", "")
        new_name = entities.get("new_name", "")

        path = Path(self._resolve_path(path_str))
        new_path = path.parent / new_name

        if not path.exists():
            return self._error(f"I couldn't find '{path_str}'.")

        if new_path.exists():
            return self._error(f"'{new_name}' already exists in that location.")

        try:
            path.rename(new_path)
            logger.info("filesystem.renamed", old=str(path), new=str(new_path))
            return self._success(f"Renamed {path.name} to {new_name}",
                                data={"action": "rename", "old": str(path), "new": str(new_path)})
        except Exception as e:
            return self._error(f"Error renaming {path.name}: {str(e)}")
