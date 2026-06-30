"""
Configuration loader — reads .env + config.yaml and merges them.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import yaml
import structlog

logger = structlog.get_logger(__name__)

# Default config values
DEFAULTS = {
    "trinity": {
        "user_name": "Mr. Walker",
        "timezone": "Africa/Accra",
        "home_address": "Hohoe, Ghana",
        "home_city": "Accra",
        "work_address": "",
        "default_browser": "edge",
        "auto_start": True,
        "data_dir": "~/.trinity",
        "log_level": "INFO",
        "privacy_mode": "hybrid",
        "redact_pii": True,
        "store_voice": False,
        "debug_mode": False,
    },
    "voice": {
        "elevenlabs_api_key": "",
        "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
        "elevenlabs_model": "eleven_turbo_v2_5",
        "wake_word": "Trinity",
        "wake_sensitivity": 0.5,
        "always_listening": True,
        "push_to_talk_hotkey": "ctrl+alt+space",
        "mute_hotkey": "ctrl+alt+m",
    },
    "llm": {
        "openai_api_key": "",
        "anthropic_api_key": "",
        "ollama_base_url": "http://localhost:11434",
        "local_fast": "llama3.2:1b",
        "local_capable": "llama3.2:3b",
        "cloud_primary": "gpt-4o",
        "cloud_fallback": "claude-3-5-sonnet-20241022",
        "mode": "local",
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "google": {
        "project_id": "agent-trinity-500718",
        "project_number": "177176143306",
        "client_id": "",
        "client_secret": "",
        "redirect_uri": "http://localhost:8400/auth/callback",
        "maps_api_key": "",
    },
    "hardware": {
        "gpu_enabled": False,
        "gpu_device": -1,
        "max_ram_gb": 2,
    },
    "updates": {
        "channel": "stable",
        "auto_update": True,
        "update_repo": "https://github.com/johnboateng19743-afk/Agent-Trinity",
        "auto_check": True,
        "check_interval_hours": 6,
    },
    "advanced": {
        "local_http_port": 8400,
        "watchdog_enabled": True,
    },
}


def load_config(config_path: str | None = None) -> dict:
    """Load configuration from .env file and optional YAML config."""
    # Find .env file
    env_path = Path(config_path).parent / ".env" if config_path else Path(__file__).parent.parent.parent / ".env"

    if env_path.exists():
        load_dotenv(env_path)
        logger.info("config.loaded_env", path=str(env_path))
    else:
        logger.warning("config.no_env_file", searched=str(env_path))

    # Start with defaults
    config = _deep_copy(DEFAULTS)

    # Override from environment variables
    config["trinity"]["user_name"] = os.getenv("TRINITY_USER_NAME", config["trinity"]["user_name"])
    config["trinity"]["timezone"] = os.getenv("TRINITY_TIMEZONE", config["trinity"]["timezone"])
    config["trinity"]["home_address"] = os.getenv("TRINITY_HOME_ADDRESS", config["trinity"]["home_address"])
    config["trinity"]["home_city"] = os.getenv("TRINITY_HOME_CITY", config["trinity"]["home_city"])
    config["trinity"]["work_address"] = os.getenv("TRINITY_WORK_ADDRESS", config["trinity"]["work_address"])
    config["trinity"]["default_browser"] = os.getenv("TRINITY_DEFAULT_BROWSER", config["trinity"]["default_browser"])
    config["trinity"]["auto_start"] = os.getenv("TRINITY_AUTO_START", "true").lower() == "true"
    config["trinity"]["data_dir"] = os.getenv("TRINITY_DATA_DIR", config["trinity"]["data_dir"])
    config["trinity"]["log_level"] = os.getenv("TRINITY_LOG_LEVEL", config["trinity"]["log_level"])
    config["trinity"]["privacy_mode"] = os.getenv("TRINITY_PRIVACY_MODE", config["trinity"]["privacy_mode"])
    config["trinity"]["redact_pii"] = os.getenv("TRINITY_REDACT_PII", "true").lower() == "true"
    config["trinity"]["store_voice"] = os.getenv("TRINITY_STORE_VOICE", "false").lower() == "true"
    config["trinity"]["debug_mode"] = os.getenv("TRINITY_DEBUG_MODE", "false").lower() == "true"

    # Voice
    config["voice"]["elevenlabs_api_key"] = os.getenv("ELEVENLABS_API_KEY", "")
    config["voice"]["elevenlabs_voice_id"] = os.getenv("ELEVENLABS_VOICE_ID", config["voice"]["elevenlabs_voice_id"])
    config["voice"]["elevenlabs_model"] = os.getenv("ELEVENLABS_MODEL", config["voice"]["elevenlabs_model"])

    # LLM
    config["llm"]["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    config["llm"]["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY", "")
    config["llm"]["ollama_base_url"] = os.getenv("OLLAMA_BASE_URL", config["llm"]["ollama_base_url"])
    config["llm"]["local_fast"] = os.getenv("LOCAL_LLM_FAST", config["llm"]["local_fast"])
    config["llm"]["local_capable"] = os.getenv("LOCAL_LLM_CAPABLE", config["llm"]["local_capable"])
    config["llm"]["mode"] = os.getenv("LLM_MODE", config["llm"].get("mode", "local"))
    config["llm"]["cloud_primary"] = os.getenv("CLOUD_LLM_PRIMARY", config["llm"]["cloud_primary"])
    config["llm"]["cloud_fallback"] = os.getenv("CLOUD_LLM_FALLBACK", config["llm"]["cloud_fallback"])

    # Google
    config["google"]["project_id"] = os.getenv("GOOGLE_CLOUD_PROJECT_ID", config["google"]["project_id"])
    config["google"]["project_number"] = os.getenv("GOOGLE_CLOUD_PROJECT_NUMBER", config["google"]["project_number"])
    config["google"]["client_id"] = os.getenv("GOOGLE_CLIENT_ID", "")
    config["google"]["client_secret"] = os.getenv("GOOGLE_CLIENT_SECRET", "")
    config["google"]["redirect_uri"] = os.getenv("GOOGLE_REDIRECT_URI", config["google"]["redirect_uri"])
    config["google"]["maps_api_key"] = os.getenv("GOOGLE_MAPS_API_KEY", "")

    # Hardware
    config["hardware"]["gpu_enabled"] = os.getenv("TRINITY_GPU_ENABLED", "false").lower() == "true"
    config["hardware"]["gpu_device"] = int(os.getenv("TRINITY_GPU_DEVICE", "-1"))
    config["hardware"]["max_ram_gb"] = int(os.getenv("TRINITY_MAX_RAM_GB", "2"))

    # Updates
    config["updates"]["channel"] = os.getenv("TRINITY_UPDATE_CHANNEL", config["updates"]["channel"])
    config["updates"]["auto_update"] = os.getenv("TRINITY_AUTO_UPDATE", "true").lower() == "true"
    config["updates"]["update_repo"] = os.getenv("TRINITY_UPDATE_REPO", config["updates"]["update_repo"])

    # Advanced
    config["advanced"]["local_http_port"] = int(os.getenv("TRINITY_LOCAL_HTTP_PORT", "8400"))
    config["advanced"]["watchdog_enabled"] = os.getenv("TRINITY_WATCHDOG_ENABLED", "true").lower() == "true"

    # Load YAML config overrides if they exist
    yaml_path = Path(config["trinity"]["data_dir"]).expanduser() / "config.yaml"
    if yaml_path.exists():
        with open(yaml_path) as f:
            yaml_config = yaml.safe_load(f)
        if yaml_config:
            _deep_merge(config, yaml_config)
            logger.info("config.loaded_yaml", path=str(yaml_path))

    # Ensure data directories exist
    data_dir = Path(config["trinity"]["data_dir"]).expanduser()
    (data_dir / "data").mkdir(parents=True, exist_ok=True)
    (data_dir / "data" / "chroma").mkdir(parents=True, exist_ok=True)
    (data_dir / "data" / "skills").mkdir(parents=True, exist_ok=True)
    (data_dir / "versions").mkdir(parents=True, exist_ok=True)
    (data_dir / "logs").mkdir(parents=True, exist_ok=True)
    (data_dir / "logs" / "crash").mkdir(parents=True, exist_ok=True)
    (data_dir / "cache").mkdir(parents=True, exist_ok=True)

    return config


def _deep_copy(d: dict) -> dict:
    """Deep copy a nested dict."""
    return {k: _deep_copy(v) if isinstance(v, dict) else v for k, v in d.items()}


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base dict."""
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base
