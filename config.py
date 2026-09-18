import os
import sys
import re

# Snapshot Storage
DOT_GIT_DIR = ".git"
SNAPSHOT_FILE = os.path.join(DOT_GIT_DIR, "sentry_last_snapshot")

# Regex Patterns for Secret Detection
SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "OpenAI/Anthropic Key": r"sk-[a-zA-Z0-9_-]{20,}",
    "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,}",
    "Private Key": r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
    "Generic Secret": r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{16,}['\"]"
}

def get_encoding_config():
    """Returns subprocess config to prevent Windows encoding issues."""
    config = {"encoding": "utf-8", "errors": "replace"}
    if sys.platform == "win32":
        # Ensure we don't break on Windows with non-UTF8 consoles
        import subprocess
        subprocess.run("chcp 65001", shell=True, capture_output=True)
    return config