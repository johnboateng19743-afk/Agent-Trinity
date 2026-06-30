"""
Trinity Voice-First Daemon — Always listening, wake word activated.
Say "Trinity" to activate, then speak your question. Trinity responds by voice.
Runs in the background — no terminal window needed.
"""

import asyncio
import structlog
import numpy as np
import signal
import sys
import time

logger = structlog.get_logger(__name__)

# Audio settings
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
SILENCE_THRESHOLD = 300  # Below this = silence
SILENCE_DURATION = 1.5   # Seconds of silence to stop recording
MAX_RECORDING = 30.0     # Max recording length in seconds
WAKE_WORD_ENERGY_BOOST = 2.0  # Wake word needs louder speech


class VoiceDaemon:
    """Trinity voice-first daemon — always listening for wake word."""

    def __init__(self, config: dict, llm_router, tts_engine, stt_engine=None):
        self.config = config
        self.llm = llm_router
        self.tts = tts_engine
        self.stt = stt_engine
        self.running = False
        self.listening = True
        self.sd = None
        self.user_name = config.get("trinity", {}).get("user_name", "User")

    def _init_sounddevice(self):
        """Initialize sounddevice."""
        if self.sd is None:
            import sounddevice as sd
            self.sd = sd
            logger.info("voice.sounddevice_initialized")

    async def start(self):
        """Start the voice loop — always listening."""
        self.running = True
        self._init_sounddevice()

        logger.info("voice.daemon_started", user=self.user_name)
        print()
        print("  ══════════════════════════════════════════")
        print("  🜂  TRINITY — Voice Assistant Active")
        print("  ══════════════════════════════════════════")
        print()
        print(f"  Say \"Trinity\" to wake me up")
        print(f"  Then ask your question")
        print()
        print("  Press Ctrl+C to stop")
        print()

        # Greeting on startup
        await self._speak(f"Trinity online. Say my name to activate.")

        # Main loop
        try:
            while self.running:
                await self._listen_for_wake_word()
                if not self.running:
                    break
                await self._handle_command()
        except KeyboardInterrupt:
            pass
        finally:
            await self._speak("Trinity going offline. Goodbye.")
            self.running = False
            print("\n  🜂 Trinity stopped.")

    async def stop(self):
        """Stop the daemon."""
        self.running = False

    async def _listen_for_wake_word(self):
        """Listen continuously for the wake word 'Trinity'."""
        logger.info("voice.listening_for_wake_word")
        print("  🎧 Listening...", end="", flush=True)

        try:
            sd = self.sd
            buffer = []
            speech_detected = False

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
                while self.running:
                    chunk, _ = stream.read(CHUNK_SIZE)
                    audio_np = np.frombuffer(chunk, dtype=np.int16)
                    amplitude = np.abs(audio_np).mean()

                    if amplitude > SILENCE_THRESHOLD * WAKE_WORD_ENERGY_BOOST:
                        # Someone is speaking
                        if not speech_detected:
                            speech_detected = True
                        buffer.append(chunk.copy())

                        # Check if we have enough audio for wake word detection
                        if len(buffer) >= int(2.0 * SAMPLE_RATE / CHUNK_SIZE):
                            # We have ~2 seconds of speech
                            audio_data = np.concatenate(buffer)
                            is_wake = await self._detect_wake_word(audio_data.tobytes())

                            if is_wake:
                                print(" ✅ WAKE!")
                                return

                            # Not wake word, reset
                            buffer = []
                            speech_detected = False

                    elif speech_detected:
                        # Speech ended without wake word
                        buffer.append(chunk.copy())
                        silence_chunks = 0
                        while silence_chunks < int(0.5 * SAMPLE_RATE / CHUNK_SIZE):
                            chunk2, _ = stream.read(CHUNK_SIZE)
                            amp2 = np.abs(np.frombuffer(chunk2, dtype=np.int16)).mean()
                            if amp2 < SILENCE_THRESHOLD:
                                silence_chunks += 1
                            else:
                                buffer.append(chunk2.copy())
                                silence_chunks = 0

                        # Check the full speech
                        audio_data = np.concatenate(buffer)
                        is_wake = await self._detect_wake_word(audio_data.tobytes())
                        if is_wake:
                            print(" ✅ WAKE!")
                            return

                        buffer = []
                        speech_detected = False

                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error("voice.wake_word_error", error=str(e))

    async def _detect_wake_word(self, audio_data: bytes) -> bool:
        """Detect if the wake word 'Trinity' was spoken."""
        # Method 1: Use STT to transcribe and check for "trinity"
        if self.stt:
            try:
                text = await self.stt.transcribe(audio_data)
                if text and "trinity" in text.lower().strip():
                    logger.info("voice.wake_word_detected", transcription=text)
                    return True
            except Exception:
                pass

        # Method 2: Simple keyword matching from faster-whisper
        try:
            from faster_whisper import WhisperModel
            import tempfile
            import soundfile as sf

            # Transcribe with faster-whisper directly
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_np, language="en")
            text = " ".join([s.text for s in segments]).strip().lower()

            if "trinity" in text:
                logger.info("voice.wake_word_detected", transcription=text)
                return True
        except Exception as e:
            logger.debug("voice.wake_word_stt_failed", error=str(e))

        return False

    async def _handle_command(self):
        """After wake word — listen for the user's command and respond."""
        print("  🎤 Listening for command...")

        # Play a short acknowledgement sound
        await self._play_chime()

        # Record the user's speech
        audio_data = await self._record_speech()
        if not audio_data or len(audio_data) < 16000:
            print("  ❌ Didn't catch that. Say 'Trinity' again.")
            return

        # Transcribe
        print("  👂 Transcribing...")
        text = await self._transcribe(audio_data)
        if not text or not text.strip():
            print("  ❌ Couldn't understand. Try again.")
            return

        print(f"  🗣️  You: {text}")

        # Process with LLM
        print("  🧠 Thinking...")
        response = await self._think(text)

        # Speak the response
        print(f"  🔊 Trinity: {response[:100]}...")
        await self._speak(response)

    async def _record_speech(self) -> bytes:
        """Record speech until silence or max duration."""
        try:
            sd = self.sd
            frames = []
            silent_chunks = 0
            max_chunks = int(MAX_RECORDING * SAMPLE_RATE / CHUNK_SIZE)
            silence_chunks_needed = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK_SIZE)
            has_speech = False

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(CHUNK_SIZE)
                    frames.append(chunk)

                    amplitude = np.abs(np.frombuffer(chunk, dtype=np.int16)).mean()

                    if amplitude > SILENCE_THRESHOLD:
                        silent_chunks = 0
                        has_speech = True
                    else:
                        silent_chunks += 1

                    # Stop after silence following speech
                    if has_speech and silent_chunks >= silence_chunks_needed:
                        break

            if not has_speech:
                return b""

            audio_data = np.concatenate(frames)
            return audio_data.tobytes()

        except Exception as e:
            logger.error("voice.record_error", error=str(e))
            return b""

    async def _transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio to text using Whisper."""
        try:
            if self.stt:
                return await self.stt.transcribe(audio_data)

            # Fallback: direct faster-whisper
            from faster_whisper import WhisperModel
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_np, language="en")
            return " ".join([s.text for s in segments]).strip()

        except Exception as e:
            logger.error("voice.transcribe_error", error=str(e))
            return ""

    async def _think(self, text: str) -> str:
        """Send text to LLM and get response."""
        try:
            system_prompt = f"""You are Trinity, a personal voice AI assistant for {self.user_name}.
You are conversational, helpful, and concise. Keep responses under 3 sentences when possible since you speak out loud.
Be natural and friendly. You can help with research, file operations, questions, and task management."""

            response = await self.llm.chat(
                message=text,
                system_prompt=system_prompt,
            )
            return response

        except Exception as e:
            logger.error("voice.think_error", error=str(e))
            return "I'm having trouble thinking right now. Please try again."

    async def _speak(self, text: str):
        """Convert text to speech and play it."""
        if not text or not text.strip():
            return

        try:
            audio_data = await self.tts._generate_speech(text, "friendly")
            await self._play_audio(audio_data)
        except Exception as e:
            logger.error("voice.speak_error", error=str(e))

    async def _play_audio(self, audio_data: bytes):
        """Play audio data through speakers."""
        loop = asyncio.get_event_loop()

        def _play():
            import tempfile
            import subprocess
            from pathlib import Path

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-quiet", temp_path],
                    check=True, capture_output=True, timeout=30
                )
            except (FileNotFoundError, subprocess.SubprocessError):
                try:
                    subprocess.run(
                        ["cmd", "/c", "start", "/min", "", temp_path],
                        check=True, capture_output=True, timeout=10
                    )
                    time.sleep(3)
                except Exception:
                    logger.warning("voice.no_audio_player")
            finally:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception:
                    pass

        await loop.run_in_executor(None, _play)

    async def _play_chime(self):
        """Play a short acknowledgement chime."""
        try:
            # Generate a simple beep
            import struct
            sample_rate = 22050
            duration = 0.15
            frequency = 880
            num_samples = int(sample_rate * duration)

            samples = []
            for i in range(num_samples):
                t = i / sample_rate
                value = int(16000 * (1 - t / duration) * (1 if (int(t * frequency * 2) % 2 == 0) else -1))
                samples.append(struct.pack('<h', value))

            audio_bytes = b''.join(samples)

            # Save as WAV and play
            import tempfile
            import subprocess
            import wave

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                with wave.open(temp_path, 'w') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_bytes)

            loop = asyncio.get_event_loop()
            def _play():
                try:
                    subprocess.run(
                        ["ffplay", "-nodisp", "-autoexit", "-quiet", temp_path],
                        capture_output=True, timeout=5
                    )
                except Exception:
                    pass
                finally:
                    try:
                        from pathlib import Path
                        Path(temp_path).unlink(missing_ok=True)
                    except Exception:
                        pass

            await loop.run_in_executor(None, _play)

        except Exception:
            pass  # Chime is optional, don't fail if it doesn't work
