"""
Trinity Skill — File System Searcher.
Search for files by name, type, content, date, or size.
"""

import os
import structlog
from pathlib import Path
from datetime import datetime, timedelta
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)


class FileSystemSearcher(BaseSkill):
    """Search for files and directories."""

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute search operation."""
        raw_text = entities.get("raw_text", "")

        # Parse search criteria from entities
        query = entities.get("raw_text", "")
        file_type = entities.get("type", None)
        date_filter = entities.get("date", None)

        # Search in common directories
        search_dirs = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Pictures",
            Path.home() / "Music",
            Path.home() / "Videos",
            Path.home(),
        ]

        results = []
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            found = await self._search_directory(search_dir, query, file_type, date_filter)
            results.extend(found)

            if len(results) > 100:  # Cap results
                break

        if not results:
            return self._success(f"No files found matching '{query}'.")

        # Format results
        result_lines = []
        for path, size, modified in results[:50]:
            icon = "📁" if path.is_dir() else "📄"
            result_lines.append(f"{icon} {path} ({self._format_size(size)}) — {modified}")

        header = f"Found {len(results)} result{'s' if len(results) > 1 else ''}:\n\n"
        content = header + "\n".join(result_lines)

        if len(results) > 50:
            content += f"\n\n... and {len(results) - 50} more"

        return self._success(content, data={"results": [str(r[0]) for r in results]})

    async def _search_directory(self, directory: Path, query: str,
                                 file_type: str | None = None,
                                 date_filter: str | None = None) -> list[tuple]:
        """Search a directory for matching files."""
        results = []
        query_lower = query.lower()

        # Determine date threshold
        date_threshold = None
        if date_filter:
            date_threshold = self._parse_date_filter(date_filter)

        try:
            for item in directory.rglob("*"):
                try:
                    # Name match
                    if query_lower and query_lower not in item.name.lower():
                        # Also check content for text files
                        if item.is_file() and item.suffix in (".txt", ".md", ".py", ".js", ".csv", ".json"):
                            try:
                                if query_lower not in item.read_text(encoding="utf-8", errors="replace")[:10000].lower():
                                    continue
                            except Exception:
                                continue
                        else:
                            continue

                    # Type filter
                    if file_type:
                        if not self._matches_type(item, file_type):
                            continue

                    # Date filter
                    if date_threshold:
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        if mtime < date_threshold:
                            continue

                    results.append((item, item.stat().st_size,
                                   datetime.fromtimestamp(item.stat().st_mtime).strftime("%b %d")))

                except (PermissionError, OSError):
                    continue

        except Exception as e:
            logger.error("search.error", directory=str(directory), error=str(e))

        return results

    @staticmethod
    def _matches_type(path: Path, file_type: str) -> bool:
        """Check if a file matches a type filter."""
        type_map = {
            "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"},
            "photo": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"},
            "video": {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"},
            "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
            "music": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
            "document": {".docx", ".doc", ".pdf", ".txt", ".md", ".rtf"},
            "pdf": {".pdf"},
            "spreadsheet": {".xlsx", ".xls", ".csv"},
            "code": {".py", ".js", ".ts", ".html", ".css", ".java", ".cpp"},
        }

        ft = file_type.lower()
        if ft in type_map:
            return path.suffix.lower() in type_map[ft]
        return path.suffix.lower() == f".{ft}"

    @staticmethod
    def _parse_date_filter(date_str: str) -> datetime | None:
        """Parse a date filter string into a datetime threshold."""
        now = datetime.now()
        lower = date_str.lower().strip()

        if "last week" in lower or ">7days" in lower:
            return now - timedelta(days=7)
        if "last month" in lower or ">30days" in lower:
            return now - timedelta(days=30)
        if "today" in lower:
            return now.replace(hour=0, minute=0, second=0)
        if "yesterday" in lower:
            return now - timedelta(days=1)

        return None

    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
