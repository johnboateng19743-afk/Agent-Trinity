"""
Trinity LLM — Hybrid LLM Router.
Routes requests to cloud (primary) or local (offline fallback) LLMs.
"""

import asyncio
import structlog

try:
    import anthropic as _anthropic_module
except ImportError:
    _anthropic_module = None

logger = structlog.get_logger(__name__)


class LLMRouter:
    """Routes LLM requests based on availability and complexity."""

    def __init__(self, config: dict):
        self.config = config
        self.openai_client = None
        self.anthropic_client = None
        self.ollama_client = None
        self._init_clients()

    def _init_clients(self):
        """Initialize LLM clients."""
        # OpenAI (primary)
        if self.config["llm"]["openai_api_key"]:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.config["llm"]["openai_api_key"])
                logger.info("llm.openai.initialized")
            except Exception as e:
                logger.error("llm.openai.init_failed", error=str(e))
        else:
            logger.warning("llm.openai.no_api_key")

        # Anthropic (fallback)
        if self.config["llm"]["anthropic_api_key"]:
            try:
                from anthropic import AsyncAnthropic
                self.anthropic_client = AsyncAnthropic(api_key=self.config["llm"]["anthropic_api_key"])
                logger.info("llm.anthropic.initialized")
            except Exception as e:
                logger.warning("llm.anthropic.init_failed", error=str(e))
        else:
            logger.warning("llm.anthropic.no_api_key")

        # Ollama (offline)
        try:
            import ollama
            self.ollama_client = ollama.AsyncClient(host=self.config["llm"]["ollama_base_url"])
            logger.info("llm.ollama.initialized")
        except Exception as e:
            logger.warning("llm.ollama.init_failed", error=str(e))

    async def chat(self, message: str, context: dict | None = None,
                   system_prompt: str = "") -> str:
        """Send a chat message and get a response. Local-first with cloud fallback."""
        messages = []

        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history from context
        if context and context.get("history"):
            for exchange in context["history"][-20:]:  # Last 10 exchanges
                role = "user" if exchange["role"] == "user" else "assistant"
                messages.append({"role": role, "content": exchange["content"]})

        # Add current message
        messages.append({"role": "user", "content": message})

        # Check mode: local-first or cloud-first
        mode = self.config["llm"].get("mode", "local")

        if mode == "local":
            # Local-first: try Ollama, then fall back to cloud
            response = await self._try_ollama(messages)
            if response is not None:
                return response

            response = await self._try_openai(messages)
            if response is not None:
                return response

            response = await self._try_anthropic(messages)
            if response is not None:
                return response
        else:
            # Cloud-first: try OpenAI, then Anthropic, then Ollama
            response = await self._try_openai(messages)
            if response is not None:
                return response

            response = await self._try_anthropic(messages)
            if response is not None:
                return response

            response = await self._try_ollama(messages)
            if response is not None:
                return response

        return "I'm having trouble reaching my brain right now. I can still help with basic file operations."

    async def _try_openai(self, messages: list[dict]) -> str | None:
        """Try OpenAI GPT-4o."""
        if not self.openai_client:
            return None

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.config["llm"]["cloud_primary"],
                messages=messages,
                max_tokens=self.config["llm"]["max_tokens"],
                temperature=self.config["llm"]["temperature"],
            )
            result = response.choices[0].message.content
            if result and hasattr(response, 'usage') and response.usage:
                logger.info("llm.openai.success", tokens=response.usage.total_tokens)
            else:
                logger.info("llm.openai.success")
            return result
        except Exception as e:
            logger.warning("llm.openai.failed", error=str(e))
            return None

    async def _try_anthropic(self, messages: list[dict]) -> str | None:
        """Try Anthropic Claude."""
        if not self.anthropic_client:
            return None

        try:
            # Anthropic uses a different message format — no "system" in messages array
            system_msg = ""
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    chat_messages.append(msg)

            # Ensure first message is not system
            if chat_messages and chat_messages[0]["role"] == "system":
                chat_messages = chat_messages[1:]

            response = await self.anthropic_client.messages.create(
                model=self.config["llm"]["cloud_fallback"],
                system=system_msg if system_msg else (_anthropic_module.NOT_GIVEN if _anthropic_module else ""),
                messages=chat_messages,
                max_tokens=self.config["llm"]["max_tokens"],
            )
            result = response.content[0].text
            logger.info("llm.anthropic.success")
            return result
        except Exception as e:
            logger.warning("llm.anthropic.failed", error=str(e))
            return None

    async def _try_ollama(self, messages: list[dict]) -> str | None:
        """Try local Ollama model (offline fallback)."""
        if not self.ollama_client:
            return None

        try:
            response = await self.ollama_client.chat(
                model=self.config["llm"]["local_fast"],
                messages=messages,
            )
            result = response["message"]["content"]
            logger.info("llm.ollama.success", model=self.config["llm"]["local_fast"])
            return result
        except Exception as e:
            logger.warning("llm.ollama.failed", error=str(e))
            return None
