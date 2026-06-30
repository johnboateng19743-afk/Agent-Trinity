"""
Trinity Web — FastAPI backend for chat UI, research, and voice.
"""

import asyncio
import json
import uuid
import structlog
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logger = structlog.get_logger(__name__)


class TrinityWebApp:
    """Web application for Trinity chat interface."""

    def __init__(self, config: dict, llm_router, tts_engine, stt_engine=None, skills: dict = None):
        self.config = config
        self.llm = llm_router
        self.tts = tts_engine
        self.stt = stt_engine
        self.skills = skills or {}
        self.app = FastAPI(title="Trinity", version="1.0.0")
        self.conversations = {}  # session_id -> messages
        self._setup_routes()

    def _setup_routes(self):
        """Set up all web routes."""

        # Serve the chat UI
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            html_path = Path(__file__).parent / "templates" / "index.html"
            return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

        # WebSocket for real-time chat
        @self.app.websocket("/ws/chat")
        async def ws_chat(websocket: WebSocket):
            await websocket.accept()
            session_id = str(uuid.uuid4())[:8]
            self.conversations[session_id] = []
            logger.info("web.session_connected", session=session_id)

            try:
                while True:
                    data = await websocket.receive_text()
                    msg = json.loads(data)

                    if msg.get("type") == "chat":
                        user_text = msg.get("text", "").strip()
                        if not user_text:
                            continue

                        # Store user message
                        self.conversations[session_id].append({
                            "role": "user",
                            "content": user_text,
                            "time": datetime.now().strftime("%H:%M"),
                        })

                        # Send user message back to UI
                        await websocket.send_json({
                            "type": "user_message",
                            "text": user_text,
                            "time": datetime.now().strftime("%H:%M"),
                        })

                        # Send typing indicator
                        await websocket.send_json({"type": "typing"})

                        # Process the message
                        response_text = await self._process_message(user_text, session_id)

                        # Store assistant message
                        self.conversations[session_id].append({
                            "role": "assistant",
                            "content": response_text,
                            "time": datetime.now().strftime("%H:%M"),
                        })

                        # Send response to UI
                        await websocket.send_json({
                            "type": "assistant_message",
                            "text": response_text,
                            "time": datetime.now().strftime("%H:%M"),
                        })

                        # Generate TTS audio if available
                        if self.tts:
                            try:
                                audio_data = await self.tts._generate_speech(response_text, "friendly")
                                import base64
                                audio_b64 = base64.b64encode(audio_data).decode("utf-8")
                                await websocket.send_json({
                                    "type": "audio",
                                    "data": audio_b64,
                                })
                            except Exception as e:
                                logger.warning("web.tts_failed", error=str(e))

                    elif msg.get("type") == "voice":
                        # Voice input — base64 encoded audio
                        audio_b64 = msg.get("audio", "")
                        if audio_b64 and self.stt:
                            try:
                                import base64
                                audio_bytes = base64.b64decode(audio_b64)
                                text = await self.stt.transcribe(audio_bytes)
                                if text and text.strip():
                                    await websocket.send_json({
                                        "type": "transcription",
                                        "text": text,
                                    })
                            except Exception as e:
                                logger.warning("web.stt_failed", error=str(e))

            except WebSocketDisconnect:
                logger.info("web.session_disconnected", session=session_id)
                del self.conversations[session_id]

        # REST endpoint for research
        @self.app.post("/api/research")
        async def research(request: Request):
            body = await request.json()
            query = body.get("query", "").strip()
            if not query:
                return JSONResponse({"error": "No query provided"}, status_code=400)

            result = await self._do_research(query)
            return JSONResponse(result)

        # REST endpoint for skills
        @self.app.post("/api/skill/{skill_name}")
        async def run_skill(skill_name: str, request: Request):
            body = await request.json()
            if skill_name in self.skills:
                try:
                    result = await self.skills[skill_name].execute(body)
                    return JSONResponse({"success": True, "data": result.data if hasattr(result, 'data') else str(result)})
                except Exception as e:
                    return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            return JSONResponse({"error": f"Skill '{skill_name}' not found"}, status_code=404)

        # Health check
        @self.app.get("/api/status")
        async def status():
            return JSONResponse({
                "status": "online",
                "llm": "local" if self.config["llm"].get("mode") == "local" else "cloud",
                "model": self.config["llm"].get("local_fast", "unknown"),
                "skills": list(self.skills.keys()),
                "sessions": len(self.conversations),
            })

    async def _process_message(self, text: str, session_id: str) -> str:
        """Process a user message and return Trinity's response."""
        # Check for research queries
        research_keywords = ["research", "look up", "find info", "search for", "tell me about", "investigate", "analyze"]
        problem_keywords = ["how do i", "how to", "solve", "fix", "troubleshoot", "debug", "help me understand", "explain why"]
        writing_keywords = ["write", "draft", "compose", "email", "letter", "essay", "blog", "article"]

        is_research = any(kw in text.lower() for kw in research_keywords)
        is_problem = any(kw in text.lower() for kw in problem_keywords)
        is_writing = any(kw in text.lower() for kw in writing_keywords)

        # Select the best system prompt
        from trinity.prompts import RESEARCH_SYSTEM_PROMPT, PROBLEM_SOLVING_PROMPT, WRITING_SYSTEM_PROMPT, MAIN_SYSTEM_PROMPT

        if is_research:
            system_prompt = RESEARCH_SYSTEM_PROMPT
        elif is_problem:
            system_prompt = PROBLEM_SOLVING_PROMPT
        elif is_writing:
            system_prompt = WRITING_SYSTEM_PROMPT
        else:
            system_prompt = MAIN_SYSTEM_PROMPT

        # Check for skill commands
        skill_response = await self._try_skill_command(text)
        if skill_response:
            return skill_response

        # Build message history
        history = self.conversations.get(session_id, [])[-20:]

        # Call LLM
        try:
            response = await self.llm.chat(
                message=text,
                context={"history": history},
                system_prompt=system_prompt,
            )
            return response
        except Exception as e:
            logger.error("web.llm_failed", error=str(e))
            return f"I'm having trouble thinking right now. Error: {str(e)}"

    async def _try_skill_command(self, text: str) -> Optional[str]:
        """Try to match a skill command from user text."""
        text_lower = text.lower()

        # File operations
        if any(kw in text_lower for kw in ["read file", "open file", "show file"]):
            if "filesystem.read" in self.skills:
                # Extract path from text
                import re
                path_match = re.search(r'["\']([^"\']+)["\']|(\S+\.\S+)', text)
                if path_match:
                    path = path_match.group(1) or path_match.group(2)
                    try:
                        result = await self.skills["filesystem.read"].execute({"path": path})
                        if result.success and result.data:
                            content = result.data.get("content", "")
                            return f"📄 **{path}**\n\n```\n{content[:3000]}\n```"
                    except Exception:
                        pass

        if any(kw in text_lower for kw in ["write file", "save file", "create file"]):
            if "filesystem.write" in self.skills:
                return "💡 To write a file, use the format: `save file [path] with [content]`"

        return None

    async def _do_research(self, query: str) -> dict:
        """Deep research on a topic using the LLM."""
        system_prompt = """You are a research agent. Provide a comprehensive analysis on the given topic.
Structure your response as:
1. **Summary** — 2-3 sentence overview
2. **Key Facts** — bullet points with important details
3. **Analysis** — deeper insights and context
4. **Recommendations** — actionable next steps (if applicable)

Be thorough, accurate, and well-organized."""

        try:
            response = await self.llm.chat(
                message=f"Research this topic thoroughly: {query}",
                system_prompt=system_prompt,
            )
            return {
                "query": query,
                "result": response,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"query": query, "error": str(e)}

    def run(self, host: str = "0.0.0.0", port: int = 8400):
        """Start the web server."""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port, log_level="warning")
