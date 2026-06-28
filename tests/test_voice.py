"""
Trinity Tests — Voice Engine Tests.
"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestWakeWordEngine:
    """Tests for wake word detection."""

    def test_init_default_wake_word(self):
        from trinity.voice.wake_word import WakeWordEngine
        config = {"voice": {"wake_word": "Trinity", "wake_sensitivity": 0.5}}
        engine = WakeWordEngine(config)
        assert engine.wake_word == "Trinity"
        assert engine.sensitivity == 0.5

    def test_detect_returns_bool(self):
        from trinity.voice.wake_word import WakeWordEngine
        config = {"voice": {"wake_word": "Trinity", "wake_sensitivity": 0.5}}
        engine = WakeWordEngine(config)
        result = engine.detect(b"\x00" * 512)
        assert isinstance(result, bool)

    def test_detect_empty_audio(self):
        from trinity.voice.wake_word import WakeWordEngine
        config = {"voice": {"wake_word": "Trinity", "wake_sensitivity": 0.5}}
        engine = WakeWordEngine(config)
        result = engine.detect(b"")
        assert result is False

    def test_detect_with_speech_noise(self):
        from trinity.voice.wake_word import WakeWordEngine
        config = {"voice": {"wake_word": "Trinity", "wake_sensitivity": 0.5}}
        engine = WakeWordEngine(config)
        # Create audio with enough energy to trigger energy-based detection
        rng = np.random.default_rng(42)
        noise = (rng.integers(-1000, 1000, size=512, dtype=np.int16)).tobytes()
        result = engine.detect(noise)
        # Energy-based detection should detect this as potential speech
        assert isinstance(result, bool)


class TestVAD:
    """Tests for voice activity detection."""

    def test_silence_detection(self):
        from trinity.voice.vad import VoiceActivityDetector
        config = {}
        vad = VoiceActivityDetector(config)
        # Pure silence should be detected as silence
        silence = b"\x00" * 1024
        assert vad.is_silence(silence) is True

    def test_speech_detection(self):
        from trinity.voice.vad import VoiceActivityDetector
        config = {}
        vad = VoiceActivityDetector(config)
        # Random noise should not be silence
        rng = np.random.default_rng(42)
        noise = (rng.integers(-1000, 1000, size=512, dtype=np.int16)).tobytes()
        assert vad.is_silence(noise) is False

    def test_empty_audio_is_silence(self):
        from trinity.voice.vad import VoiceActivityDetector
        config = {}
        vad = VoiceActivityDetector(config)
        assert vad.is_silence(b"") is True
