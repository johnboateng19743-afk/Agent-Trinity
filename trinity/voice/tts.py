"""
Trinity Voice Engine — Text-to-Speech using ElevenLabs.
"""

import asyncio
import io
import structlog
import requests
import pyaudio

logger = structlog.get_logger(__name__)


class TTSEngine:
    """Text-to-Speech engine using ElevenLabs API with WebSocket streaming."""

    def __init__(self, config: dict):
        self.config = config
        self.api_key = config["voice"]["elevenlabs_api_key"]
        self.voice_id = config["voice"]["elevenlabs_voice_id"]
        self.model = config["voice"]["elevenlabs_model"]
        self.speaking = False
        self._pyaudio = pyaudio.PyInitialize() if False else None  # Lazy init

    async def speak(self, text: str, emotion: str = "neutral"):
        """Convert text to speech and play through speakers."""
        if not text or not text.strip():
            return

        self.speaking = True

        try:
            audio_data = await self._generate_speech(text, emotion)
            await self._play_audio(audio_data)
        except Exception as e:
            logger.error("tts.speak_failed", error=str(e))
        finally:
            self.speaking = False

    async def stop_speaking(self):
        """Stop current TTS playback."""
        self.speaking = False
        if self._pyaudio:
            # Stop any active stream
            pass

    async def _generate_speech(self, text: str, emotion: str = "neutral") -> bytes:
        """Generate speech audio from text via ElevenLabs API."""
        # Voice settings based on emotion context
        settings = self._get_voice_settings(emotion)

        loop = asyncio.get_event_loop()

        def _do_request():
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            }
            data = {
                "text": text,
                "model_id": self.model,
                "voice_settings": settings,
            }
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.content

        try:
            audio_data = await loop.run_in_executor(None, _do_request)
            logger.info("tts.generated", chars=len(text), emotion=emotion)
            return audio_data
        except Exception as e:
            logger.error("tts.generation_failed", error=str(e))
            raise

    async def _generate_speech_streaming(self, text: str, emotion: str = "neutral"):
        """Generate speech via WebSocket for real-time streaming playback."""
        try:
            import websockets
            import json

            uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
            settings = self._get_voice_settings(emotion)

            async with websockets.connect(uri) as ws:
                # Send configuration
                await ws.send(json.dumps({
                    "text": " ",
                    "voice_settings": settings,
                    "xi_api_key": self.api_key,
                    "model_id": self.model,
                }))

                # Send text
                await ws.send(json.dumps({
                    "text": text,
                    "try_trigger_generation": True,
                }))

                # Send end signal
                await ws.send(json.dumps({"text": ""}))

                # Receive audio chunks
                audio_buffer = b""
                async for message in ws:
                    if isinstance(message, bytes):
                        audio_buffer += message
                        # Play chunk immediately for low-latency
                        await self._play_audio_chunk(message)

                return audio_buffer

        except ImportError:
            logger.warning("tts.websockets_not_available", fallback="rest_api")
            return await self._generate_speech(text, emotion)
        except Exception as e:
            logger.error("tts.streaming_failed", error=str(e), fallback="rest_api")
            return await self._generate_speech(text, emotion)

    async def _play_audio(self, audio_data: bytes):
        """Play MP3 audio data through speakers."""
        loop = asyncio.get_event_loop()

        def _do_play():
            try:
                import pygame
                pygame.mixer.init()
                sound = pygame.mixer.Sound(file=io.BytesIO(audio_data))
                sound.play()
                while pygame.mixer.get_busy():
                    pygame.time.Clock().tick(30)
            except ImportError:
                # Fallback: save to temp file and play with system player
                import tempfile
                import subprocess
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(audio_data)
                    temp_path = f.name
                try:
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", temp_path],
                                   check=True, capture_output=True)
                finally:
                    Path(temp_path).unlink(missing_ok=True)

        await loop.run_in_executor(None, _do_play)

    async def _play_audio_chunk(self, chunk: bytes):
        """Play a single audio chunk (for streaming)."""
        # Buffer and play — simplified for now
        pass

    def _get_voice_settings(self, emotion: str) -> dict:
        """Get voice settings based on emotional context."""
        settings_map = {
            "neutral": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3, "use_speaker_boost": True},
            "greeting": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.4, "use_speaker_boost": True},
            "information": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.2, "use_speaker_boost": True},
            "confirmation": {"stability": 0.4, "similarity_boost": 0.75, "style": 0.5, "use_speaker_boost": True},
            "error": {"stability": 0.7, "similarity_boost": 0.75, "style": 0.1, "use_speaker_boost": True},
            "casual": {"stability": 0.3, "similarity_boost": 0.75, "style": 0.6, "use_speaker_boost": True},
            "reading": {"stability": 0.7, "similarity_boost": 0.75, "style": 0.1, "use_speaker_boost": True},
        }
        return settings_map.get(emotion, settings_map["neutral"])
