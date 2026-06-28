"""
Trinity Tests — Update System Tests.
"""

import pytest
from trinity.updates.checker import UpdateChecker


class TestUpdateChecker:
    """Tests for the update checker."""

    def test_init(self):
        config = {
            "updates": {
                "update_repo": "https://github.com/johnboateng19743-design/Agent-Trinity",
                "channel": "stable",
            }
        }
        checker = UpdateChecker(config)
        assert checker.repo_url == "https://github.com/johnboateng19743-design/Agent-Trinity"
        assert checker.channel == "stable"

    @pytest.mark.asyncio
    async def test_check_no_repo(self):
        config = {"updates": {"update_repo": "", "channel": "stable"}}
        checker = UpdateChecker(config)
        result = await checker.check()
        assert result is None
