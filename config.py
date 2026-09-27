# import os
# import sys
# import re

# # Snapshot Storage
# DOT_GIT_DIR = ".git"
# SNAPSHOT_FILE = os.path.join(DOT_GIT_DIR, "sentry_last_snapshot")

# # Regex Patterns for Secret Detection
# SECRET_PATTERNS = {
#     "AWS Access Key": r"AKIA[0-9A-Z]{16}",
#     "OpenAI/Anthropic Key": r"sk-[a-zA-Z0-9_-]{20,}",
#     "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,}",
#     "Private Key": r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
#     "Generic Secret": r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{16,}['\"]"
# }

# def get_encoding_config():
#     """Returns subprocess config to prevent Windows encoding issues."""
#     config = {"encoding": "utf-8", "errors": "replace"}
#     if sys.platform == "win32":
#         # Ensure we don't break on Windows with non-UTF8 consoles
#         import subprocess
#         subprocess.run("chcp 65001", shell=True, capture_output=True)
#     return config




# import os
# import sys
# from pathlib import Path

# # Snapshot Storage
# DOT_GIT_DIR = Path(".git")
# SNAPSHOT_FILE = DOT_GIT_DIR / "sentry_last_snapshot"

# # Regex Patterns for Secret Detection
# SECRET_PATTERNS = {
#     "AWS Access Key": r"AKIA[0-9A-Z]{16}",
#     "OpenAI/Anthropic Key": r"sk-[a-zA-Z0-9_-]{20,}",
#     "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,}",
#     "Private Key": r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
#     "Generic Secret": r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{16,}['\"]",
# }

# # Subprocess Configuration
# SUBPROCESS_ENCODING = {
#     "encoding": "utf-8",
#     "errors": "replace",
#     "text": True,
# }

# def format_windows_command(cmd: str) -> str:
#     """Prepends code page 65001 on Windows so shell commands run in UTF-8."""
#     if sys.platform == "win32":
#         return f"chcp 65001 >nul && {cmd}"
#     return cmd


# import os
# import sys
# import json
# from pathlib import Path

# # User Global Configuration (~/.git-sentry/config.json)
# GLOBAL_CONFIG_DIR = Path.home() / ".git-sentry"
# GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"

# def get_global_api_key() -> str | None:
#     """Retrieves API key from environment or user global config."""
#     env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
#     if env_key:
#         return env_key
#     if GLOBAL_CONFIG_FILE.exists():
#         try:
#             data = json.loads(GLOBAL_CONFIG_FILE.read_text(encoding="utf-8"))
#             return data.get("api_key")
#         except Exception:
#             return None
#     return None

# def set_global_api_key(key: str):
#     """Saves the API key globally in the user home profile."""
#     GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
#     GLOBAL_CONFIG_FILE.write_text(json.dumps({"api_key": key}, indent=2), encoding="utf-8")

# def get_repo_root() -> Path | None:
#     """Finds the root directory of the active repository dynamically."""
#     import subprocess
#     try:
#         res = subprocess.run(
#             ["git", "rev-parse", "--show-toplevel"],
#             capture_output=True,
#             text=True,
#             encoding="utf-8",
#             errors="replace"
#         )
#         if res.returncode == 0 and res.stdout.strip():
#             return Path(res.stdout.strip())
#     except Exception:
#         pass
#     return None

# def get_snapshot_file() -> Path | None:
#     """Resolves the snapshot file inside the active repository's .git folder."""
#     root = get_repo_root()
#     if root:
#         return root / ".git" / "sentry_last_snapshot"
#     return None

# # Regex Patterns for Secret Detection
# SECRET_PATTERNS = {
#     "AWS Access Key": r"AKIA[0-9A-Z]{16}",
#     "OpenAI/Anthropic Key": r"sk-[a-zA-Z0-9_-]{20,}",
#     "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,}",
#     "Private Key": r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
#     "Generic Secret": r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{16,}['\"]",
# }

import os
import sys
import json
import subprocess
from pathlib import Path

# User Global Configuration (~/.git-sentry/config.json)
GLOBAL_CONFIG_DIR = Path.home() / ".git-sentry"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"

# Alias for backward compatibility
DEFAULT_CONFIG_DIR = GLOBAL_CONFIG_DIR
DEFAULT_CONFIG_FILE = GLOBAL_CONFIG_FILE

def get_config() -> dict:
    """Reads the JSON configuration file safely."""
    if GLOBAL_CONFIG_FILE.exists():
        try:
            return json.loads(GLOBAL_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_config(api_key: str, storage_dir: str | None = None, model: str = "gemini-3.8-flash"):
    """Saves API key, optional custom snapshot directory, and chosen model."""
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = {
        "api_key": api_key.strip(),
        "storage_dir": str(Path(storage_dir).resolve()) if storage_dir else str(GLOBAL_CONFIG_DIR),
        "model": model.strip()
    }
    GLOBAL_CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def get_global_api_key() -> str | None:
    """Retrieves API key from environment variables or global config."""
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key
    return get_config().get("api_key")

def set_global_api_key(key: str):
    """Convenience setter preserving existing config values."""
    current = get_config()
    storage_dir = current.get("storage_dir")
    model = current.get("model", "gemini-3.8-flash")
    save_config(api_key=key, storage_dir=storage_dir, model=model)

DEFAULT_MODEL = "gemini-3.8-flash"
SUPPORTED_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.8-pro",
]

def get_selected_model() -> str:
    """Returns the user's configured model or defaults to gemini-3.5-flash."""
    return get_config().get("model", DEFAULT_MODEL)

def get_repo_root() -> Path | None:
    """Finds the root directory of the active repository dynamically."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode == 0 and res.stdout.strip():
            return Path(res.stdout.strip())
    except Exception:
        pass
    return None

def get_snapshot_file() -> Path | None:
    """Resolves snapshot path based on custom storage dir or local repo .git directory."""
    cfg = get_config()
    custom_dir = cfg.get("storage_dir")
    root = get_repo_root()
    if not root:
        return None

    if custom_dir and Path(custom_dir) != GLOBAL_CONFIG_DIR:
        repo_hash = str(abs(hash(str(root.resolve()))))
        target = Path(custom_dir) / f"snapshot_{repo_hash}"
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    return root / ".git" / "sentry_last_snapshot"

# Regex Patterns for Secret Detection
SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "OpenAI/Anthropic Key": r"sk-[a-zA-Z0-9_-]{20,}",
    "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,}",
    "Private Key": r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
    "Generic Secret": r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{16,}['\"]",
}