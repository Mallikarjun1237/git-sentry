import sys
import stat
from pathlib import Path
from config import get_repo_root

HOOK_TEMPLATE = """#!/bin/sh
# Git-Sentry Automated Pre-Flight Safety Hook
echo "🛡️  Running Git-Sentry pre-flight safety check..."

# Run secret scan
git-sentry scan --hook-mode
SCAN_EXIT=$?

if [ $SCAN_EXIT -ne 0 ]; then
    echo "❌ Git-Sentry: Commit/Push aborted due to exposed credentials."
    exit 1
fi

echo "✅ Git-Sentry: Pre-flight checks passed."
exit 0
"""

def install_hooks() -> tuple[bool, str]:
    root = get_repo_root()
    if not root:
        return False, "Not inside a valid Git repository."

    hooks_dir = root / ".git" / "hooks"
    if not hooks_dir.exists():
        hooks_dir.mkdir(parents=True, exist_ok=True)

    targets = [hooks_dir / "pre-commit", hooks_dir / "pre-push"]
    for hook_file in targets:
        hook_file.write_text(HOOK_TEMPLATE, encoding="utf-8")
        # Ensure executable permissions
        try:
            current_perms = hook_file.stat().st_mode
            hook_file.chmod(current_perms | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass

    return True, f"Installed Git-Sentry hooks in: {hooks_dir}"