"""
Configuration, API key discovery, and user settings for LLMForge.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_MODEL = "recursive/flint-v1.0:free"
CONFIG_DIR = Path.home() / ".llmforge"
CONFIG_FILE = CONFIG_DIR / "config.json"
ENV_FILE = CONFIG_DIR / ".env"

DEFAULT_SETTINGS = {
    "default_model": DEFAULT_MODEL,
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 4096,
    "stream": True,
    "save_transcripts": True,
    "system_prompt": "You are a helpful, expert AI assistant powered by OpenRouter's Free Tier."
}

def get_api_key() -> Optional[str]:
    """
    Retrieve OpenRouter API key.
    Checks in priority:
    1. os.environ['OPENROUTER_API_KEY']
    2. ~/.llmforge/.env
    3. .env in current working directory
    """
    # 1. Environment variable
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key

    # 2. Local ~/.llmforge/.env
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass

    # 3. .env in current directory
    local_env = Path(".env")
    if local_env.exists():
        try:
            with open(local_env, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass

    return None

def save_api_key_to_env(key: str) -> None:
    """Save API key to ~/.llmforge/.env for future runs."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(f"OPENROUTER_API_KEY={key}\n")
    os.environ["OPENROUTER_API_KEY"] = key

def load_settings() -> Dict[str, Any]:
    """Load settings from config file, creating defaults if missing."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                merged = {**DEFAULT_SETTINGS, **saved}
                return merged
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> None:
    """Save updated settings to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass
