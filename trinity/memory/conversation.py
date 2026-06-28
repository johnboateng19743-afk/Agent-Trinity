"""
Trinity Memory — Conversation Store using SQLite.
"""

import asyncio
import aiosqlite
import json
import structlog
from pathlib import Path
from datetime import datetime

logger = structlog.get_logger(__name__)


class ConversationStore:
    """Persistent conversation log using SQLite."""

    def __init__(self, config: dict):
        self.config = config
        data_dir = Path(config["trinity"]["data_dir"]).expanduser() / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(data_dir / "conversations.db")
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("memory.conversation_db.initialized", path=self.db_path)

    async def add_exchange(self, user_text: str, trinity_response: str, metadata: dict | None = None):
        """Store a conversation exchange."""
        now = datetime.utcnow().isoformat()
        meta_str = json.dumps(metadata) if metadata else None

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO conversations (timestamp, role, content, metadata) VALUES (?, ?, ?, ?)",
                    (now, "user", user_text, meta_str),
                )
                await db.execute(
                    "INSERT INTO conversations (timestamp, role, content, metadata) VALUES (?, ?, ?, ?)",
                    (now, "trinity", trinity_response, meta_str),
                )
                await db.commit()
            logger.debug("conversation.exchange_stored")
        except Exception as e:
            logger.error("conversation.store_failed", error=str(e))

    async def get_recent(self, n: int = 20) -> list[dict]:
        """Get the most recent n exchanges."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM conversations ORDER BY id DESC LIMIT ?", (n,)
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in reversed(rows)]
        except Exception as e:
            logger.error("conversation.get_recent_failed", error=str(e))
            return []

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search conversation history."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM conversations WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
                    (f"%{query}%", limit),
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in reversed(rows)]
        except Exception as e:
            logger.error("conversation.search_failed", error=str(e))
            return []

    async def delete_range(self, start_time: str, end_time: str):
        """Delete conversation entries in a time range."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM conversations WHERE timestamp BETWEEN ? AND ?",
                    (start_time, end_time),
                )
                await db.commit()
            logger.info("conversation.range_deleted", start=start_time, end=end_time)
        except Exception as e:
            logger.error("conversation.delete_range_failed", error=str(e))

    async def purge(self):
        """Delete all conversation history."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM conversations")
                await db.commit()
            logger.info("conversation.purged")
        except Exception as e:
            logger.error("conversation.purge_failed", error=str(e))
