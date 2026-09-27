# import subprocess
# import os
# from config import get_encoding_config

# def run_git(args: list[str]) -> str:
#     try:
#         res = subprocess.run(
#             ["git"] + args, 
#             capture_output=True, 
#             text=True, 
#             **get_encoding_config()
#         )
#         return res.stdout.strip()
#     except Exception:
#         return ""

# def is_git_repository() -> bool:
#     return run_git(["rev-parse", "--is-inside-work-tree"]) == "true"

# def get_git_state() -> dict:
#     status_raw = run_git(["status", "--porcelain"])
    
#     staged = run_git(["diff", "--name-only", "--cached"]).splitlines()
#     unstaged = run_git(["diff", "--name-only"]).splitlines()
#     untracked = [line[3:] for line in status_raw.splitlines() if line.startswith("??")]

#     return {
#         "branch": run_git(["branch", "--show-current"]) or "DETACHED",
#         "is_dirty": len(status_raw) > 0,
#         "staged_files": staged,
#         "unstaged_files": unstaged,
#         "untracked_files": untracked,
#         "last_commit": run_git(["log", "-n", "1", "--oneline"]) or "Initial State (No Commits)",
#         "merge_in_progress": os.path.exists(os.path.join(".git", "MERGE_HEAD"))
#     }




import subprocess
import os
from pathlib import Path

def run_git(args: list[str]) -> str:
    """Executes non-destructive git commands with explicit utf-8 handling."""
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.stdout.strip()
    except Exception:
        return ""

def is_git_repository() -> bool:
    return run_git(["rev-parse", "--is-inside-work-tree"]).lower() == "true"

def get_git_state() -> dict:
    status_raw = run_git(["status", "--porcelain"])
    
    staged = [f for f in run_git(["diff", "--name-only", "--cached"]).splitlines() if f]
    unstaged = [f for f in run_git(["diff", "--name-only"]).splitlines() if f]
    untracked = [line[3:].strip() for line in status_raw.splitlines() if line.startswith("??")]

    # Detect current branch with fallback for unborn branches (fresh repo before first commit)
    current_branch = run_git(["branch", "--show-current"])
    if not current_branch:
        # Check symbolic-ref in case of fresh repo
        sym_ref = run_git(["symbolic-ref", "--short", "HEAD"])
        current_branch = sym_ref if sym_ref else "DETACHED"

    # Git directory path (handles submodules, worktrees, and regular repos)
    git_dir = run_git(["rev-parse", "--git-dir"]) or ".git"
    merge_head = Path(git_dir) / "MERGE_HEAD"

    return {
        "branch": current_branch,
        "is_dirty": len(status_raw) > 0,
        "staged_files": staged,
        "unstaged_files": unstaged,
        "untracked_files": untracked,
        "last_commit": run_git(["log", "-n", "1", "--oneline"]) or "Initial State (No Commits)",
        "merge_in_progress": merge_head.exists()
    }