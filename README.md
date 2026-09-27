
# Git-Sentry 🛡️
> Autonomous Pre-Flight Blast-Radius Analyzer, Secret Quarantine & Disaster-Recovery CLI for Git.

## Quick Installation

```bash
# Recommended via pipx
pipx install git+[https://github.com/](https://github.com/)Mallikarjun1237/git-sentry.git

# Or via pip
pip install git+[https://github.com/](https://github.com/)Mallikarjun1237/git-sentry.git

# Git-Sentry 🛡️

> **Autonomous Pre-Flight Blast-Radius Analyzer, Secret Quarantine & Disaster-Recovery CLI for Git.**

Git-Sentry is a deterministic safety proxy that intercepts natural language commands and raw Git execution. It maps repository blast radius, flags exposed credentials, creates silent recovery snapshots, and gates destructive changes before data loss or remote leaks can occur.

---

## Architecture Overview

```text
[ User Prompt / Raw Intent ]
             │
             ▼
┌─────────────────────────────────────────┐
│ 1. Git State Probe (`context.py`)       │ ──> Working tree, index, remotes, branches
│ 2. Deterministic Regex (`scanner.py`)   │ ──> High-entropy secrets, Bearer tokens
└─────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 3. Agentic Risk Engine (`agent.py`)     │ ──> Powered by Gemini 3.6 Flash
│    - Evaluates Blast Radius Matrix      │ ──> Classifies: SAFE | CAUTION | CRITICAL_HAZARD
└─────────────────────────────────────────┘
             │
             ▼
   [ Autonomous Gate (`cli.py`) ]
   ├── [SAFE] (Read-only status/diff/log) ───────────► Execute Autonomously (Zero Prompts)
   ├── [Credentials Detected] ───────────────────────► HARD BLOCK on Staging & Commits
   └── [CAUTION / CRITICAL_HAZARD] ──────────────────► Interactive Impact Dashboard
                                                             │
                                                     (User Confirms)
                                                             ▼
                                                ┌─────────────────────────┐
                                                │ 4. Shadow Snapshot      │
                                                │    (`snapshot.py`)      │
                                                └─────────────────────────┘
                                                             │
                                                             ▼
                                                    [ Execute Command ]
                                                             │
                                                    (Accidental Wipe?)
                                                             ▼
                                                ┌─────────────────────────┐
                                                │ 5. Panic Revert Engine  │
                                                │    `git-sentry panic`   │
                                                └─────────────────────────┘