"""
Trinity Voice Engine — Speech-to-Text using Whisper.
"""

import asyncio
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class STTEngine:
    """Speech-to-Text engine using faster-whisper (local) or OpenAI Whisper API (cloud)."""

    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.use_cloud = False
        self._init_model()

    def _init_model(self):
        """Initialize the local Whisper model."""
        try:
            from faster_whisper import WhisperModel
            device = "cuda" if self.config["hardware"]["gpu_enabled"] else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            self.model = WhisperModel("base", device=device, compute_type=compute_type)
            logger.info("stt.local_model.loaded", device=device)
        except ImportError:
            logger.warning("stt.faster_whisper_not_found", fallback="cloud")
            self.use_cloud = True
        except Exception as e:
            logger.error("stt.local_model_failed", error=str(e), fallback="cloud")
            self.use_cloud = True

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio data to text."""
        if not audio_data or len(audio_data) < 100:
            return ""

        if self.use_cloud or self.model is None:
            return await self._transcribe_cloud(audio_data)
        return await self._transcribe_local(audio_data)

    async def _transcribe_local(self, audio_data: bytes) -> str:
        """Transcribe using local faster-whisper model."""
        loop = asyncio.get_event_loop()

        def _do_transcribe():
            import tempfile
            import soundfile as sf
            import numpy as np

            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                # Convert raw bytes to wav format
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                if len(audio_array) == 0:
                    Path(temp_path).unlink(missing_ok=True)
                    return ""
                sf.write(temp_path, audio_array, samplerate=16000)

            try:
                segments, info = self.model.transcribe(temp_path, beam_size=5)
                text = " ".join([seg.text for seg in segments]).strip()
                return text
            finally:
                Path(temp_path).unlink(missing_ok=True)

        try:
            text = await loop.run_in_executor(None, _do_transcribe)
            logger.info("stt.transcribed", chars=len(text), method="local")
            return text
        except Exception as e:
            logger.error("stt.local_transcription_failed", error=str(e))
            return await self._transcribe_cloud(audio_data)

    async def _transcribe_cloud(self, audio_data: bytes) -> str:
        """Transcribe using OpenAI Whisper API."""
        try:
            from openai import AsyncOpenAI
            import tempfile

            client = AsyncOpenAI(api_key=self.config["llm"]["openai_api_key"])

            # Save to temp wav file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                f.write(audio_data)

            try:
                with open(temp_path, "rb") as audio_file:
                    response = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en",
                    )
                return response.text
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error("stt.cloud_transcription_failed", error=str(e))
            return ""
