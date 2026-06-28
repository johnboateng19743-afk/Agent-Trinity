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
        except Exception as e:
            logger.warning("wake_word.model_failed", error=str(e), fallback="energy_based")
            self.model = None

    def detect(self, audio_chunk: bytes) -> bool:
        """Check if the wake word is present in audio chunk."""
        if not audio_chunk or len(audio_chunk) < 2:
            return False

        if self.model is not None:
            return self._detect_ml(audio_chunk)
        return self._detect_energy(audio_chunk)

    def _detect_ml(self, audio_chunk: bytes) -> bool:
        """Use ML-based wake word detection."""
        try:
            import numpy as np
            audio = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            prediction = self.model.predict(audio)
            for key, score in prediction.items():
                if score >= self.sensitivity:
                    return True
            return False
        except Exception as e:
            logger.error("wake_word.ml_detection_failed", error=str(e))
            return False

    def _detect_energy(self, audio_chunk: bytes) -> bool:
        """Simple energy-based detection (fallback).

        This is a placeholder. Use push-to-talk (Ctrl+Alt+Space) for reliable activation.
        """
        try:
            import numpy as np
            audio = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            if len(audio) == 0:
                return False
            energy = np.sqrt(np.mean(audio ** 2))
            return energy > 500
        except Exception:
            return False
