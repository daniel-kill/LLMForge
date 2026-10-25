"""
Configuration, API key discovery, and user settings for LLMForge.
Supports both OpenRouter Free-Tier and Groq LPU inference.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_OPENROUTER_MODEL = "recursive/flint-v1.0:free"
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"

CONFIG_DIR = Path.home() / ".llmforge"
CONFIG_FILE = CONFIG_DIR / "config.json"
ENV_FILE = CONFIG_DIR / ".env"

DEFAULT_SETTINGS = {
    "active_provider": "openrouter",
    "default_model": DEFAULT_OPENROUTER_MODEL,
    "openrouter_default_model": DEFAULT_OPENROUTER_MODEL,
    "groq_default_model": DEFAULT_GROQ_MODEL,
    "temperature": 0.7,
    "top_p": 0.95,
    "max_tokens": 4096,
    "stream": True,
    "save_transcripts": True,
    "system_prompt": "You are a helpful, expert AI assistant powered by LLMForge."
}

PROVIDER_ENV_VARS = {
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY"
}

def _lookup_env_file(path: Path, target_var: str) -> Optional[str]:
    """Search a .env file for the given variable."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{target_var}="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    except Exception:
        pass
    return None

def get_api_key(provider: str = "openrouter") -> Optional[str]:
    """
    Retrieve API key for the requested provider ('openrouter' or 'groq').
    Searches:
    1. os.environ[VAR]
    2. ~/.llmforge/.env
    3. .env in current working directory
    4. Cross-environment fallback (WSL -> Windows Host environment/paths)
    """
    var_name = PROVIDER_ENV_VARS.get(provider.lower(), "OPENROUTER_API_KEY")

    # 1. Active environment variable
    key = os.environ.get(var_name, "").strip()
    if key:
        return key

    # 2. Local user config ~/.llmforge/.env
    found = _lookup_env_file(ENV_FILE, var_name)
    if found:
        return found

    # 3. .env in current directory
    found = _lookup_env_file(Path(".env"), var_name)
    if found:
        return found

    # 4. WSL -> Windows user fallback
    if os.name != "nt" and Path("/proc/version").exists():
        try:
            # Check mounted Windows user .llmforge/.env
            for win_user_dir in Path("/mnt/c/Users").glob("*/.llmforge/.env"):
                found = _lookup_env_file(win_user_dir, var_name)
                if found:
                    return found

            # Check Windows User environment via powershell.exe if available
            cmd = ["powershell.exe", "-NoProfile", "-Command", f"[System.Environment]::GetEnvironmentVariable('{var_name}', 'User')"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if proc.returncode == 0:
                val = proc.stdout.strip()
                if val:
                    return val
        except Exception:
            pass

    return None

def save_api_key_to_env(key: str, provider: str = "openrouter") -> None:
    """Save or update API key in ~/.llmforge/.env for future runs."""
    var_name = PROVIDER_ENV_VARS.get(provider.lower(), "OPENROUTER_API_KEY")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    lines = []
    found = False
    if ENV_FILE.exists():
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith(f"{var_name}="):
                        lines.append(f"{var_name}={key}\n")
                        found = True
                    else:
                        lines.append(line)
        except Exception:
            pass

    if not found:
        lines.append(f"{var_name}={key}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    os.environ[var_name] = key

def get_available_providers() -> Dict[str, bool]:
    """Check which providers currently have a valid API key discovered."""
    return {
        "openrouter": bool(get_api_key("openrouter")),
        "groq": bool(get_api_key("groq"))
    }

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
