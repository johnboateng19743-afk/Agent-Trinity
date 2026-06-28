"""
Trinity Skill — Google Calendar Client.
"""

import structlog
from datetime import datetime, timedelta
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)


class CalendarClient(BaseSkill):
    """Google Calendar integration."""

    def __init__(self, config: dict, google_auth=None):
        super().__init__(config)
        self.google_auth = google_auth
        self.service = None

    def _get_service(self):
        """Get authenticated Calendar service."""
        if self.service:
            return self.service
        if not self.google_auth:
            return None
        self.service = self.google_auth.get_calendar_service()
        return self.service

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute calendar operation."""
        service = self._get_service()
        if not service:
            return self._error(
                "Google Calendar isn't connected yet. Say 'Trinity, connect my Google account' to set it up."
            )

        raw_text = entities.get("raw_text", "").lower()

        if any(kw in raw_text for kw in ["create", "schedule", "add", "new meeting"]):
            return await self._create_event(entities, service)
        elif any(kw in raw_text for kw in ["delete", "cancel", "remove"]):
            return await self._delete_event(entities, service)
        elif any(kw in raw_text for kw in ["move", "change", "reschedule"]):
            return await self._modify_event(entities, service)
        elif any(kw in raw_text for kw in ["free", "available", "open"]):
            return await self._find_free_time(entities, service)
        else:
            return await self._view_events(entities, service)

    async def _view_events(self, entities: dict, service) -> SkillResult:
        """View upcoming calendar events."""
        try:
            now = datetime.utcnow().isoformat() + "Z"
            end = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                timeMax=end,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = events_result.get("items", [])

            if not events:
                return self._success("Your calendar is clear — you have nothing scheduled.")

            lines = ["📅 Upcoming events:\n"]
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date", ""))
                summary = event.get("summary", "No title")
                lines.append(f"  {start[:16]} — {summary}")

            return self._success("\n".join(lines), data={"events": events})

        except Exception as e:
            logger.error("calendar.view_failed", error=str(e))
            return self._error(f"Error reading calendar: {str(e)}")

    async def _create_event(self, entities: dict, service) -> SkillResult:
        """Create a new calendar event."""
        return self._confirm("Create a new calendar event. Please confirm the details.")

    async def _delete_event(self, entities: dict, service) -> SkillResult:
        """Delete a calendar event."""
        return self._confirm("Delete this calendar event? This cannot be undone.")

    async def _modify_event(self, entities: dict, service) -> SkillResult:
        """Modify an existing calendar event."""
        return self._confirm("Reschedule this event?")

    async def _find_free_time(self, entities: dict, service) -> SkillResult:
        """Find free time slots."""
        return self._success("Checking your availability...")
