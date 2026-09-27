# import re
# import subprocess
# import os
# from config import SECRET_PATTERNS, get_encoding_config

# def scan_working_tree_for_secrets() -> list[dict]:
#     findings = []
#     # Scan staged and unstaged changes
#     diff_content = subprocess.run(
#         ["git", "diff", "HEAD"], 
#         capture_output=True, text=True, **get_encoding_config()
#     ).stdout

#     # Also scan untracked files
#     untracked_files = subprocess.run(
#         ["git", "ls-files", "--others", "--exclude-standard"], 
#         capture_output=True, text=True, **get_encoding_config()
#     ).stdout.splitlines()

#     # Process Diff
#     for name, pattern in SECRET_PATTERNS.items():
#         matches = re.finditer(pattern, diff_content)
#         for m in matches:
#             findings.append({
#                 "type": name,
#                 "sample": m.group(0)[:10] + "...",
#                 "source": "Diff/Staged"
#             })

#     # Process Untracked Files
#     for file_path in untracked_files:
#         if os.path.isfile(file_path):
#             with open(file_path, "r", errors="ignore") as f:
#                 content = f.read()
#                 for name, pattern in SECRET_PATTERNS.items():
#                     if re.search(pattern, content):
#                         findings.append({
#                             "type": name,
#                             "sample": "Found in file content",
#                             "source": file_path
#                         })
#     return findings

# def quarantine_file(file_path: str):
#     with open(".gitignore", "a") as f:
#         f.write(f"\n{file_path}\n")
#     subprocess.run(["git", "rm", "--cached", file_path], capture_output=True)




# import os
# import re
# import subprocess
# from pathlib import Path
# from config import SECRET_PATTERNS

# MAX_SCAN_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB limit per file

# def _run_git_cmd(args: list[str]) -> str:
#     """Helper to run git commands safely with UTF-8 encoding."""
#     try:
#         res = subprocess.run(
#             ["git"] + args,
#             capture_output=True,
#             text=True,
#             encoding="utf-8",
#             errors="replace"
#         )
#         return res.stdout
#     except Exception:
#         return ""

# def scan_working_tree_for_secrets() -> list[dict]:
#     findings = []

#     # 1. Fetch Diff (handles fresh repos without an initial commit)
#     has_head = subprocess.run(
#         ["git", "rev-parse", "--verify", "HEAD"],
#         capture_output=True
#     ).returncode == 0

#     if has_head:
#         diff_content = _run_git_cmd(["diff", "HEAD"])
#     else:
#         # Before initial commit: scan what's currently staged
#         diff_content = _run_git_cmd(["diff", "--cached"])

#     # 2. Fetch Untracked Files
#     raw_untracked = _run_git_cmd(["ls-files", "--others", "--exclude-standard"])
#     untracked_files = [f.strip() for f in raw_untracked.splitlines() if f.strip()]

#     # 3. Process Diff / Staged Changes
#     if diff_content:
#         for name, pattern in SECRET_PATTERNS.items():
#             matches = re.finditer(pattern, diff_content)
#             for m in matches:
#                 sample_text = m.group(0)
#                 obfuscated_sample = sample_text[:8] + "..." if len(sample_text) > 8 else sample_text
#                 findings.append({
#                     "type": name,
#                     "sample": obfuscated_sample,
#                     "source": "Diff/Staged"
#                 })

#     # 4. Process Untracked Files
#     for file_path in untracked_files:
#         path_obj = Path(file_path)
#         if path_obj.is_file():
#             # Skip large files (e.g., binaries, archives, model weights)
#             try:
#                 if path_obj.stat().st_size > MAX_SCAN_FILE_SIZE_BYTES:
#                     continue
#                 content = path_obj.read_text(encoding="utf-8", errors="ignore")
#             except Exception:
#                 continue

#             for name, pattern in SECRET_PATTERNS.items():
#                 if re.search(pattern, content):
#                     findings.append({
#                         "type": name,
#                         "sample": "Detected in file contents",
#                         "source": file_path
#                     })
#                     break  # Avoid logging multiple findings for the exact same file

#     return findings

# def quarantine_file(file_path: str):
#     """Appends unique file path to .gitignore and removes it from the git index if tracked."""
#     gitignore_path = Path(".gitignore")
#     existing_lines = []

#     if gitignore_path.exists():
#         existing_lines = gitignore_path.read_text(encoding="utf-8", errors="ignore").splitlines()

#     # Normalize file path for gitignore (forward slashes)
#     norm_path = file_path.replace("\\", "/")

#     if norm_path not in [line.strip() for line in existing_lines]:
#         with gitignore_path.open("a", encoding="utf-8") as f:
#             if existing_lines and existing_lines[-1].strip() != "":
#                 f.write("\n")
#             f.write(f"{norm_path}\n")

#     # Unstage the file if it was previously staged in index
#     subprocess.run(
#         ["git", "rm", "--cached", "-f", file_path],
#         capture_output=True,
#         text=True,
#         encoding="utf-8",
#         errors="replace"
#     )




import os
import re
import subprocess
from pathlib import Path
from config import SECRET_PATTERNS, get_repo_root

MAX_SCAN_FILE_SIZE_BYTES = 2 * 1024 * 1024

def _run_git_cmd(args: list[str]) -> str:
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.stdout
    except Exception:
        return ""

def scan_working_tree_for_secrets() -> list[dict]:
    findings = []
    has_head = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], capture_output=True).returncode == 0

    diff_content = _run_git_cmd(["diff", "HEAD"]) if has_head else _run_git_cmd(["diff", "--cached"])
    raw_untracked = _run_git_cmd(["ls-files", "--others", "--exclude-standard"])
    untracked_files = [f.strip() for f in raw_untracked.splitlines() if f.strip()]

    if diff_content:
        for name, pattern in SECRET_PATTERNS.items():
            for m in re.finditer(pattern, diff_content):
                sample_text = m.group(0)
                findings.append({
                    "type": name,
                    "sample": sample_text[:8] + "...",
                    "source": "Diff/Staged"
                })

    for file_path in untracked_files:
        path_obj = Path(file_path)
        if path_obj.is_file():
            try:
                if path_obj.stat().st_size > MAX_SCAN_FILE_SIZE_BYTES:
                    continue
                content = path_obj.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for name, pattern in SECRET_PATTERNS.items():
                if re.search(pattern, content):
                    findings.append({
                        "type": name,
                        "sample": "Detected in file contents",
                        "source": file_path
                    })
                    break

    return findings

def quarantine_file(file_path: str):
    root = get_repo_root() or Path(".")
    gitignore_path = root / ".gitignore"
    existing_lines = []

    if gitignore_path.exists():
        existing_lines = gitignore_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    norm_path = file_path.replace("\\", "/")
    if norm_path not in [line.strip() for line in existing_lines]:
        with gitignore_path.open("a", encoding="utf-8") as f:
            if existing_lines and existing_lines[-1].strip() != "":
                f.write("\n")
            f.write(f"{norm_path}\n")

    subprocess.run(["git", "rm", "--cached", "-f", file_path], capture_output=True)