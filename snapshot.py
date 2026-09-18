import subprocess
import os
from config import SNAPSHOT_FILE, get_encoding_config

def create_shadow_snapshot() -> str | None:
    # Captures current index + working tree into a dangling commit
    sha = subprocess.run(
        ["git", "stash", "create"], 
        capture_output=True, text=True, **get_encoding_config()
    ).stdout.strip()

    if not sha:
        # If clean, just use HEAD
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], 
            capture_output=True, text=True, **get_encoding_config()
        ).stdout.strip()

    if sha:
        with open(SNAPSHOT_FILE, "w") as f:
            f.write(sha)
    return sha

def execute_panic_revert() -> tuple[bool, str]:
    if not os.path.exists(SNAPSHOT_FILE):
        return False, "No snapshot found to revert to."
    
    with open(SNAPSHOT_FILE, "r") as f:
        sha = f.read().strip()
    
    res = subprocess.run(
        ["git", "checkout", sha, "--", "."], 
        capture_output=True, text=True, **get_encoding_config()
    )
    if res.returncode == 0:
        return True, f"Restored working tree to shadow snapshot: {sha}"
    return False, res.stderr