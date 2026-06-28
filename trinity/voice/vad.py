"""
Trinity Voice Engine — Voice Activity Detection.
"""

import structlog
import numpy as np

logger = structlog.get_logger(__name__)


class VoiceActivityDetector:
    """Detects when speech starts and stops in an audio stream."""

    def __init__(self, config: dict):
        self.config = config
        self.silence_threshold = 500  # Energy threshold for silence
        self._vad = None
        self._init_vad()

    def _init_vad(self):
        """Initialize VAD engine."""
        try:
            import webrtcvad
            self._vad = webrtcvad.Vad()
            self._vad.set_mode(2)  # 0-3, 3 = most aggressive filtering
            logger.info("vad.webrtcvad.loaded")
        except ImportError:
            logger.warning("vad.webrtcvad_not_found", fallback="energy_based")

    def is_silence(self, audio_chunk: bytes) -> bool:
        """Check if an audio chunk is silence."""
        if self._vad is not None:
            return self._is_silence_webrtc(audio_chunk)
        return self._is_silence_energy(audio_chunk)

    def _is_silence_webrtc(self, audio_chunk: bytes) -> bool:
        """Use WebRTC VAD for silence detection."""
        try:
            # WebRTC VAD requires specific frame sizes
            # 16kHz, 16-bit mono = 320 samples per 20ms frame
            frame_size = 320 * 2  # bytes
            if len(audio_chunk) >= frame_size:
                return not self._vad.is_speech(audio_chunk[:frame_size], sample_rate=16000)
            return True
        except Exception:
            return self._is_silence_energy(audio_chunk)

    def _is_silence_energy(self, audio_chunk: bytes) -> bool:
        """Simple energy-based silence detection."""
        try:
            audio = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            energy = np.sqrt(np.mean(audio ** 2))
            return energy < self.silence_threshold
        except Exception:
            return True
