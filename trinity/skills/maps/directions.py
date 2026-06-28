"""
Trinity Skill — Directions Service.
"""

import structlog
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)


class DirectionsService(BaseSkill):
    """Get directions and commute information."""

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute directions operation."""
        maps_key = self.config.get("google", {}).get("maps_api_key", "")
        if not maps_key:
            return self._error(
                "Google Maps isn't configured yet. Add your Maps API key to enable directions."
            )

        raw_text = entities.get("raw_text", "").lower()

        if any(kw in raw_text for kw in ["how far", "distance", "eta", "how long"]):
            return await self._get_distance(entities)
        elif any(kw in raw_text for kw in ["directions", "navigate", "how to get", "route"]):
            return await self._get_directions(entities)
        else:
            return self._success("Where would you like directions to?")

    async def _get_directions(self, entities: dict) -> SkillResult:
        """Get directions between two points."""
        return self._success("Getting directions...")

    async def _get_distance(self, entities: dict) -> SkillResult:
        """Get distance and travel time."""
        return self._success("Calculating distance...")
