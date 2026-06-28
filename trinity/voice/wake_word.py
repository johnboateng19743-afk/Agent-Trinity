"""
Trinity Voice Engine — Wake Word Detection.
"""

import structlog

logger = structlog.get_logger(__name__)


class WakeWordEngine:
    """Detects the wake word 'Trinity' in audio stream."""

    def __init__(self, config: dict):
        self.config = config
        self.wake_word = config["voice"]["wake_word"]
        self.sensitivity = config["voice"]["wake_sensitivity"]
        self.model = None
        self._init_model()

    def _init_model(self):
        """Initialize the wake word detection model."""
        try:
            from openwakeword import Model
            self.model = Model()
            logger.info("wake_word.model.loaded", word=self.wake_word)
        except ImportError:
            logger.warning("wake_word.openwakeword_not_found", fallback="energy_based")
            self.model = None

    def detect(self, audio_chunk: bytes) -> bool:
        """Check if the wake word is present in audio chunk."""
        if self.model is not None:
            return self._detect_ml(audio_chunk)
        return self._detect_energy(audio_chunk)

    def _detect_ml(self, audio_chunk: bytes) -> bool:
        """Use ML-based wake word detection."""
        try:
            import numpy as np
            audio = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            prediction = self.model.predict(audio)
            # Check if any wake word score exceeds sensitivity
            for key, score in prediction.items():
                if score >= self.sensitivity:
                    return True
            return False
        except Exception as e:
            logger.error("wake_word.ml_detection_failed", error=str(e))
            return False

    def _detect_energy(self, audio_chunk: bytes) -> bool:
        """Simple energy-based detection (fallback — always returns True for any speech).

        This is a placeholder. In production, use openWakeWord or Porcupine.
        For testing, you can use push-to-talk instead.
        """
        import numpy as np
        try:
            audio = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            energy = np.sqrt(np.mean(audio ** 2))
            # Very simple: if there's enough audio energy, treat it as potential wake word
            return energy > 500  # Threshold — adjust as needed
        except Exception:
            return False
