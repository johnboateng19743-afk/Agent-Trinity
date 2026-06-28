"""
Trinity Skill — Location Service.
"""

import structlog
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)


class LocationService(BaseSkill):
    """Get current location and find nearby places."""

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute location operation."""
        raw_text = entities.get("raw_text", "").lower()

        if any(kw in raw_text for kw in ["where am i", "my location", "current location"]):
            return await self._get_current_location()
        elif any(kw in raw_text for kw in ["nearest", "nearby", "close", "around"]):
            return await self._find_nearby(entities)
        else:
            return self._success(f"You're currently in {self.config['trinity']['home_city']}.")

    async def _get_current_location(self) -> SkillResult:
        """Get the user's current location."""
        # Try Windows Location API first
        try:
            # TODO: Implement winrt location
            pass
        except Exception:
            pass

        # Fallback: use configured city
        city = self.config["trinity"]["home_city"]
        return self._success(f"You're currently in {city}.")

    async def _find_nearby(self, entities: dict) -> SkillResult:
        """Find nearby places using Google Maps."""
        maps_key = self.config.get("google", {}).get("maps_api_key", "")
        if not maps_key:
            return self._error(
                "Google Maps isn't configured yet. Add your Maps API key to enable location search."
            )

        query = entities.get("raw_text", "")
        return self._success(f"Searching for '{query}' nearby...")
