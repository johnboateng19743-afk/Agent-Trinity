"""
Trinity Tests — Memory Store Tests.
"""

import pytest
from trinity.memory.user_profile import UserProfile


@pytest.fixture
def config(tmp_path):
    return {"trinity": {"data_dir": str(tmp_path), "user_name": "Mr. Walker",
                        "timezone": "Africa/Accra", "home_address": "Hohoe, Ghana",
                        "home_city": "Accra", "work_address": ""}}


class TestUserProfile:
    """Tests for user profile management."""

    def test_create_default_profile(self, config):
        profile = UserProfile(config)
        assert profile.get("name") == "Mr. Walker"
        assert profile.get("timezone") == "Africa/Accra"

    def test_set_preference(self, config):
        profile = UserProfile(config)
        profile.set_preference("dark_mode", True)
        assert profile.get_preference("dark_mode") is True

    def test_add_shortcut(self, config):
        profile = UserProfile(config)
        profile.add_shortcut("work", "Open my work folder")
        assert profile.get("shortcuts")["work"] == "Open my work folder"

    def test_pin_memory(self, config):
        profile = UserProfile(config)
        profile.pin_memory("Project deadline is July 15")
        assert "Project deadline is July 15" in profile.get("pinned_memories")
