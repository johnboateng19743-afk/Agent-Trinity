"""
Trinity Voice Engine — Text-to-Speech using ElevenLabs.
"""

import asyncio
import structlog
import requests

logger = structlog.get_logger(__name__)


class TTSEngine:
    """Text-to-Speech engine using ElevenLabs API."""

    def __init__(self, config: dict):
        self.config = config
        self.api_key = config["voice"]["elevenlabs_api_key"]
        self.voice_id = config["voice"]["elevenlabs_voice_id"]
        self.model = config["voice"]["elevenlabs_model"]
        self.speaking = False

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

    async def _generate_speech(self, text: str, emotion: str = "neutral") -> bytes:
        """Generate speech audio from text via ElevenLabs API."""
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

    def _get_voice_settings(self, emotion: str = "neutral") -> dict:
        """Return voice settings based on emotion."""
        presets = {
            "neutral": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True},
            "friendly": {"stability": 0.4, "similarity_boost": 0.75, "style": 0.3, "use_speaker_boost": True},
            "excited": {"stability": 0.3, "similarity_boost": 0.75, "style": 0.7, "use_speaker_boost": True},
            "calm": {"stability": 0.7, "similarity_boost": 0.8, "style": 0.1, "use_speaker_boost": True},
            "serious": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.2, "use_speaker_boost": True},
            "whisper": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": False},
        }
        return presets.get(emotion, presets["neutral"])

    async def _play_audio(self, audio_data: bytes):
        """Play MP3 audio data through speakers."""
        loop = asyncio.get_event_loop()

        def _do_play():
            import tempfile
            import subprocess
            from pathlib import Path

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                # Try ffplay first (ffmpeg)
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-quiet", temp_path],
                    check=True, capture_output=True, timeout=30
                )
            except (FileNotFoundError, subprocess.SubprocessError):
                # Fallback: open with Windows default player
                try:
                    subprocess.run(
                        ["cmd", "/c", "start", "/min", "", temp_path],
                        check=True, capture_output=True, timeout=10
                    )
                    # Give the player time to load the file
                    import time
                    time.sleep(3)
                except Exception:
                    logger.warning("tts.no_audio_player")
            finally:
                # Clean up temp file
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception:
                    pass

        await loop.run_in_executor(None, _do_play)
