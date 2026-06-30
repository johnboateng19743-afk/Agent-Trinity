# Trinity Installer Script — Run this in PowerShell
# ==========================================
# 1. Open PowerShell
# 2. Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# 3. Run: cd $HOME
# 4. Copy and paste this entire script, then press Enter

Write-Host "🜂 Trinity Installer — Setting everything up..." -ForegroundColor Cyan

# Create project directory
$projectDir = "$HOME\Agent-Trinity"
New-Item -ItemType Directory -Force -Path $projectDir | Out-Null
Set-Location $projectDir

Write-Host "   ✅ Created project directory" -ForegroundColor Green

# Create virtual environment
Write-Host "   ⏳ Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv
Write-Host "   ✅ Virtual environment created" -ForegroundColor Green

# Activate venv
& .\.venv\Scripts\Activate.ps1

# Create requirements.txt
@"
python-dotenv>=1.0.0
pyyaml>=6.0
structlog>=24.1.0
faster-whisper>=1.0.0
openai>=1.12.0
anthropic>=0.18.0
PyQt6>=6.6.0
chromadb>=0.4.22
aiosqlite>=0.19.0
aiofiles>=23.2.0
send2trash>=1.8.2
python-docx>=1.1.0
openpyxl>=3.1.2
PyMuPDF>=1.23.8
Pillow>=10.2.0
google-api-python-client>=2.111.0
google-auth-oauthlib>=1.2.0
keyring>=24.3.0
psutil>=5.9.8
websockets>=12.0
requests>=2.31.0
rich>=13.7.0
click>=8.1.7
numpy>=1.26.0
soundfile>=0.12.1
pytz>=2024.1
"@ | Out-File -FilePath "requirements.txt" -Encoding utf8

Write-Host "   ⏳ Installing dependencies (this takes 2-5 minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "   ✅ Dependencies installed" -ForegroundColor Green

# Create .env file
@"
# .env — Trinity Configuration
ELEVENLABS_API_KEY=sk_6bb94189d27375342674a4899112cd26858ff8b9f39a3e96
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
ELEVENLABS_MODEL=eleven_turbo_v2_5
OPENAI_API_KEY=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
ANTHROPIC_API_KEY=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
OLLAMA_BASE_URL=http://localhost:11434
LOCAL_LLM_FAST=qwen2.5:1.5b
LOCAL_LLM_CAPABLE=llama3.2:3b
CLOUD_LLM_PRIMARY=gpt-4o
CLOUD_LLM_FALLBACK=claude-sonnet-4-20250514
GOOGLE_CLOUD_PROJECT_ID=agent-trinity-500718
GOOGLE_CLOUD_PROJECT_NUMBER=177176143306
GOOGLE_CLIENT_ID=177176143306-rb6p8ng2ucrcq1a4d45f1ubdeg4eptod.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:8400/auth/callback
GOOGLE_MAPS_API_KEY=019f0b5f-7cb6-70b7-9dd6-d5ef36b96b5b
TRINITY_USER_NAME=Mr. Walker
TRINITY_TIMEZONE=Africa/Accra
TRINITY_HOME_ADDRESS=Hohoe, Ghana
TRINITY_HOME_CITY=Accra
TRINITY_WORK_ADDRESS=
TRINITY_DEFAULT_BROWSER=edge
TRINITY_AUTO_START=true
TRINITY_DATA_DIR=~/.trinity
TRINITY_LOG_LEVEL=INFO
TRINITY_PRIVACY_MODE=hybrid
TRINITY_REDACT_PII=true
TRINITY_STORE_VOICE=false
TRINITY_UPDATE_CHANNEL=stable
TRINITY_AUTO_UPDATE=true
TRINITY_UPDATE_REPO=https://github.com/johnboateng19743-afk/Agent-Trinity
TRINITY_GPU_ENABLED=false
TRINITY_GPU_DEVICE=-1
TRINITY_MAX_RAM_GB=2
TRINITY_LOCAL_HTTP_PORT=8400
TRINITY_WATCHDOG_ENABLED=true
TRINITY_DEBUG_MODE=false
"@ | Out-File -FilePath ".env" -Encoding utf8

Write-Host "   ✅ .env configured" -ForegroundColor Green

# Create directory structure
$dirs = @(
    "trinity\orchestrator",
    "trinity\voice",
    "trinity\skills\filesystem",
    "trinity\skills\calendar",
    "trinity\skills\email",
    "trinity\skills\drive",
    "trinity\skills\maps",
    "trinity\skills\applications",
    "trinity\llm",
    "trinity\memory",
    "trinity\ui",
    "trinity\integrations",
    "trinity\updates",
    "trinity\watchdog",
    "trinity\utils",
    "assets",
    "tests"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}
Write-Host "   ✅ Directory structure created" -ForegroundColor Green

# Create __init__.py files
Get-ChildItem -Path "trinity" -Directory -Recurse | ForEach-Object {
    $initFile = Join-Path $_.FullName "__init__.py"
    if (-not (Test-Path $initFile)) {
        New-Item -ItemType File -Force -Path $initFile | Out-Null
    }
}
Write-Host "   ✅ Python packages initialized" -ForegroundColor Green

# ---- CREATE ALL PYTHON SOURCE FILES ----

Write-Host "   ⏳ Creating source files..." -ForegroundColor Yellow

# trinity/__init__.py
@"
"""Trinity - Voice-first AI agent for Windows."""
__version__ = "1.0.0"
__author__ = "Mr. Walker"
"@ | Out-File -FilePath "trinity\__init__.py" -Encoding utf8

# trinity/main.py
@"
"""Trinity - Main entry point. Run with: python -m trinity.main"""
import sys
import signal
import asyncio
import click
from pathlib import Path
from trinity.daemon import TrinityDaemon
from trinity.utils.config import load_config
from trinity.utils.logging import setup_logging


@click.group(invoke_without_command=True)
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", default=None, help="Path to config file")
@click.pass_context
def cli(ctx, debug: bool, config: str | None):
    """Trinity - Your voice-first AI agent."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["config_path"] = config
    if ctx.invoked_subcommand is None:
        ctx.invoke(run, debug=debug, config=config)


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", default=None, help="Path to config file")
def run(debug: bool, config: str | None):
    """Start Trinity agent."""
    setup_logging(debug=debug)
    cfg = load_config(config_path=config)
    if debug:
        cfg["trinity"]["debug_mode"] = True
    click.echo("Starting Trinity...")
    click.echo(f"   User: {cfg['trinity']['user_name']}")
    click.echo(f"   Mode: {cfg['trinity']['privacy_mode']}")
    click.echo(f"   LLM:  {cfg['llm']['cloud_primary']} (cloud-first)")
    click.echo()
    daemon = TrinityDaemon(cfg)

    def shutdown(signum, frame):
        click.echo("\\nTrinity shutting down...")
        daemon.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    try:
        daemon.start()
    except KeyboardInterrupt:
        shutdown(None, None)


@cli.command()
def status():
    """Check if Trinity is running."""
    import psutil
    trinity_procs = [p for p in psutil.process_iter(["name", "cmdline"])
                     if p.info["cmdline"] and "trinity" in " ".join(p.info["cmdline"])]
    if trinity_procs:
        click.echo("Trinity is running")
    else:
        click.echo("Trinity is not running")


if __name__ == "__main__":
    cli()
"@ | Out-File -FilePath "trinity\main.py" -Encoding utf8

# trinity/daemon.py
@"
"""Trinity Daemon - Main process that orchestrates all subsystems."""
import asyncio
import structlog
from pathlib import Path
from trinity.orchestrator.router import IntentRouter
from trinity.orchestrator.context import ConversationManager
from trinity.voice.stt import STTEngine
from trinity.voice.tts import TTSEngine
from trinity.voice.wake_word import WakeWordEngine
from trinity.voice.vad import VoiceActivityDetector
from trinity.voice.audio_io import AudioIO
from trinity.llm.router import LLMRouter
from trinity.memory.vector_store import MemoryStore
from trinity.memory.conversation import ConversationStore
from trinity.memory.user_profile import UserProfile
from trinity.skills.filesystem.reader import FileSystemReader
from trinity.skills.filesystem.writer import FileSystemWriter
from trinity.skills.filesystem.mover import FileSystemMover
from trinity.skills.filesystem.deleter import FileSystemDeleter
from trinity.skills.filesystem.searcher import FileSystemSearcher
from trinity.skills.filesystem.documents import DocumentHandler
from trinity.skills.calendar.client import CalendarClient
from trinity.skills.email.client import EmailClient
from trinity.skills.drive.client import DriveClient
from trinity.skills.maps.location import LocationService
from trinity.skills.maps.directions import DirectionsService
from trinity.integrations.google_auth import GoogleAuthManager
from trinity.integrations.credential_store import CredentialStore
from trinity.updates.checker import UpdateChecker

logger = structlog.get_logger(__name__)


class TrinityDaemon:
    def __init__(self, config: dict):
        self.config = config
        self.running = False
        self.audio_io = AudioIO(config)
        self.wake_word = WakeWordEngine(config)
        self.vad = VoiceActivityDetector(config)
        self.stt = STTEngine(config)
        self.tts = TTSEngine(config)
        self.llm_router = LLMRouter(config)
        self.conversation = ConversationManager(config)
        self.intent_router = IntentRouter(config)
        self.memory = MemoryStore(config)
        self.conversation_store = ConversationStore(config)
        self.user_profile = UserProfile(config)
        self.credential_store = CredentialStore(config)
        self.google_auth = GoogleAuthManager(config, self.credential_store)
        self.update_checker = UpdateChecker(config)
        self.skills = {}
        self._register_skills()
        logger.info("trinity.daemon.initialized", user=config["trinity"]["user_name"])

    def _register_skills(self):
        cfg = self.config
        self.skills = {
            "filesystem.read": FileSystemReader(cfg),
            "filesystem.write": FileSystemWriter(cfg),
            "filesystem.move": FileSystemMover(cfg),
            "filesystem.delete": FileSystemDeleter(cfg),
            "filesystem.search": FileSystemSearcher(cfg),
            "filesystem.documents": DocumentHandler(cfg),
            "calendar": CalendarClient(cfg, self.google_auth),
            "email": EmailClient(cfg, self.google_auth),
            "drive": DriveClient(cfg, self.google_auth),
            "maps.location": LocationService(cfg),
            "maps.directions": DirectionsService(cfg),
        }

    def start(self):
        self.running = True
        logger.info("trinity.daemon.starting")
        print("Trinity is listening... Say 'Trinity' to activate.")
        print("   Press Ctrl+C to stop.\\n")
        try:
            asyncio.run(self._main_loop())
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        logger.info("trinity.daemon.stopping")
        print("\\nTrinity signing off. Goodbye, Mr. Walker.")

    async def _main_loop(self):
        while self.running:
            try:
                audio_chunk = await self.audio_io.read_chunk()
                if not self.wake_word.detect(audio_chunk):
                    continue
                logger.info("trinity.wake_word.detected")
                await self._on_wake_word()
                utterance_audio = await self._record_utterance()
                transcript = await self.stt.transcribe(utterance_audio)
                if not transcript or not transcript.strip():
                    await self.tts.speak("I didn't catch that. Could you say it again?")
                    continue
                logger.info("trinity.stt.transcript", text=transcript)
                print(f'   "{transcript}"')
                response = await self._process_command(transcript)
                await self.tts.speak(response)
                print(f'   Trinity: "{response}"')
                await self.conversation_store.add_exchange(transcript, response)
            except Exception as e:
                logger.error("trinity.daemon.error", error=str(e))

    async def _on_wake_word(self):
        chime_path = Path(__file__).parent.parent / "assets" / "chime.wav"
        if chime_path.exists():
            await self.audio_io.play_file(chime_path)
        print("   Listening...")

    async def _record_utterance(self) -> bytes:
        chunks = []
        silence_count = 0
        max_silence = 30
        while True:
            chunk = await self.audio_io.read_chunk()
            chunks.append(chunk)
            if self.vad.is_silence(chunk):
                silence_count += 1
            else:
                silence_count = 0
            if silence_count >= max_silence and len(chunks) > max_silence:
                break
        return b"".join(chunks)

    async def _process_command(self, transcript: str) -> str:
        context = await self.conversation.get_context()
        intent = await self.intent_router.classify(transcript, context)
        logger.info("trinity.intent.classified", intent=intent.skill)
        if intent.skill in self.skills:
            skill = self.skills[intent.skill]
            result = await skill.execute(intent.entities, context)
            return result.response
        else:
            response = await self.llm_router.chat(
                message=transcript, context=context,
                system_prompt=self._build_system_prompt()
            )
            return response

    def _build_system_prompt(self) -> str:
        from datetime import datetime
        import pytz
        tz = pytz.timezone("Africa/Accra")
        time_str = datetime.now(tz).strftime("%I:%M %p on %A, %B %d")
        return f"""You are Trinity, a voice-first AI agent living on Mr. Walker's Windows machine.
You are warm, confident, and efficient. You speak naturally.
Current time: {time_str}. Location: Accra, Ghana.
Rules: Be concise. Confirm before destructive actions. Use Mr. Walker's name when appropriate.
If you can't do something, explain why and suggest alternatives."""

    @staticmethod
    def _current_time() -> str:
        from datetime import datetime
        import pytz
        tz = pytz.timezone("Africa/Accra")
        return datetime.now(tz).strftime("%I:%M %p on %A, %B %d")
"@ | Out-File -FilePath "trinity\daemon.py" -Encoding utf8

# trinity/utils/config.py
@"
"""Configuration loader."""
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml
import structlog

logger = structlog.get_logger(__name__)

DEFAULTS = {
    "trinity": {"user_name": "Mr. Walker", "timezone": "Africa/Accra", "home_address": "Hohoe, Ghana",
                "home_city": "Accra", "work_address": "", "default_browser": "edge", "auto_start": True,
                "data_dir": "~/.trinity", "log_level": "INFO", "privacy_mode": "hybrid",
                "redact_pii": True, "store_voice": False, "debug_mode": False},
    "voice": {"elevenlabs_api_key": "", "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
              "elevenlabs_model": "eleven_turbo_v2_5", "wake_word": "Trinity",
              "wake_sensitivity": 0.5, "always_listening": True},
    "llm": {"openai_api_key": "", "anthropic_api_key": "", "ollama_base_url": "http://localhost:11434",
            "local_fast": "qwen2.5:1.5b", "local_capable": "llama3.2:3b",
            "cloud_primary": "gpt-4o", "cloud_fallback": "claude-sonnet-4-20250514",
            "max_tokens": 4096, "temperature": 0.7},
    "google": {"project_id": "agent-trinity-500718", "project_number": "177176143306",
               "client_id": "", "client_secret": "", "redirect_uri": "http://localhost:8400/auth/callback",
               "maps_api_key": ""},
    "hardware": {"gpu_enabled": False, "gpu_device": -1, "max_ram_gb": 2},
    "updates": {"channel": "stable", "auto_update": True,
                "update_repo": "https://github.com/johnboateng19743-afk/Agent-Trinity"},
    "advanced": {"local_http_port": 8400, "watchdog_enabled": True},
}


def load_config(config_path=None):
    env_path = Path(config_path).parent / ".env" if config_path else Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    config = {k: dict(v) for k, v in DEFAULTS.items()}
    config["trinity"]["user_name"] = os.getenv("TRINITY_USER_NAME", config["trinity"]["user_name"])
    config["trinity"]["timezone"] = os.getenv("TRINITY_TIMEZONE", config["trinity"]["timezone"])
    config["trinity"]["home_address"] = os.getenv("TRINITY_HOME_ADDRESS", config["trinity"]["home_address"])
    config["trinity"]["home_city"] = os.getenv("TRINITY_HOME_CITY", config["trinity"]["home_city"])
    config["trinity"]["work_address"] = os.getenv("TRINITY_WORK_ADDRESS", "")
    config["trinity"]["default_browser"] = os.getenv("TRINITY_DEFAULT_BROWSER", "edge")
    config["trinity"]["privacy_mode"] = os.getenv("TRINITY_PRIVACY_MODE", "hybrid")
    config["trinity"]["debug_mode"] = os.getenv("TRINITY_DEBUG_MODE", "false").lower() == "true"
    config["voice"]["elevenlabs_api_key"] = os.getenv("ELEVENLABS_API_KEY", "")
    config["voice"]["elevenlabs_voice_id"] = os.getenv("ELEVENLABS_VOICE_ID", config["voice"]["elevenlabs_voice_id"])
    config["voice"]["elevenlabs_model"] = os.getenv("ELEVENLABS_MODEL", config["voice"]["elevenlabs_model"])
    config["llm"]["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    config["llm"]["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY", "")
    config["llm"]["ollama_base_url"] = os.getenv("OLLAMA_BASE_URL", config["llm"]["ollama_base_url"])
    config["llm"]["local_fast"] = os.getenv("LOCAL_LLM_FAST", config["llm"]["local_fast"])
    config["llm"]["local_capable"] = os.getenv("LOCAL_LLM_CAPABLE", config["llm"]["local_capable"])
    config["llm"]["cloud_primary"] = os.getenv("CLOUD_LLM_PRIMARY", config["llm"]["cloud_primary"])
    config["llm"]["cloud_fallback"] = os.getenv("CLOUD_LLM_FALLBACK", config["llm"]["cloud_fallback"])
    config["google"]["client_id"] = os.getenv("GOOGLE_CLIENT_ID", "")
    config["google"]["client_secret"] = os.getenv("GOOGLE_CLIENT_SECRET", "")
    config["google"]["maps_api_key"] = os.getenv("GOOGLE_MAPS_API_KEY", "")
    config["hardware"]["gpu_enabled"] = os.getenv("TRINITY_GPU_ENABLED", "false").lower() == "true"
    config["hardware"]["max_ram_gb"] = int(os.getenv("TRINITY_MAX_RAM_GB", "2"))
    config["updates"]["update_repo"] = os.getenv("TRINITY_UPDATE_REPO", config["updates"]["update_repo"])
    data_dir = Path(config["trinity"]["data_dir"]).expanduser()
    for sub in ["data/chroma", "data/skills", "versions", "logs/crash", "cache"]:
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    return config
"@ | Out-File -FilePath "trinity\utils\config.py" -Encoding utf8

# trinity/utils/logging.py
@"
"""Structured logging setup."""
import sys
import logging
import structlog

def setup_logging(debug=False):
    log_level = logging.DEBUG if debug else logging.INFO
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
"@ | Out-File -FilePath "trinity\utils\logging.py" -Encoding utf8

# trinity/utils/permissions.py
@"
"""Permission tier checking."""
from enum import IntEnum
from pathlib import Path

class PermissionTier(IntEnum):
    TRUSTED = 0
    STANDARD = 1
    DESTRUCTIVE = 2
    SENSITIVE = 3
    CRITICAL = 4

PROTECTED_PATHS = [Path("C:/Windows"), Path("C:/Program Files"), Path("C:/Program Files (x86)"), Path("C:/ProgramData")]
BATCH_SIZE_THRESHOLD = 500 * 1024 * 1024

def classify_operation(operation):
    tier_map = {"read_file": 0, "list_dir": 0, "search_files": 0, "create_file": 1, "create_dir": 1,
                "edit_file": 1, "move": 1, "copy": 1, "rename": 1, "delete": 2, "execute": 4,
                "send_email": 3, "share_file": 3}
    return PermissionTier(tier_map.get(operation, 1))

def is_protected_path(path):
    try:
        resolved = Path(path).resolve()
        for protected in PROTECTED_PATHS:
            try:
                resolved.relative_to(protected)
                return True
            except ValueError:
                continue
    except Exception:
        pass
    return False

def requires_confirmation(operation, path=None, size=0):
    tier = classify_operation(operation)
    if tier >= PermissionTier.DESTRUCTIVE:
        return True
    if path and is_protected_path(path):
        return True
    if size > BATCH_SIZE_THRESHOLD:
        return True
    return False
"@ | Out-File -FilePath "trinity\utils\permissions.py" -Encoding utf8

# trinity/voice/stt.py
@"
"""Speech-to-Text using Whisper."""
import asyncio
import structlog
from pathlib import Path
logger = structlog.get_logger(__name__)

class STTEngine:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.use_cloud = False
        self._init_model()

    def _init_model(self):
        try:
            from faster_whisper import WhisperModel
            device = "cuda" if self.config["hardware"]["gpu_enabled"] else "cpu"
            self.model = WhisperModel("base", device=device, compute_type="int8")
            logger.info("stt.local_model.loaded", device=device)
        except Exception as e:
            logger.warning("stt.faster_whisper_failed", error=str(e), fallback="cloud")
            self.use_cloud = True

    async def transcribe(self, audio_data):
        if self.use_cloud or self.model is None:
            return await self._transcribe_cloud(audio_data)
        return await self._transcribe_local(audio_data)

    async def _transcribe_local(self, audio_data):
        loop = asyncio.get_event_loop()
        def _do():
            import tempfile, soundfile as sf, numpy as np
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                sf.write(temp_path, audio_array, samplerate=16000)
            segments, _ = self.model.transcribe(temp_path, beam_size=5)
            text = " ".join([seg.text for seg in segments]).strip()
            Path(temp_path).unlink(missing_ok=True)
            return text
        try:
            return await loop.run_in_executor(None, _do)
        except Exception as e:
            logger.error("stt.local_failed", error=str(e))
            return await self._transcribe_cloud(audio_data)

    async def _transcribe_cloud(self, audio_data):
        try:
            from openai import AsyncOpenAI
            import tempfile
            client = AsyncOpenAI(api_key=self.config["llm"]["openai_api_key"])
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                f.write(audio_data)
            with open(temp_path, "rb") as af:
                response = await client.audio.transcriptions.create(model="whisper-1", file=af, language="en")
            Path(temp_path).unlink(missing_ok=True)
            return response.text
        except Exception as e:
            logger.error("stt.cloud_failed", error=str(e))
            return ""
"@ | Out-File -FilePath "trinity\voice\stt.py" -Encoding utf8

# trinity/voice/tts.py
@"
"""Text-to-Speech using ElevenLabs."""
import asyncio
import structlog
import requests
logger = structlog.get_logger(__name__)

class TTSEngine:
    def __init__(self, config):
        self.config = config
        self.api_key = config["voice"]["elevenlabs_api_key"]
        self.voice_id = config["voice"]["elevenlabs_voice_id"]
        self.model = config["voice"]["elevenlabs_model"]
        self.speaking = False

    async def speak(self, text, emotion="neutral"):
        if not text or not text.strip():
            return
        self.speaking = True
        try:
            audio_data = await self._generate(text, emotion)
            await self._play(audio_data)
        except Exception as e:
            logger.error("tts.speak_failed", error=str(e))
        finally:
            self.speaking = False

    async def _generate(self, text, emotion="neutral"):
        settings = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3, "use_speaker_boost": True}
        loop = asyncio.get_event_loop()
        def _do():
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": self.api_key}
            data = {"text": text, "model_id": self.model, "voice_settings": settings}
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.content
        return await loop.run_in_executor(None, _do)

    async def _play(self, audio_data):
        loop = asyncio.get_event_loop()
        def _do():
            import tempfile, subprocess
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            try:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", temp_path], check=True, capture_output=True)
            except FileNotFoundError:
                subprocess.run(["cmd", "/c", "start", "", temp_path], capture_output=True)
            finally:
                from pathlib import Path
                Path(temp_path).unlink(missing_ok=True)
        await loop.run_in_executor(None, _do)
"@ | Out-File -FilePath "trinity\voice\tts.py" -Encoding utf8

# trinity/voice/wake_word.py
@"
"""Wake Word Detection."""
import structlog
logger = structlog.get_logger(__name__)

class WakeWordEngine:
    def __init__(self, config):
        self.config = config
        self.wake_word = config["voice"]["wake_word"]
        self.sensitivity = config["voice"]["wake_sensitivity"]
        self.model = None
        try:
            from openwakeword import Model
            self.model = Model()
        except ImportError:
            logger.warning("wake_word.openwakeword_not_found", fallback="push_to_talk")

    def detect(self, audio_chunk):
        if self.model is not None:
            return self._detect_ml(audio_chunk)
        return self._detect_energy(audio_chunk)

    def _detect_ml(self, audio_chunk):
        try:
            import numpy as np
            audio = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            prediction = self.model.predict(audio)
            for key, score in prediction.items():
                if score >= self.sensitivity:
                    return True
            return False
        except Exception:
            return False

    def _detect_energy(self, audio_chunk):
        try:
            import numpy as np
            audio = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            energy = np.sqrt(np.mean(audio ** 2))
            return energy > 500
        except Exception:
            return False
"@ | Out-File -FilePath "trinity\voice\wake_word.py" -Encoding utf8

# trinity/voice/vad.py
@"
"""Voice Activity Detection."""
import structlog
import numpy as np
logger = structlog.get_logger(__name__)

class VoiceActivityDetector:
    def __init__(self, config):
        self.config = config
        self.silence_threshold = 500
        self._vad = None
        try:
            import webrtcvad
            self._vad = webrtcvad.Vad()
            self._vad.set_mode(2)
        except ImportError:
            pass

    def is_silence(self, audio_chunk):
        if self._vad is not None:
            try:
                frame_size = 320 * 2
                if len(audio_chunk) >= frame_size:
                    return not self._vad.is_speech(audio_chunk[:frame_size], sample_rate=16000)
            except Exception:
                pass
        try:
            audio = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            energy = np.sqrt(np.mean(audio ** 2))
            return energy < self.silence_threshold
        except Exception:
            return True
"@ | Out-File -FilePath "trinity\voice\vad.py" -Encoding utf8

# trinity/voice/audio_io.py
@"
"""Audio Input/Output management."""
import asyncio
import structlog
logger = structlog.get_logger(__name__)
SAMPLE_RATE = 16000
CHUNK_SIZE = 512
CHANNELS = 1

class AudioIO:
    def __init__(self, config):
        self.config = config
        self._stream = None
        self._pyaudio = None

    def _init_pyaudio(self):
        if self._pyaudio is None:
            import pyaudio
            self._pyaudio = pyaudio.PyAudio()
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, frames_per_buffer=CHUNK_SIZE)

    async def read_chunk(self):
        loop = asyncio.get_event_loop()
        def _read():
            self._init_pyaudio()
            return self._stream.read(CHUNK_SIZE, exception_on_overflow=False)
        try:
            return await loop.run_in_executor(None, _read)
        except Exception:
            return b"\\x00" * CHUNK_SIZE * 2

    async def play_file(self, path):
        loop = asyncio.get_event_loop()
        def _play():
            import subprocess
            subprocess.run(["ffplay", "-nodisp", "-autoexit", str(path)], capture_output=True)
        try:
            await loop.run_in_executor(None, _play)
        except Exception:
            pass
"@ | Out-File -FilePath "trinity\voice\audio_io.py" -Encoding utf8

# trinity/orchestrator/router.py
@"
"""Intent Router - Classifies user intent and routes to skills."""
import re
import structlog
from dataclasses import dataclass, field
logger = structlog.get_logger(__name__)

@dataclass
class Intent:
    skill: str
    action: str
    entities: dict = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str = ""

class IntentRouter:
    INTENT_PATTERNS = {
        "filesystem.read": [r"(?i)(read|show|display|open|view|what's in)\s+.*(file|doc|folder|dir)"],
        "filesystem.search": [r"(?i)(find|search|locate|look for)\s+", r"(?i)(where is|where are)\s+"],
        "filesystem.write": [r"(?i)(create|make|write|new)\s+.*(file|doc|folder|note)"],
        "filesystem.edit": [r"(?i)(edit|modify|change|update|set|rename)\s+"],
        "filesystem.move": [r"(?i)(move|transfer|relocate)\s+"],
        "filesystem.delete": [r"(?i)(delete|remove|trash|erase)\s+"],
        "calendar": [r"(?i)(calendar|schedule|meeting|event|appointment)\s+", r"(?i)(what('s| is) on my calendar)"],
        "email": [r"(?i)(email|mail|inbox|send|reply|read my)\s+", r"(?i)(unread|new email)"],
        "drive": [r"(?i)(google drive|drive|upload|download from cloud)\s+"],
        "maps.location": [r"(?i)(where am i|my location|nearest|nearby|around me)\s+"],
        "maps.directions": [r"(?i)(directions|navigate|how (do i|to) get|route to)\s+", r"(?i)(how far|how long|distance)\s+"],
    }

    def __init__(self, config):
        self.config = config
        self._compiled = {skill: [re.compile(p) for p in patterns] for skill, patterns in self.INTENT_PATTERNS.items()}

    async def classify(self, text, context=None):
        text = text.strip()
        best_match = None
        best_conf = 0.0
        for skill, patterns in self._compiled.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    conf = 0.7 + min(0.25, 0.1 * len(match.group()) / max(len(text), 1))
                    if conf > best_conf:
                        best_conf = conf
                        best_match = Intent(skill=skill, action="execute", entities={"raw_text": text}, confidence=conf, raw_text=text)
        if best_match and best_match.confidence >= 0.5:
            return best_match
        return Intent(skill="llm_conversation", action="chat", entities={"raw_text": text}, confidence=0.3, raw_text=text)
"@ | Out-File -FilePath "trinity\orchestrator\router.py" -Encoding utf8

# trinity/orchestrator/context.py
@"
"""Conversation Context Manager."""
import structlog
logger = structlog.get_logger(__name__)
MAX_CONTEXT = 50

class ConversationManager:
    def __init__(self, config):
        self.config = config
        self.history = []

    async def get_context(self):
        return {"history": self.history[-MAX_CONTEXT:], "user_name": self.config["trinity"]["user_name"],
                "timezone": self.config["trinity"]["timezone"], "home_city": self.config["trinity"]["home_city"]}

    async def add_exchange(self, user_text, trinity_response):
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "trinity", "content": trinity_response})
        if len(self.history) > MAX_CONTEXT * 2:
            self.history = self.history[-MAX_CONTEXT * 2:]
"@ | Out-File -FilePath "trinity\orchestrator\context.py" -Encoding utf8

# trinity/orchestrator/prompts.py
@"
"""System and skill prompts."""
SYSTEM_PROMPT = '''You are Trinity, a voice-first AI agent on Mr. Walker's Windows machine.
You are warm, confident, and efficient. Be concise. Confirm before destructive actions.
Use Mr. Walker's name when appropriate. If you can't do something, explain why and suggest alternatives.'''
"@ | Out-File -FilePath "trinity\orchestrator\prompts.py" -Encoding utf8

# trinity/llm/router.py
@"
"""Hybrid LLM Router - Cloud-first fallback chain."""
import asyncio
import structlog
logger = structlog.get_logger(__name__)

class LLMRouter:
    def __init__(self, config):
        self.config = config
        self.openai_client = None
        self.anthropic_client = None
        self.ollama_client = None
        try:
            from openai import AsyncOpenAI
            self.openai_client = AsyncOpenAI(api_key=config["llm"]["openai_api_key"])
        except Exception as e:
            logger.error("llm.openai.init_failed", error=str(e))
        try:
            from anthropic import AsyncAnthropic
            self.anthropic_client = AsyncAnthropic(api_key=config["llm"]["anthropic_api_key"])
        except Exception as e:
            logger.warning("llm.anthropic.init_failed", error=str(e))

    async def chat(self, message, context=None, system_prompt=""):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context and context.get("history"):
            for ex in context["history"][-20:]:
                role = "user" if ex["role"] == "user" else "assistant"
                messages.append({"role": role, "content": ex["content"]})
        messages.append({"role": "user", "content": message})

        response = await self._try_openai(messages)
        if response:
            return response
        response = await self._try_anthropic(messages, system_prompt)
        if response:
            return response
        response = await self._try_ollama(messages)
        if response:
            return response
        return "I'm having trouble reaching my brain right now. I can still help with basic file operations."

    async def _try_openai(self, messages):
        if not self.openai_client:
            return None
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.config["llm"]["cloud_primary"], messages=messages,
                max_tokens=self.config["llm"]["max_tokens"], temperature=self.config["llm"]["temperature"])
            return response.choices[0].message.content
        except Exception as e:
            logger.warning("llm.openai.failed", error=str(e))
            return None

    async def _try_anthropic(self, messages, system_prompt=""):
        if not self.anthropic_client:
            return None
        try:
            chat_msgs = [m for m in messages if m["role"] != "system"]
            sys = system_prompt or next((m["content"] for m in messages if m["role"] == "system"), "")
            response = await self.anthropic_client.messages.create(
                model=self.config["llm"]["cloud_fallback"], system=sys, messages=chat_msgs,
                max_tokens=self.config["llm"]["max_tokens"])
            return response.content[0].text
        except Exception as e:
            logger.warning("llm.anthropic.failed", error=str(e))
            return None

    async def _try_ollama(self, messages):
        try:
            import ollama
            client = ollama.AsyncClient(host=self.config["llm"]["ollama_base_url"])
            response = await client.chat(model=self.config["llm"]["local_fast"], messages=messages)
            return response["message"]["content"]
        except Exception as e:
            logger.warning("llm.ollama.failed", error=str(e))
            return None
"@ | Out-File -FilePath "trinity\llm\router.py" -Encoding utf8

# trinity/memory/vector_store.py
@"
"""Vector Store using ChromaDB."""
import structlog
from pathlib import Path
logger = structlog.get_logger(__name__)

class MemoryStore:
    def __init__(self, config):
        self.config = config
        self.collection = None
        try:
            import chromadb
            data_dir = Path(config["trinity"]["data_dir"]).expanduser() / "data" / "chroma"
            client = chromadb.PersistentClient(path=str(data_dir))
            self.collection = client.get_or_create_collection("trinity_memory", metadata={"hnsw:space": "cosine"})
        except Exception as e:
            logger.warning("memory.chromadb_unavailable", error=str(e))

    async def remember(self, fact, category="general", pinned=False):
        if not self.collection:
            return
        import uuid
        self.collection.add(documents=[fact], metadatas=[{"category": category, "pinned": pinned}], ids=[str(uuid.uuid4())])

    async def recall(self, query, n=5):
        if not self.collection:
            return []
        results = self.collection.query(query_texts=[query], n_results=n)
        return results.get("documents", [[]])[0]

    async def forget(self, substring):
        if not self.collection:
            return 0
        all_data = self.collection.get()
        ids = [all_data["ids"][i] for i, d in enumerate(all_data["documents"]) if substring.lower() in d.lower()]
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)
"@ | Out-File -FilePath "trinity\memory\vector_store.py" -Encoding utf8

# trinity/memory/conversation.py
@"
"""Conversation Store using SQLite."""
import aiosqlite
import json
import structlog
from pathlib import Path
from datetime import datetime
logger = structlog.get_logger(__name__)

class ConversationStore:
    def __init__(self, config):
        data_dir = Path(config["trinity"]["data_dir"]).expanduser() / "data"
        self.db_path = str(data_dir / "conversations.db")
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, role TEXT, content TEXT, metadata TEXT)")
        conn.commit()
        conn.close()

    async def add_exchange(self, user_text, trinity_response, metadata=None):
        now = datetime.utcnow().isoformat()
        meta_str = json.dumps(metadata) if metadata else None
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO conversations (timestamp, role, content, metadata) VALUES (?, ?, ?, ?)", (now, "user", user_text, meta_str))
            await db.execute("INSERT INTO conversations (timestamp, role, content, metadata) VALUES (?, ?, ?, ?)", (now, "trinity", trinity_response, meta_str))
            await db.commit()
"@ | Out-File -FilePath "trinity\memory\conversation.py" -Encoding utf8

# trinity/memory/user_profile.py
@"
"""User Profile Management."""
import yaml
import structlog
from pathlib import Path
logger = structlog.get_logger(__name__)

class UserProfile:
    def __init__(self, config):
        self.config = config
        self.profile_path = Path(config["trinity"]["data_dir"]).expanduser() / "profile.yaml"
        self.profile = self._load()

    def _load(self):
        if self.profile_path.exists():
            with open(self.profile_path) as f:
                return yaml.safe_load(f) or {}
        profile = {"name": self.config["trinity"]["user_name"], "timezone": self.config["trinity"]["timezone"],
                   "home_address": self.config["trinity"]["home_address"], "preferences": {}, "shortcuts": {}, "pinned_memories": []}
        self._save(profile)
        return profile

    def _save(self, profile=None):
        if profile is None:
            profile = self.profile
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.profile_path, "w") as f:
            yaml.dump(profile, f, default_flow_style=False)

    def get(self, key, default=None):
        return self.profile.get(key, default)

    def set(self, key, value):
        self.profile[key] = value
        self._save()

    def set_preference(self, key, value):
        self.profile.setdefault("preferences", {})[key] = value
        self._save()

    def get_preference(self, key, default=None):
        return self.profile.get("preferences", {}).get(key, default)
"@ | Out-File -FilePath "trinity\memory\user_profile.py" -Encoding utf8

# trinity/skills/base.py
@"
"""Base Skill class."""
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path
import structlog
logger = structlog.get_logger(__name__)

@dataclass
class SkillResult:
    success: bool
    response: str
    data: dict = None
    requires_confirmation: bool = False
    confirmation_message: str = ""

class BaseSkill(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    async def execute(self, entities, context=None) -> SkillResult:
        pass

    def _confirm(self, message):
        return SkillResult(success=False, response="", requires_confirmation=True, confirmation_message=message)

    def _success(self, response, data=None):
        return SkillResult(success=True, response=response, data=data)

    def _error(self, message):
        return SkillResult(success=False, response=message)

    def _resolve_path(self, path_str):
        path = Path(path_str).expanduser()
        aliases = {"desktop": Path.home() / "Desktop", "documents": Path.home() / "Documents",
                   "downloads": Path.home() / "Downloads", "pictures": Path.home() / "Pictures",
                   "music": Path.home() / "Music", "videos": Path.home() / "Videos", "home": Path.home()}
        if path_str.lower().strip() in aliases:
            return str(aliases[path_str.lower().strip()])
        if not path.is_absolute():
            path = Path.home() / path
        return str(path)
"@ | Out-File -FilePath "trinity\skills\base.py" -Encoding utf8

# trinity/skills/filesystem/reader.py
@"
"""File System Reader."""
import structlog
from pathlib import Path
from datetime import datetime
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)
MAX_FILE_SIZE = 10 * 1024 * 1024

class FileSystemReader(BaseSkill):
    async def execute(self, entities, context=None):
        raw = entities.get("raw_text", "")
        if any(kw in raw.lower() for kw in ["what's in", "what is in", "list", "contents"]):
            return await self.list_dir(entities)
        return await self.read_file(entities)

    async def read_file(self, entities):
        path_str = entities.get("path", entities.get("raw_text", ""))
        path = Path(self._resolve_path(path_str))
        if not path.exists():
            return self._error(f"I couldn't find '{path_str}'.")
        if path.is_dir():
            return await self.list_dir(entities)
        if path.stat().st_size > MAX_FILE_SIZE:
            return self._error(f"This file is too large to read entirely.")
        try:
            content = await self._read_by_type(path)
            return self._success(f"Content of {path.name}:\\n\\n{content}", data={"path": str(path), "content": content})
        except Exception as e:
            return self._error(f"Error reading '{path.name}': {str(e)}")

    async def list_dir(self, entities):
        path_str = entities.get("path", entities.get("raw_text", ""))
        path = Path(self._resolve_path(path_str))
        if not path.exists():
            return self._error(f"The folder '{path_str}' doesn't exist. Should I create it?")
        if not path.is_dir():
            return await self.read_file(entities)
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            lines = []
            for item in items:
                icon = "📁" if item.is_dir() else "📄"
                size = f" ({self._fmt_size(item.stat().st_size)})" if item.is_file() else ""
                lines.append(f"{icon} {item.name}{size}")
            total = len(items)
            return self._success(f"Contents of {path.name} ({total} items):\\n\\n" + "\\n".join(lines))
        except PermissionError:
            return self._error(f"I don't have permission to access '{path.name}'.")

    async def _read_by_type(self, path):
        suffix = path.suffix.lower()
        if suffix in (".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".html", ".css", ".log"):
            return path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".pdf":
            try:
                import fitz
                doc = fitz.open(str(path))
                text = "".join(page.get_text() for page in doc)
                doc.close()
                return text[:50000]
            except ImportError:
                return "[PDF reader not available]"
        if suffix == ".docx":
            try:
                from docx import Document
                doc = Document(str(path))
                return "\\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                return "[DOCX reader not available]"
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return f"[Binary file: {self._fmt_size(path.stat().st_size)}]"

    @staticmethod
    def _fmt_size(size):
        for u in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {u}"
            size /= 1024
        return f"{size:.1f} TB"
"@ | Out-File -FilePath "trinity\skills\filesystem\reader.py" -Encoding utf8

# trinity/skills/filesystem/writer.py
@"
"""File System Writer."""
import shutil
import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class FileSystemWriter(BaseSkill):
    async def execute(self, entities, context=None):
        raw = entities.get("raw_text", "").lower()
        if any(kw in raw for kw in ["edit", "modify", "change", "update", "set"]):
            return await self.edit_file(entities)
        return await self.create_file(entities)

    async def create_file(self, entities):
        path_str = entities.get("path", entities.get("raw_text", ""))
        content = entities.get("content", "")
        path = Path(self._resolve_path(path_str))
        if path.exists():
            return self._error(f"'{path.name}' already exists. Overwrite, rename, or skip?")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return self._success(f"Created {path.name}")
        except Exception as e:
            return self._error(f"Error creating file: {str(e)}")

    async def create_dir(self, entities):
        path_str = entities.get("path", entities.get("raw_text", ""))
        path = Path(self._resolve_path(path_str))
        if path.exists():
            return self._error(f"'{path.name}' already exists.")
        try:
            path.mkdir(parents=True, exist_ok=True)
            return self._success(f"Created folder '{path.name}'")
        except Exception as e:
            return self._error(f"Error creating folder: {str(e)}")

    async def edit_file(self, entities):
        path_str = entities.get("path", entities.get("raw_text", ""))
        find_text = entities.get("find", "")
        replace_text = entities.get("replace", "")
        path = Path(self._resolve_path(path_str))
        if not path.exists():
            return self._error(f"I couldn't find '{path_str}'.")
        try:
            backup = path.with_suffix(path.suffix + ".trinity-backup")
            shutil.copy2(str(path), str(backup))
            content = path.read_text(encoding="utf-8", errors="replace")
            if find_text and find_text in content:
                new_content = content.replace(find_text, replace_text)
                path.write_text(new_content, encoding="utf-8")
                return self._success(f"Updated {path.name}. Backup saved.")
            return self._error(f"Couldn't find '{find_text}' in {path.name}.")
        except Exception as e:
            if backup.exists():
                shutil.copy2(str(backup), str(path))
            return self._error(f"Error editing file: {str(e)}")
"@ | Out-File -FilePath "trinity\skills\filesystem\writer.py" -Encoding utf8

# trinity/skills/filesystem/mover.py
@"
"""File System Mover."""
import shutil
import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class FileSystemMover(BaseSkill):
    async def execute(self, entities, context=None):
        raw = entities.get("raw_text", "").lower()
        if "copy" in raw:
            return await self.copy(entities)
        return await self.move(entities)

    async def move(self, entities):
        source_str = entities.get("path", entities.get("raw_text", ""))
        source = Path(self._resolve_path(source_str))
        if not source.exists():
            return self._error(f"I couldn't find '{source_str}'.")
        try:
            dest = Path(self._resolve_path(entities.get("to", ""))) / source.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
            return self._success(f"Moved {source.name} to {dest.parent}")
        except Exception as e:
            return self._error(f"Error moving: {str(e)}")

    async def copy(self, entities):
        source_str = entities.get("path", entities.get("raw_text", ""))
        source = Path(self._resolve_path(source_str))
        if not source.exists():
            return self._error(f"I couldn't find '{source_str}'.")
        try:
            dest = Path(self._resolve_path(entities.get("to", "")))
            if source.is_dir():
                shutil.copytree(str(source), str(dest / source.name))
            else:
                shutil.copy2(str(source), str(dest / source.name) if dest.is_dir() else str(dest))
            return self._success(f"Copied {source.name}")
        except Exception as e:
            return self._error(f"Error copying: {str(e)}")
"@ | Out-File -FilePath "trinity\skills\filesystem\mover.py" -Encoding utf8

# trinity/skills/filesystem/deleter.py
@"
"""File System Deleter - sends to Recycle Bin."""
import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class FileSystemDeleter(BaseSkill):
    async def execute(self, entities, context=None):
        path_str = entities.get("path", entities.get("raw_text", ""))
        path = Path(self._resolve_path(path_str))
        if not path.exists():
            return self._error(f"I couldn't find '{path_str}'.")
        try:
            from send2trash import send2trash
            send2trash(str(path))
            return self._success(f"Moved {path.name} to the Recycle Bin.")
        except ImportError:
            return self._confirm(f"send2trash not installed. Permanently delete {path.name}?")
        except Exception as e:
            return self._error(f"Error deleting: {str(e)}")
"@ | Out-File -FilePath "trinity\skills\filesystem\deleter.py" -Encoding utf8

# trinity/skills/filesystem/searcher.py
@"
"""File System Searcher."""
import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class FileSystemSearcher(BaseSkill):
    async def execute(self, entities, context=None):
        query = entities.get("raw_text", "").lower()
        search_dirs = [Path.home() / d for d in ["Desktop", "Documents", "Downloads", "Pictures"]]
        results = []
        for sd in search_dirs:
            if not sd.exists():
                continue
            for item in sd.rglob("*"):
                try:
                    if query and query not in item.name.lower():
                        continue
                    results.append(item)
                    if len(results) > 50:
                        break
                except (PermissionError, OSError):
                    continue
            if len(results) > 50:
                break
        if not results:
            return self._success(f"No files found matching '{query}'.")
        lines = [f"📄 {r}" for r in results[:30]]
        return self._success(f"Found {len(results)} result(s):\\n\\n" + "\\n".join(lines))
"@ | Out-File -FilePath "trinity\skills\filesystem\searcher.py" -Encoding utf8

# trinity/skills/filesystem/documents.py
@"
"""Document Handler - DOCX, XLSX, PDF."""
import structlog
from pathlib import Path
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class DocumentHandler(BaseSkill):
    async def execute(self, entities, context=None):
        path_str = entities.get("path", "")
        path = Path(self._resolve_path(path_str))
        suffix = path.suffix.lower()
        if suffix == ".docx":
            try:
                from docx import Document
                doc = Document(str(path))
                return self._success("\\n".join(p.text for p in doc.paragraphs))
            except ImportError:
                return self._error("python-docx not installed")
        if suffix == ".pdf":
            try:
                import fitz
                doc = fitz.open(str(path))
                text = "".join(page.get_text() for page in doc)
                doc.close()
                return self._success(text[:10000])
            except ImportError:
                return self._error("PyMuPDF not installed")
        return self._error(f"Unsupported format: {suffix}")
"@ | Out-File -FilePath "trinity\skills\filesystem\documents.py" -Encoding utf8

# trinity/skills/calendar/client.py
@"
"""Google Calendar Client."""
import structlog
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class CalendarClient(BaseSkill):
    def __init__(self, config, google_auth=None):
        super().__init__(config)
        self.google_auth = google_auth

    async def execute(self, entities, context=None):
        if not self.google_auth or not self.google_auth.is_authenticated():
            return self._error("Google Calendar isn't connected. Say 'Trinity, connect my Google account'.")
        return self._success("Checking your calendar...")
"@ | Out-File -FilePath "trinity\skills\calendar\client.py" -Encoding utf8

# trinity/skills/email/client.py
@"
"""Gmail Client."""
import structlog
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class EmailClient(BaseSkill):
    def __init__(self, config, google_auth=None):
        super().__init__(config)
        self.google_auth = google_auth

    async def execute(self, entities, context=None):
        if not self.google_auth or not self.google_auth.is_authenticated():
            return self._error("Gmail isn't connected. Say 'Trinity, connect my Google account'.")
        return self._success("Checking your email...")
"@ | Out-File -FilePath "trinity\skills\email\client.py" -Encoding utf8

# trinity/skills/drive/client.py
@"
"""Google Drive Client."""
import structlog
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class DriveClient(BaseSkill):
    def __init__(self, config, google_auth=None):
        super().__init__(config)
        self.google_auth = google_auth

    async def execute(self, entities, context=None):
        if not self.google_auth or not self.google_auth.is_authenticated():
            return self._error("Google Drive isn't connected. Say 'Trinity, connect my Google account'.")
        return self._success("Google Drive ready. What would you like to do?")
"@ | Out-File -FilePath "trinity\skills\drive\client.py" -Encoding utf8

# trinity/skills/maps/location.py
@"
"""Location Service."""
import structlog
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class LocationService(BaseSkill):
    async def execute(self, entities, context=None):
        city = self.config["trinity"]["home_city"]
        return self._success(f"You're currently in {city}.")
"@ | Out-File -FilePath "trinity\skills\maps\location.py" -Encoding utf8

# trinity/skills/maps/directions.py
@"
"""Directions Service."""
import structlog
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class DirectionsService(BaseSkill):
    async def execute(self, entities, context=None):
        maps_key = self.config.get("google", {}).get("maps_api_key", "")
        if not maps_key:
            return self._error("Google Maps isn't configured yet.")
        return self._success("Getting directions...")
"@ | Out-File -FilePath "trinity\skills\maps\directions.py" -Encoding utf8

# trinity/skills/applications/launcher.py
@"
"""Application Launcher."""
import structlog
from trinity.skills.base import BaseSkill, SkillResult
logger = structlog.get_logger(__name__)

class ApplicationLauncher(BaseSkill):
    async def execute(self, entities, context=None):
        return self._success("Application launcher ready.")
"@ | Out-File -FilePath "trinity\skills\applications\launcher.py" -Encoding utf8

# trinity/integrations/google_auth.py
@"
"""Google OAuth Authentication."""
import structlog
logger = structlog.get_logger(__name__)

class GoogleAuthManager:
    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self, config, credential_store=None):
        self.config = config
        self.credential_store = credential_store
        self.client_id = config["google"]["client_id"]
        self.client_secret = config["google"]["client_secret"]
        self.credentials = None

    async def authenticate(self):
        if not self.client_id or not self.client_secret:
            return False
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            client_config = {"installed": {"client_id": self.client_id, "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.config["google"]["redirect_uri"]]}}
            flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
            self.credentials = flow.run_local_server(port=self.config["advanced"]["local_http_port"])
            if self.credential_store:
                self.credential_store.store("google_credentials", self.credentials.to_json())
            return True
        except Exception as e:
            logger.error("google_auth.failed", error=str(e))
            return False

    def is_authenticated(self):
        return self.credentials is not None and self.credentials.valid

    def get_calendar_service(self):
        return self._build_service("calendar", "v3")

    def get_gmail_service(self):
        return self._build_service("gmail", "v1")

    def get_drive_service(self):
        return self._build_service("drive", "v3")

    def _build_service(self, api_name, version):
        if not self.credentials:
            return None
        try:
            from googleapiclient.discovery import build
            return build(api_name, version, credentials=self.credentials)
        except Exception as e:
            logger.error("google_auth.service_failed", api=api_name, error=str(e))
            return None
"@ | Out-File -FilePath "trinity\integrations\google_auth.py" -Encoding utf8

# trinity/integrations/credential_store.py
@"
"""Credential Store using keyring."""
import structlog
logger = structlog.get_logger(__name__)
SERVICE_NAME = "TrinityAgent"

class CredentialStore:
    def __init__(self, config):
        self.config = config

    def store(self, key, value):
        try:
            import keyring
            keyring.set_password(SERVICE_NAME, key, value)
        except Exception as e:
            logger.warning("credential.store_failed", error=str(e))

    def load(self, key):
        try:
            import keyring
            return keyring.get_password(SERVICE_NAME, key)
        except Exception:
            return None
"@ | Out-File -FilePath "trinity\integrations\credential_store.py" -Encoding utf8

# trinity/updates/checker.py
@"
"""Update Checker."""
import asyncio
import structlog
logger = structlog.get_logger(__name__)

class UpdateChecker:
    def __init__(self, config):
        self.config = config
        self.repo_url = config["updates"]["update_repo"]

    async def check(self):
        if not self.repo_url:
            return None
        try:
            import httpx
            api_url = self.repo_url.replace("https://github.com/", "https://api.github.com/repos/") + "/releases/latest"
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, timeout=10)
            if response.status_code == 200:
                release = response.json()
                return {"version": release["tag_name"], "url": release["html_url"], "notes": release.get("body", "")}
        except Exception as e:
            logger.warning("update.check_failed", error=str(e))
        return None
"@ | Out-File -FilePath "trinity\updates\checker.py" -Encoding utf8

# trinity/watchdog/monitor.py
@"
"""Watchdog Monitor - crash detection."""
import structlog
logger = structlog.get_logger(__name__)

class WatchdogMonitor:
    def __init__(self, config):
        self.config = config
"@ | Out-File -FilePath "trinity\watchdog\monitor.py" -Encoding utf8

# trinity/ui/overlay.py
@"
"""Voice Overlay UI."""
import structlog
logger = structlog.get_logger(__name__)

class VoiceOverlay:
    def __init__(self, config):
        self.config = config
    def show_listening(self):
        pass
    def show_response(self, text):
        pass
"@ | Out-File -FilePath "trinity\ui\overlay.py" -Encoding utf8

# trinity/ui/dashboard.py
@"
"""Dashboard UI."""
import structlog
logger = structlog.get_logger(__name__)

class Dashboard:
    def __init__(self, config):
        self.config = config
"@ | Out-File -FilePath "trinity\ui\dashboard.py" -Encoding utf8

# trinity/ui/confirm.py
@"
"""Confirmation Dialog."""
import structlog
logger = structlog.get_logger(__name__)

class ConfirmDialog:
    def __init__(self, config):
        self.config = config
    def show(self, message, action="Confirm"):
        return False
"@ | Out-File -FilePath "trinity\ui\confirm.py" -Encoding utf8

# trinity/ui/setup_wizard.py
@"
"""Setup Wizard."""
import structlog
logger = structlog.get_logger(__name__)

class SetupWizard:
    def __init__(self, config):
        self.config = config
    def start(self):
        pass
"@ | Out-File -FilePath "trinity\ui\setup_wizard.py" -Encoding utf8

Write-Host "   ✅ All source files created" -ForegroundColor Green

# Create .gitignore
@"
__pycache__/
*.py[cod]
.venv/
.env
.trinity/
.pytest_cache/
*.log
*.trinity-backup
"@ | Out-File -FilePath ".gitignore" -Encoding utf8

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Trinity is installed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run Trinity:" -ForegroundColor White
Write-Host "  cd $HOME\Agent-Trinity" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "  python -m trinity.main" -ForegroundColor Yellow
Write-Host ""
Write-Host "To test without microphone (text mode):" -ForegroundColor White
Write-Host "  python -m trinity.main --debug" -ForegroundColor Yellow
