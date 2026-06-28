"""
Trinity Tests — Orchestrator Tests.
"""

import pytest
from trinity.orchestrator.router import IntentRouter


@pytest.fixture
def config():
    return {"trinity": {"user_name": "Mr. Walker"}}


class TestIntentRouter:
    """Tests for intent classification and routing."""

    @pytest.mark.asyncio
    async def test_calendar_intent(self, config):
        router = IntentRouter(config)
        intent = await router.classify("What's on my calendar today?")
        assert intent.skill == "calendar"

    @pytest.mark.asyncio
    async def test_email_intent(self, config):
        router = IntentRouter(config)
        intent = await router.classify("Read my latest emails")
        assert intent.skill == "email"

    @pytest.mark.asyncio
    async def test_filesystem_search_intent(self, config):
        router = IntentRouter(config)
        intent = await router.classify("Find all PDFs in my Downloads")
        assert intent.skill == "filesystem.search"

    @pytest.mark.asyncio
    async def test_filesystem_delete_intent(self, config):
        router = IntentRouter(config)
        intent = await router.classify("Delete all temp files")
        assert intent.skill == "filesystem.delete"

    @pytest.mark.asyncio
    async def test_maps_directions_intent(self, config):
        router = IntentRouter(config)
        intent = await router.classify("How do I get to the airport?")
        assert intent.skill == "maps.directions"

    @pytest.mark.asyncio
    async def test_unknown_intent_fallback(self, config):
        router = IntentRouter(config)
        intent = await router.classify("Tell me a joke")
        assert intent.skill == "llm_conversation"

    @pytest.mark.asyncio
    async def test_intent_has_raw_text(self, config):
        router = IntentRouter(config)
        intent = await router.classify("Find my resume")
        assert intent.raw_text == "Find my resume"

    @pytest.mark.asyncio
    async def test_intent_confidence_range(self, config):
        router = IntentRouter(config)
        intent = await router.classify("Delete old files")
        assert 0.0 <= intent.confidence <= 1.0
