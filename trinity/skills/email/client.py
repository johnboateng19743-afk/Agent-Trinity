"""
Trinity Skill — Gmail Client.
"""

import structlog
from trinity.skills.base import BaseSkill, SkillResult

logger = structlog.get_logger(__name__)


class EmailClient(BaseSkill):
    """Gmail integration."""

    def __init__(self, config: dict, google_auth=None):
        super().__init__(config)
        self.google_auth = google_auth
        self.service = None

    def _get_service(self):
        """Get authenticated Gmail service."""
        if self.service:
            return self.service
        if not self.google_auth:
            return None
        self.service = self.google_auth.get_gmail_service()
        return self.service

    async def execute(self, entities: dict, context: dict | None = None) -> SkillResult:
        """Execute email operation."""
        service = self._get_service()
        if not service:
            return self._error(
                "Gmail isn't connected yet. Say 'Trinity, connect my Google account' to set it up."
            )

        raw_text = entities.get("raw_text", "").lower()

        if any(kw in raw_text for kw in ["send", "compose", "email ", "write"]):
            return await self._compose(entities, service)
        elif any(kw in raw_text for kw in ["reply"]):
            return await self._reply(entities, service)
        elif any(kw in raw_text for kw in ["delete", "remove", "trash"]):
            return await self._delete(entities, service)
        else:
            return await self._read(entities, service)

    async def _read(self, entities: dict, service) -> SkillResult:
        """Read recent emails."""
        try:
            results = service.users().messages().list(
                userId="me",
                maxResults=5,
                labelIds=["INBOX"],
            ).execute()

            messages = results.get("messages", [])

            if not messages:
                return self._success("Your inbox is empty!")

            lines = ["📧 Recent emails:\n"]
            for msg in messages:
                msg_data = service.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                ).execute()

                headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
                subject = headers.get("Subject", "(No subject)")
                sender = headers.get("From", "Unknown")
                date = headers.get("Date", "")

                lines.append(f"  From: {sender}")
                lines.append(f"  Subject: {subject}")
                lines.append(f"  Date: {date}")
                lines.append("")

            return self._success("\n".join(lines))

        except Exception as e:
            logger.error("email.read_failed", error=str(e))
            return self._error(f"Error reading emails: {str(e)}")

    async def _compose(self, entities: dict, service) -> SkillResult:
        """Compose a new email — ALWAYS requires confirmation."""
        return self._confirm(
            "I'll draft an email for you. You must review and confirm before I send it. "
            "Who is the recipient and what should I say?"
        )

    async def _reply(self, entities: dict, service) -> SkillResult:
        """Reply to an email — ALWAYS requires confirmation."""
        return self._confirm(
            "I'll draft a reply. You must review and confirm before I send it."
        )

    async def _delete(self, entities: dict, service) -> SkillResult:
        """Delete email(s) — requires confirmation."""
        return self._confirm("Delete these emails? This will move them to trash.")
