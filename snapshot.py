# import subprocess
# import os
# from config import SNAPSHOT_FILE, get_encoding_config

# def create_shadow_snapshot() -> str | None:
#     # Captures current index + working tree into a dangling commit
#     sha = subprocess.run(
#         ["git", "stash", "create"], 
#         capture_output=True, text=True, **get_encoding_config()
#     ).stdout.strip()

#     if not sha:
#         # If clean, just use HEAD
#         sha = subprocess.run(
#             ["git", "rev-parse", "HEAD"], 
#             capture_output=True, text=True, **get_encoding_config()
#         ).stdout.strip()

#     if sha:
#         with open(SNAPSHOT_FILE, "w") as f:
#             f.write(sha)
#     return sha

# def execute_panic_revert() -> tuple[bool, str]:
#     if not os.path.exists(SNAPSHOT_FILE):
#         return False, "No snapshot found to revert to."
    
#     with open(SNAPSHOT_FILE, "r") as f:
#         sha = f.read().strip()
    
#     res = subprocess.run(
#         ["git", "checkout", sha, "--", "."], 
#         capture_output=True, text=True, **get_encoding_config()
#     )
#     if res.returncode == 0:
#         return True, f"Restored working tree to shadow snapshot: {sha}"
#     return False, res.stderr




# import subprocess
# from pathlib import Path
# from config import SNAPSHOT_FILE

# def _run_git(args: list[str]) -> tuple[int, str, str]:
#     """Helper to run git commands with explicit utf-8 encoding."""
#     try:
#         res = subprocess.run(
#             ["git"] + args,
#             capture_output=True,
#             text=True,
#             encoding="utf-8",
#             errors="replace"
#         )
#         return res.returncode, res.stdout.strip(), res.stderr.strip()
#     except Exception as e:
#         return 1, "", str(e)

# def create_shadow_snapshot() -> str | None:
#     """
#     Captures current index, working tree, and untracked files into a dangling commit.
#     Creates a true shadow snapshot without altering the working directory or stash list.
#     """
#     # 1. Attempt stash create with untracked files (-u)
#     code, sha, _ = _run_git(["stash", "create", "-u"])

#     # Fallback to standard stash create if -u isn't supported or empty
#     if not sha:
#         code, sha, _ = _run_git(["stash", "create"])

#     # 2. If the working tree was already clean, snapshot current HEAD
#     if not sha:
#         code, head_sha, _ = _run_git(["rev-parse", "--verify", "HEAD"])
#         if code == 0 and head_sha:
#             sha = head_sha

#     # 3. Persist the snapshot SHA to disk
#     if sha:
#         snapshot_path = Path(SNAPSHOT_FILE)
#         snapshot_path.parent.mkdir(parents=True, exist_ok=True)
#         snapshot_path.write_text(sha, encoding="utf-8")
#         return sha

#     return None

# def execute_panic_revert() -> tuple[bool, str]:
#     """
#     Restores the repository working tree and index to the dangling shadow snapshot commit.
#     """
#     snapshot_path = Path(SNAPSHOT_FILE)
#     if not snapshot_path.exists():
#         return False, "No shadow snapshot found to revert to."

#     sha = snapshot_path.read_text(encoding="utf-8").strip()
#     if not sha:
#         return False, "Recorded snapshot SHA is invalid or empty."

#     # Restore working tree files from the dangling commit
#     code, stdout, stderr = _run_git(["checkout", sha, "--", "."])
    
#     if code == 0:
#         return True, f"Successfully restored working tree to shadow snapshot ({sha[:8]})."
    
#     return False, f"Failed to restore: {stderr or stdout}"




import subprocess
from pathlib import Path
from config import get_snapshot_file

def _run_git(args: list[str]) -> tuple[int, str, str]:
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def create_shadow_snapshot() -> str | None:
    snapshot_path = get_snapshot_file()
    if not snapshot_path:
        return None

    code, sha, _ = _run_git(["stash", "create", "-u"])
    if not sha:
        code, sha, _ = _run_git(["stash", "create"])

    if not sha:
        code, head_sha, _ = _run_git(["rev-parse", "--verify", "HEAD"])
        if code == 0 and head_sha:
            sha = head_sha

    if sha:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(sha, encoding="utf-8")
        return sha

    return None

def execute_panic_revert() -> tuple[bool, str]:
    snapshot_path = get_snapshot_file()
    if not snapshot_path or not snapshot_path.exists():
        return False, "No shadow snapshot found for this repository."

    sha = snapshot_path.read_text(encoding="utf-8").strip()
    if not sha:
        return False, "Snapshot reference is empty."

    code, stdout, stderr = _run_git(["checkout", sha, "--", "."])
    if code == 0:
        return True, f"Restored current repository from shadow snapshot ({sha[:8]})."
    
    return False, f"Failed to restore: {stderr or stdout}"