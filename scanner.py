import re
import subprocess
import os
from config import SECRET_PATTERNS, get_encoding_config

def scan_working_tree_for_secrets() -> list[dict]:
    findings = []
    # Scan staged and unstaged changes
    diff_content = subprocess.run(
        ["git", "diff", "HEAD"], 
        capture_output=True, text=True, **get_encoding_config()
    ).stdout

    # Also scan untracked files
    untracked_files = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"], 
        capture_output=True, text=True, **get_encoding_config()
    ).stdout.splitlines()

    # Process Diff
    for name, pattern in SECRET_PATTERNS.items():
        matches = re.finditer(pattern, diff_content)
        for m in matches:
            findings.append({
                "type": name,
                "sample": m.group(0)[:10] + "...",
                "source": "Diff/Staged"
            })

    # Process Untracked Files
    for file_path in untracked_files:
        if os.path.isfile(file_path):
            with open(file_path, "r", errors="ignore") as f:
                content = f.read()
                for name, pattern in SECRET_PATTERNS.items():
                    if re.search(pattern, content):
                        findings.append({
                            "type": name,
                            "sample": "Found in file content",
                            "source": file_path
                        })
    return findings

def quarantine_file(file_path: str):
    with open(".gitignore", "a") as f:
        f.write(f"\n{file_path}\n")
    subprocess.run(["git", "rm", "--cached", file_path], capture_output=True)