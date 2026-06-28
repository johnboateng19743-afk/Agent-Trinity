"""
Trinity Memory — User Profile Management.
"""

import yaml
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class UserProfile:
    """Manages the user's profile and preferences."""

    def __init__(self, config: dict):
        self.config = config
        self.profile_path = Path(config["trinity"]["data_dir"]).expanduser() / "profile.yaml"
        self.profile = self._load_profile()

    def _load_profile(self) -> dict:
        """Load user profile from YAML file."""
        if self.profile_path.exists():
            with open(self.profile_path) as f:
                profile = yaml.safe_load(f) or {}
            logger.info("profile.loaded", path=str(self.profile_path))
            return profile

        # Create default profile from config
        profile = {
            "name": self.config["trinity"]["user_name"],
            "timezone": self.config["trinity"]["timezone"],
            "home_address": self.config["trinity"]["home_address"],
            "home_city": self.config["trinity"]["home_city"],
            "work_address": self.config["trinity"]["work_address"],
            "preferences": {},
            "shortcuts": {},
            "pinned_memories": [],
        }
        self._save_profile(profile)
        return profile

    def _save_profile(self, profile: dict | None = None):
        """Save user profile to YAML file."""
        if profile is None:
            profile = self.profile
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.profile_path, "w") as f:
            yaml.dump(profile, f, default_flow_style=False)
        logger.info("profile.saved")

    def get(self, key: str, default=None):
        """Get a profile value."""
        return self.profile.get(key, default)

    def set(self, key: str, value):
        """Set a profile value and save."""
        self.profile[key] = value
        self._save_profile()

    def set_preference(self, key: str, value):
        """Set a user preference."""
        if "preferences" not in self.profile:
            self.profile["preferences"] = {}
        self.profile["preferences"][key] = value
        self._save_profile()
        logger.info("profile.preference_set", key=key, value=value)

    def get_preference(self, key: str, default=None):
        """Get a user preference."""
        return self.profile.get("preferences", {}).get(key, default)

    def add_shortcut(self, name: str, command: str):
        """Add a voice shortcut."""
        if "shortcuts" not in self.profile:
            self.profile["shortcuts"] = {}
        self.profile["shortcuts"][name] = command
        self._save_profile()

    def pin_memory(self, fact: str):
        """Pin a memory so it never decays."""
        if "pinned_memories" not in self.profile:
            self.profile["pinned_memories"] = []
        self.profile["pinned_memories"].append(fact)
        self._save_profile()
