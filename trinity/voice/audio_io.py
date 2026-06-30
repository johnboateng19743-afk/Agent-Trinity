"""
Trinity Voice Engine — Audio Input/Output management.
Uses sounddevice (pre-built wheels, no C compiler needed on Windows).
"""

import asyncio
import structlog
import numpy as np

logger = structlog.get_logger(__name__)

SAMPLE_RATE = 16000
CHUNK_SIZE = 512
CHANNELS = 1


class AudioIO:
    """Manages microphone input and speaker output using sounddevice."""

    def __init__(self, config: dict):
        self.config = config
        self._recording = False
        self._audio_buffer = []

    def _init_sounddevice(self):
        """Verify sounddevice is available."""
        try:
            import sounddevice as sd
            return sd
        except ImportError:
            logger.error("audio_io.sounddevice_not_available", hint="pip install sounddevice")
            raise

    async def read_chunk(self) -> bytes:
        """Read a chunk of audio from the microphone."""
        loop = asyncio.get_event_loop()

        def _read():
            try:
                sd = self._init_sounddevice()
                # Read one chunk of audio
                audio_data = sd.rec(
                    frames=CHUNK_SIZE,
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype='int16',
                    blocking=True,
                )
                return audio_data.tobytes()
            except Exception as e:
                logger.error("audio_io.read_error", error=str(e))
                return b"\x00" * CHUNK_SIZE * 2

        try:
            return await loop.run_in_executor(None, _read)
        except Exception as e:
            logger.error("audio_io.read_failed", error=str(e))
            return b"\x00" * CHUNK_SIZE * 2  # Return silence on error

    async def record_until_silence(self, silence_threshold: int = 500, 
                                    silence_duration: float = 1.5,
                                    max_duration: float = 30.0) -> bytes:
        """Record audio until silence is detected or max duration reached."""
        loop = asyncio.get_event_loop()

        def _record():
            try:
                sd = self._init_sounddevice()
                frames = []
                silent_chunks = 0
                max_chunks = int(max_duration * SAMPLE_RATE / CHUNK_SIZE)
                silence_chunks_needed = int(silence_duration * SAMPLE_RATE / CHUNK_SIZE)

                with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16') as stream:
                    for _ in range(max_chunks):
                        chunk, _ = stream.read(CHUNK_SIZE)
                        frames.append(chunk)

                        # Check if this chunk is silence
                        amplitude = np.abs(chunk).mean()
                        if amplitude < silence_threshold:
                            silent_chunks += 1
                        else:
                            silent_chunks = 0

                        # Stop if we've had enough silence after some speech
                        if silent_chunks >= silence_chunks_needed and len(frames) > silence_chunks_needed:
                            break

                audio_data = np.concatenate(frames)
                return audio_data.tobytes()
            except Exception as e:
                logger.error("audio_io.record_error", error=str(e))
                return b""

        try:
            return await loop.run_in_executor(None, _record)
        except Exception as e:
            logger.error("audio_io.record_failed", error=str(e))
            return b""

    async def play_file(self, path):
        """Play an audio file."""
        loop = asyncio.get_event_loop()

        def _play():
            import subprocess
            try:
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-quiet", str(path)],
                    capture_output=True, timeout=30
                )
            except FileNotFoundError:
                # Fallback: Windows default player
                try:
                    subprocess.run(
                        ["cmd", "/c", "start", "/min", "", str(path)],
                        capture_output=True, timeout=10
                    )
                except Exception:
                    logger.warning("audio_io.no_player_found")
            except Exception as e:
                logger.error("audio_io.play_failed", error=str(e))

        try:
            await loop.run_in_executor(None, _play)
        except Exception as e:
            logger.error("audio_io.play_failed", error=str(e))

    def cleanup(self):
        """Clean up audio resources."""
        try:
            import sounddevice as sd
            sd.stop()
        except Exception as e:
            logger.warning("audio_io.cleanup_error", error=str(e))
