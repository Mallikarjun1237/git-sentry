import subprocess
import os
from config import get_encoding_config

def run_git(args: list[str]) -> str:
    try:
        res = subprocess.run(
            ["git"] + args, 
            capture_output=True, 
            text=True, 
            **get_encoding_config()
        )
        return res.stdout.strip()
    except Exception:
        return ""

def is_git_repository() -> bool:
    return run_git(["rev-parse", "--is-inside-work-tree"]) == "true"

def get_git_state() -> dict:
    status_raw = run_git(["status", "--porcelain"])
    
    staged = run_git(["diff", "--name-only", "--cached"]).splitlines()
    unstaged = run_git(["diff", "--name-only"]).splitlines()
    untracked = [line[3:] for line in status_raw.splitlines() if line.startswith("??")]

    return {
        "branch": run_git(["branch", "--show-current"]) or "DETACHED",
        "is_dirty": len(status_raw) > 0,
        "staged_files": staged,
        "unstaged_files": unstaged,
        "untracked_files": untracked,
        "last_commit": run_git(["log", "-n", "1", "--oneline"]) or "Initial State (No Commits)",
        "merge_in_progress": os.path.exists(os.path.join(".git", "MERGE_HEAD"))
    }