"""
Trinity Memory — Vector Store using ChromaDB.
"""

import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class MemoryStore:
    """Semantic memory store using ChromaDB for fact storage and retrieval."""

    def __init__(self, config: dict):
        self.config = config
        self.client = None
        self.collection = None
        self._init_store()

    def _init_store(self):
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            data_dir = Path(self.config["trinity"]["data_dir"]).expanduser() / "data" / "chroma"
            self.client = chromadb.PersistentClient(path=str(data_dir))
            self.collection = self.client.get_or_create_collection(
                name="trinity_memory",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("memory.chromadb.initialized", path=str(data_dir))
        except ImportError:
            logger.warning("memory.chromadb_not_available")
        except Exception as e:
            logger.error("memory.chromadb.init_failed", error=str(e))

    async def remember(self, fact: str, category: str = "general", pinned: bool = False):
        """Store a fact in memory."""
        if not self.collection:
            logger.warning("memory.store_unavailable")
            return

        try:
            import uuid
            self.collection.add(
                documents=[fact],
                metadatas=[{"category": category, "pinned": pinned}],
                ids=[str(uuid.uuid4())],
            )
            logger.info("memory.fact_stored", fact=fact[:50], category=category, pinned=pinned)
        except Exception as e:
            logger.error("memory.store_failed", error=str(e))

    async def recall(self, query: str, n: int = 5) -> list[str]:
        """Search memory for relevant facts."""
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n,
            )
            facts = results.get("documents", [[]])[0]
            logger.info("memory.recalled", query=query[:30], results=len(facts))
            return facts
        except Exception as e:
            logger.error("memory.recall_failed", error=str(e))
            return []

    async def forget(self, fact_substring: str) -> int:
        """Remove facts containing a substring."""
        if not self.collection:
            return 0

        try:
            all_data = self.collection.get()
            ids_to_delete = []
            for i, doc in enumerate(all_data["documents"]):
                if fact_substring.lower() in doc.lower():
                    ids_to_delete.append(all_data["ids"][i])

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info("memory.forgotten", count=len(ids_to_delete))

            return len(ids_to_delete)
        except Exception as e:
            logger.error("memory.forget_failed", error=str(e))
            return 0

    async def list_all(self, category: str | None = None) -> list[dict]:
        """List all stored memories."""
        if not self.collection:
            return []

        try:
            where_filter = {"category": category} if category else None
            results = self.collection.get(where=where_filter)
            memories = []
            for i, doc in enumerate(results["documents"]):
                memories.append({
                    "id": results["ids"][i],
                    "content": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
            return memories
        except Exception as e:
            logger.error("memory.list_failed", error=str(e))
            return []
