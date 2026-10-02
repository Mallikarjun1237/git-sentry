# Git-Sentry 🛡️

### AI-Powered Git Safety & Security CLI

Git-Sentry is a security-first command-line tool that makes Git safer and easier to use.

It allows developers to describe Git operations in **natural language**, analyzes the current repository before acting, detects potential secrets, evaluates the risk of an operation, and creates local recovery snapshots before potentially destructive changes.

Instead of remembering complex Git commands, you can say:

```bash
gs run "undo my last commit but keep my code changes"
```
Git-Sentry determines the appropriate Git operation, shows its potential impact, and applies safety checks before execution.

---

## 🚀 Why Git-Sentry?

Git is powerful, but some commands can easily cause accidental data loss or security problems.

Examples include:

```bash
git reset --hard
git clean -fd
git checkout .
git push --force
```

There are also common problems such as:

* Accidentally committing `.env` files or API keys
* Difficulty remembering complex Git commands
* Accidentally deleting uncommitted work
* Difficult merge conflicts
* Using generic AI tools that cannot see the actual state of your local repository

Git-Sentry adds a safety layer between the developer and Git.

---

# 🧠 How It Works

Git-Sentry follows a four-stage pipeline:

```text
Natural Language Request
          ↓
Local Git Context + Security Scan
          ↓
Intent & Risk Analysis
          ↓
Safety Check / Snapshot
          ↓
Git Execution
          ↓
Recovery if Required
```

### 1. Understand the repository

Git-Sentry examines the current Git state, including:

* Current branch
* HEAD
* Staged changes
* Working-tree changes
* Untracked files
* Relevant diffs
* Conflict markers

It uses this information to understand what the requested operation could affect.

### 2. Scan for secrets

Before operations that interact with files, Git-Sentry can scan for potential credentials using:

* Regex-based detection
* Shannon entropy analysis

It is designed to detect common credentials such as AWS keys, GitHub tokens, Google API keys and private keys, while entropy analysis helps identify less recognizable secrets.

### 3. Analyze the requested operation

For supported complex requests, Git-Sentry uses the Gemini API with structured JSON output.

The planning stage produces:

* Git command
* Risk level
* Blast-radius explanation
* Potentially affected files

### 4. Execute safely

Operations are classified as:

| Level               | Meaning                                                                |
| ------------------- | ---------------------------------------------------------------------- |
| **SAFE**            | Read-only operations can execute automatically                         |
| **CAUTION**         | Requires confirmation                                                  |
| **CRITICAL_HAZARD** | Destructive operation; high-visibility warning and snapshot protection |

For risky operations, Git-Sentry can create a local snapshot before execution.

---

# ✨ Key Features

### Natural-Language Git

Describe what you want instead of constructing the Git command yourself.

```bash
gs run "show what changed in the last 2 commits"
```

```bash
gs run "create a new branch called feature-auth"
```

```bash
gs run "stash only my Python files"
```

---

### 🔐 Secret Detection

Git-Sentry combines:

```text
Regex Detection
       +
Shannon Entropy
```

to identify potential secrets before they become part of Git history.

It can also provide a quarantine workflow for sensitive files such as `.env`.

---

### 💥 Blast-Radius Analysis

Before executing risky operations, Git-Sentry shows what could be affected, including the branch and files at risk.

---

### 🛡️ Safety Tiers

Git-Sentry distinguishes between safe, caution-level and potentially destructive operations rather than treating every Git command equally.

---

### 🔄 Local Recovery

Before a hazardous operation, Git-Sentry can create a local snapshot.

If something goes wrong:

```bash
gs panic
```

can restore the latest applicable snapshot.

---

### 🔀 Conflict Resolution

Git-Sentry can inspect Git conflict markers and analyze the conflicting sections to suggest a contextual resolution.

```bash
gs resolve path/to/conflicted_file.py
```

---

### 🪝 Git Hook Protection

Install Git-Sentry as a pre-commit hook:

```bash
gs install-hook
```

Future commits can then be checked for potential secrets using the project's regex and entropy scanners.

---

# 📦 Installation

## Requirements

* Python **3.10+**
* Git
* Gemini API key
* pipx recommended

### Install pipx

**Windows:**

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

**macOS / Linux:**

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

### Install Git-Sentry

From GitHub:

```bash
pipx install git+https://github.com/Mallikarjun1237/git-sentry.git
```

For local development:

```bash
cd git-sentry
pipx install --editable .
```

---

# ⚙️ Configuration

Run:

```bash
git-sentry configure
```

The setup wizard configures:

1. Gemini API key
2. Snapshot directory
3. Gemini model

Configuration is stored locally under:

```text
Windows:
C:\Users\<YourUser>\.git-sentry\config.json

macOS/Linux:
~/.git-sentry/config.json
```

---

# 🔗 Using `gs`

Git-Sentry can install a global `gs` shortcut:

```bash
git-sentry install-alias
```

After configuring the alias, you can use:

```bash
gs run "..."
```

from Git repositories on your system.

---

# 💻 Command Reference

## Run a Git operation

```bash
gs run "<request>"
```

Examples:

```bash
gs run "show what changed in the last 2 commits"
```

```bash
gs run "undo my previous commit but keep all my code"
```

```bash
gs run "squash the last 3 commits into one"
```

---

## Recover from a snapshot

```bash
gs panic
```

---

## Resolve a conflict

```bash
gs resolve path/to/file.py
```

---

## Install pre-commit protection

```bash
gs install-hook
```

---

## Configure Git-Sentry

```bash
gs configure
```

---

# 🔒 Privacy & Security

Git-Sentry is designed to keep repository processing local wherever possible.

According to the project design:

* It does **not upload the entire repository**.
* Only relevant metadata, intent and required diff/conflict context are processed by the AI layer.
* Configuration and snapshots are stored locally.
* No third-party analytics or tracking telemetry is used.

However, complex AI operations require communication with the Gemini API.

Basic deterministic operations can use the local fast path without requiring an AI request.

---

# ⚠️ Limitations

Git-Sentry is a safety layer, not a replacement for Git or a guarantee against every possible mistake.

### Repository scope

Submodules and nested repositories need to be handled from their respective repository directories.

### Large files

Files larger than the configured scan limit are skipped by the secret scanner. The documented default is **1 MB**.

### Large conflicts

Very large conflict sections may be split or truncated before AI processing.

### Internet dependency

Basic local operations can work through the deterministic path, but complex natural-language planning and AI conflict resolution require Gemini connectivity.

---

# 🏗️ Project Structure

```text
git-sentry/
│
├── git_sentry/
│   ├── cli.py
│   ├── agent.py
│   ├── scanner.py
│   ├── snapshot.py
│   ├── context.py
│   ├── hooks.py
│   ├── config.py
│   └── __init__.py
│
├── tests/
├── pyproject.toml
├── README.md
└── LICENSE
```

| File          | Responsibility                           |
| ------------- | ---------------------------------------- |
| `cli.py`      | CLI commands and terminal interface      |
| `agent.py`    | Gemini integration and command planning  |
| `scanner.py`  | Regex and entropy-based secret detection |
| `snapshot.py` | Snapshot creation and recovery           |
| `context.py`  | Local Git repository inspection          |
| `hooks.py`    | Git hooks and shell alias installation   |
| `config.py`   | Configuration and model management       |

The documented architecture separates repository context, security scanning, AI planning, snapshots, and CLI functionality into these modules.

---

# 🛠️ Technology Stack

* **Python 3.10+**
* **Typer** — CLI framework
* **Rich** — terminal interface
* **Git** — repository operations
* **Gemini API** — natural-language planning
* **Regex + Shannon Entropy** — secret detection
* **Git Object Database** — snapshots
* **Zlib** — snapshot compression
* **Git Hooks** — commit protection
* **pytest** — testing
* **mypy** — static type checking

---

# 🧪 Development

Clone the repository:

```bash
git clone https://github.com/Mallikarjun1237/git-sentry.git
cd git-sentry
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

**Windows:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests/
```

Run type checking:

```bash
mypy git_sentry/
```

---

# 🧹 Uninstallation

Remove the CLI:

```bash
pipx uninstall git-sentry
```

Remove the local configuration and snapshots:

**Windows:**

```powershell
Remove-Item -Recurse -Force "$HOME\.git-sentry"
```

**macOS/Linux:**

```bash
rm -rf ~/.git-sentry
```

Also remove the `gs` alias from your shell profile if it was installed.

---

# 🌟 What Makes Git-Sentry Unique?

Git-Sentry combines several capabilities into one Git workflow:

```text
Natural Language
      +
Real Git Context
      +
Secret Detection
      +
Risk Analysis
      +
Pre-Execution Snapshot
      +
Git Execution
      +
Recovery
```

A generic AI assistant can explain a Git command, but it does not inherently have access to the current state of the developer's local repository.

Git-Sentry is designed specifically to connect **AI reasoning with actual local Git state and safety mechanisms**.

That combination is the core idea behind the project.

---

# 📄 License

See the `LICENSE` file for the project's open-source license.

---

## Git-Sentry in One Line

> **Describe what you want to do with Git. Git-Sentry understands the repository, checks the risks, protects sensitive data, and helps you execute the operation safely.**
