"""
Trinity Orchestrator — Conversation Context Manager.
Manages conversation history and context window.
"""

import structlog

logger = structlog.get_logger(__name__)

MAX_CONTEXT_EXCHANGES = 50


class ConversationManager:
    """Manages conversation context and history."""

    def __init__(self, config: dict):
        self.config = config
        self.history: list[dict] = []
        self.max_exchanges = MAX_CONTEXT_EXCHANGES

    async def get_context(self) -> dict:
        """Get current conversation context for the LLM."""
        return {
            "history": self.history[-self.max_exchanges:],
            "exchange_count": len(self.history),
            "user_name": self.config["trinity"]["user_name"],
            "timezone": self.config["trinity"]["timezone"],
            "home_city": self.config["trinity"]["home_city"],
        }

    async def add_exchange(self, user_text: str, trinity_response: str):
        """Add a conversation exchange to history."""
        self.history.append({
            "role": "user",
            "content": user_text,
        })
        self.history.append({
            "role": "trinity",
            "content": trinity_response,
        })

        # Trim history if it exceeds max
        if len(self.history) > self.max_exchanges * 2:
            self.history = self.history[-self.max_exchanges * 2:]

        logger.debug("context.exchange_added", total=len(self.history))

    async def clear(self):
        """Clear conversation history."""
        self.history.clear()
        logger.info("context.cleared")

    async def get_recent(self, n: int = 5) -> list[dict]:
        """Get the most recent n exchanges."""
        return self.history[-n * 2:]
