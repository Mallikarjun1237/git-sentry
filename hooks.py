import sys
import os
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

def install_shell_alias() -> tuple[bool, str]:
    """Adds 'gs' alias for git-sentry across Windows PowerShell and Unix shells."""
    try:
        if sys.platform == "win32":
            # Ask PowerShell directly for its resolved $PROFILE path
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Write-Output $PROFILE"],
                capture_output=True,
                text=True,
                check=True
            )
            profile_path_str = res.stdout.strip()
            if not profile_path_str:
                profile_path = Path.home() / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
            else:
                profile_path = Path(profile_path_str)

            profile_path.parent.mkdir(parents=True, exist_ok=True)
            alias_line = "\nSet-Alias -Name gs -Value git-sentry -ErrorAction SilentlyContinue\n"

            if profile_path.exists():
                content = profile_path.read_text(encoding="utf-8", errors="replace")
                if "Set-Alias -Name gs" in content:
                    return True, f"Alias 'gs' already configured in: {profile_path}"

            with open(profile_path, "a", encoding="utf-8") as f:
                f.write(alias_line)
            return True, f"Installed PowerShell alias 'gs' in: {profile_path}"
        else:
            home = Path.home()
            for shell_file in [home / ".bashrc", home / ".zshrc"]:
                if shell_file.exists():
                    content = shell_file.read_text(encoding="utf-8", errors="replace")
                    if "alias gs=" not in content:
                        with open(shell_file, "a", encoding="utf-8") as f:
                            f.write("\nalias gs='git-sentry'\n")
            return True, "Installed 'gs' alias in ~/.bashrc and ~/.zshrc"
    except Exception as e:
        return False, f"Failed to install alias: {e}"