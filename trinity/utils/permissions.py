"""
Permission tier checking for Trinity actions.
"""

from enum import IntEnum
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class PermissionTier(IntEnum):
    """Permission tiers — higher = more dangerous."""
    TRUSTED = 0       # Non-destructive reads
    STANDARD = 1      # Non-destructive writes
    DESTRUCTIVE = 2   # Irreversible actions
    SENSITIVE = 3     # External communication
    CRITICAL = 4      # System-level changes


# Paths that require explicit confirmation even for reads
PROTECTED_PATHS = [
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/ProgramData"),
]

# Size threshold for batch operation confirmation (500 MB)
BATCH_SIZE_THRESHOLD = 500 * 1024 * 1024


def classify_operation(operation: str) -> PermissionTier:
    """Classify an operation into a permission tier."""
    tier_map = {
        "read_file": PermissionTier.TRUSTED,
        "list_dir": PermissionTier.TRUSTED,
        "search_files": PermissionTier.TRUSTED,
        "create_file": PermissionTier.STANDARD,
        "create_dir": PermissionTier.STANDARD,
        "edit_file": PermissionTier.STANDARD,
        "move": PermissionTier.STANDARD,
        "copy": PermissionTier.STANDARD,
        "rename": PermissionTier.STANDARD,
        "delete": PermissionTier.DESTRUCTIVE,
        "execute": PermissionTier.CRITICAL,
        "send_email": PermissionTier.SENSITIVE,
        "share_file": PermissionTier.SENSITIVE,
    }
    return tier_map.get(operation, PermissionTier.STANDARD)


def is_protected_path(path: Path) -> bool:
    """Check if a path is in a protected directory."""
    try:
        resolved = path.resolve()
        for protected in PROTECTED_PATHS:
            try:
                resolved.relative_to(protected)
                return True
            except ValueError:
                continue
    except Exception:
        pass
    return False


def requires_confirmation(operation: str, path: Path | None = None, size: int = 0) -> bool:
    """Determine if an operation requires user confirmation."""
    tier = classify_operation(operation)

    if tier >= PermissionTier.DESTRUCTIVE:
        return True

    if path and is_protected_path(path):
        return True

    if size > BATCH_SIZE_THRESHOLD:
        return True

    return False
