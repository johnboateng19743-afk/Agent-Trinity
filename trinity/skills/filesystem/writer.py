"""
Trinity Skill — File System Writer.
Creates and edits files.
"""

import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)


class FileSystemWriter(BaseSkill):
    """Create new files and edit existing ones."""

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute write/edit operation."""
        raw_text = entities.get("raw_text", "")

        if any(kw in raw_text.lower() for kw in ["edit", "modify", "change", "update", "set", "rename"]):
            return await self.edit_file(entities)
        return await self.create_file(entities)

    async def create_file(self, entities: dict) -> SkillResult:
        """Create a new file with content."""
        path_str = entities.get("path", entities.get("raw_text", ""))
        content = entities.get("content", "")

        # If no content specified, create empty file
        path = Path(self._resolve_path(path_str))

        # If path ends with separator or no extension, create directory
        if not path.suffix and not content:
            return await self.create_dir(entities)

        if path.exists():
            return self._error(f"A file named '{path.name}' already exists. Overwrite, rename, or skip?")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info("filesystem.file_created", path=str(path))
            return self._success(f"Created {path.name} at {path.parent}",
                                data={"path": str(path), "action": "create"})
        except PermissionError:
            return self._error(f"I don't have permission to create a file there.")
        except Exception as e:
            return self._error(f"Error creating file: {str(e)}")

    async def create_dir(self, entities: dict) -> SkillResult:
        """Create a new directory."""
        path_str = entities.get("path", entities.get("raw_text", ""))
        path = Path(self._resolve_path(path_str))

        if path.exists():
            return self._error(f"'{path.name}' already exists.")

        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info("filesystem.dir_created", path=str(path))
            return self._success(f"Created folder '{path.name}' at {path.parent}",
                                data={"path": str(path), "action": "create_dir"})
        except PermissionError:
            return self._error(f"I don't have permission to create a folder there.")
        except Exception as e:
            return self._error(f"Error creating folder: {str(e)}")

    async def edit_file(self, entities: dict) -> SkillResult:
        """Edit an existing file (find and replace)."""
        path_str = entities.get("path", entities.get("raw_text", ""))
        find_text = entities.get("find", "")
        replace_text = entities.get("replace", "")

        path = Path(self._resolve_path(path_str))

        if not path.exists():
            found = await self._find_file(path_str)
            if found:
                path = Path(found)
            else:
                return self._error(f"I couldn't find '{path_str}' to edit.")

        if not path.is_file():
            return self._error(f"'{path.name}' is not a file.")

        try:
            # Create backup
            backup_path = path.with_suffix(path.suffix + ".trinity-backup")
            import shutil
            shutil.copy2(str(path), str(backup_path))

            # Read current content
            content = path.read_text(encoding="utf-8", errors="replace")

            if find_text:
                # Find and replace
                if find_text not in content:
                    return self._error(f"Couldn't find '{find_text}' in {path.name}.")

                new_content = content.replace(find_text, replace_text)

                # Show diff
                diff = self._simple_diff(content, new_content)
                logger.info("filesystem.file_edited", path=str(path))

                # Write new content
                path.write_text(new_content, encoding="utf-8")
                return self._success(
                    f"Updated {path.name}:\n{diff}\nBackup saved as {backup_path.name}",
                    data={"path": str(path), "action": "edit", "backup": str(backup_path)}
                )
            else:
                return self._error("What should I change? Please specify what to find and replace.")

        except PermissionError:
            return self._error(f"I don't have permission to edit '{path.name}'.")
        except Exception as e:
            # Restore from backup
            if backup_path.exists():
                shutil.copy2(str(backup_path), str(path))
            return self._error(f"Error editing file: {str(e)}. Original file restored from backup.")

    async def _find_file(self, name: str) -> str | None:
        """Find file by name in common directories."""
        search_dirs = [Path.home() / "Desktop", Path.home() / "Documents", Path.home() / "Downloads"]
        for d in search_dirs:
            if not d.exists():
                continue
            for item in d.iterdir():
                if name.lower() in item.name.lower():
                    return str(item)
        return None

    @staticmethod
    def _simple_diff(old: str, new: str) -> str:
        """Simple diff showing what changed."""
        old_lines = old.splitlines()
        new_lines = new.splitlines()

        diff_lines = []
        for i, (old_line, new_line) in enumerate(zip(old_lines, new_lines)):
            if old_line != new_line:
                diff_lines.append(f"  Line {i+1}:")
                diff_lines.append(f"    - {old_line.strip()}")
                diff_lines.append(f"    + {new_line.strip()}")

        return "\n".join(diff_lines[:20]) if diff_lines else "No changes detected."
