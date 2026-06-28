"""
Trinity Voice Engine — Audio Input/Output management.
"""

import asyncio
import structlog

logger = structlog.get_logger(__name__)

SAMPLE_RATE = 16000
CHUNK_SIZE = 512
CHANNELS = 1


class AudioIO:
    """Manages microphone input and speaker output."""

    def __init__(self, config: dict):
        self.config = config
        self._stream = None
        self._pyaudio = None

    def _init_pyaudio(self):
        """Initialize PyAudio lazily."""
        if self._pyaudio is None:
            try:
                import pyaudio
                self._pyaudio = pyaudio.PyAudio()
                self._stream = self._pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE,
                )
                logger.info("audio_io.initialized", sample_rate=SAMPLE_RATE)
            except ImportError:
                logger.error("audio_io.pyaudio_not_available")
                raise
            except Exception as e:
                logger.error("audio_io.init_failed", error=str(e))
                raise

    async def read_chunk(self) -> bytes:
        """Read a chunk of audio from the microphone."""
        loop = asyncio.get_event_loop()

        def _read():
            self._init_pyaudio()
            return self._stream.read(CHUNK_SIZE, exception_on_overflow=False)

        try:
            return await loop.run_in_executor(None, _read)
        except Exception as e:
            logger.error("audio_io.read_failed", error=str(e))
            return b"\x00" * CHUNK_SIZE * 2  # Return silence on error

    async def play_file(self, path):
        """Play an audio file."""
        loop = asyncio.get_event_loop()

        def _play():
            import subprocess
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", str(path)],
                check=True, capture_output=True
            )

        try:
            await loop.run_in_executor(None, _play)
        except FileNotFoundError:
            logger.warning("audio_io.ffplay_not_found", hint="Install ffmpeg")
        except Exception as e:
            logger.error("audio_io.play_failed", error=str(e))

    def cleanup(self):
        """Clean up audio resources."""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pyaudio:
            self._pyaudio.terminate()
