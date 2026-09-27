# import os
# from dotenv import load_dotenv
# from pydantic import BaseModel, Field
# from google import genai
# from typing import Literal
# import time
# from google.genai.errors import ServerError
# from google.genai import types

# load_dotenv()

# class GitPlan(BaseModel):
#     command: str = Field(description="The suggested bash Git command")
#     explanation: str = Field(description="Brief breakdown of what it does")
#     risk_level: Literal["SAFE", "CAUTION", "CRITICAL_HAZARD"]
#     blast_radius_summary: str = Field(description="Affected scope summary")
#     files_at_risk: list[str] = Field(description="Files facing deletion/modification")
#     undo_command: str = Field(description="Recovery command")

# def analyze_and_plan(user_query: str, git_state: dict, secrets_found: list) -> GitPlan:
#     gen_config = types.GenerateContentConfig(
#         response_mime_type="application/json",
#         response_schema=GitPlan,
#         temperature=0.2,
#     )
#     client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
#     prompt = f"""
#     Context: {git_state}
#     Secrets Detected: {secrets_found}
#     User Intent: {user_query}

#     Task: Provide a Git command. 
#     Rules:
#     1. If user asks to reset, clean, or force push, risk is CRITICAL_HAZARD.
#     2. Never use shell redirection ('>').
#     3. If secrets were found and the user is trying to 'push' or 'commit', warn them.
#     CRITICAL OS ENVIRONMENT RULE:
#     The host operating system is Windows running PowerShell.
#     - NEVER suggest Linux/Unix-only utilities like `sed`, `awk`, or `grep`.
#     - For file updates or text replacements, output standard Git commands or self-contained Python one-liners.
#     """

#     for attempt in range(2):
#         try:
#             response = client.models.generate_content(
#                 model="gemini-3.6-flash",  # fallback or stable flash
#                 contents=prompt,
#                 config=gen_config,
#             )
#             return response.parsed
#         except ServerError:
#             if attempt == 0:
#                 time.sleep(1.5)  # brief wait for temporary spike to clear
#                 continue
#             raise

#     return response.parsed




# import os
# import time
# from typing import Literal
# from dotenv import load_dotenv
# from pydantic import BaseModel, Field
# from google import genai
# from google.genai import types
# from google.genai.errors import ServerError

# load_dotenv()

# class GitPlan(BaseModel):
#     command: str = Field(description="The suggested bash Git command")
#     explanation: str = Field(description="Brief breakdown of what it does")
#     risk_level: Literal["SAFE", "CAUTION", "CRITICAL_HAZARD"]
#     blast_radius_summary: str = Field(description="Affected scope summary")
#     files_at_risk: list[str] = Field(
#         default_factory=list, 
#         description="Files facing deletion or modification"
#     )
#     undo_command: str = Field(description="Recovery command")

# def analyze_and_plan(user_query: str, git_state: dict, secrets_found: list) -> GitPlan:
#     gen_config = types.GenerateContentConfig(
#         response_mime_type="application/json",
#         response_schema=GitPlan,
#         temperature=0.1,
#     )
    
#     # Check both common environment variable names
#     api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
#     client = genai.Client(api_key=api_key)
    
#     prompt = f"""
#     Context: {git_state}
#     Secrets Detected: {secrets_found}
#     User Intent: {user_query}

#     Task: Formulate the safest, most accurate Git command to achieve the user's intent.

#     RISK CLASSIFICATION RULES:
#     1. SAFE: Read-only inspection commands that do not alter repository state, files, or remotes.
#        Examples: git status, git log, git diff, git show, git branch, git remote -v.
#     2. CAUTION: Operations that create commits, stage files, or switch branches without deleting local work.
#        Examples: git add, git commit, git checkout -b, git switch, git stash.
#     3. CRITICAL_HAZARD: Irreversible operations, destructive resets, forced overwrites, or data discards.
#        Examples: git reset --hard, git clean -fd, git push --force, git restore ., git checkout -- .

#     CRITICAL OS & ENVIRONMENT RULES:
#     - The host operating system is Windows running PowerShell.
#     - NEVER suggest Linux/Unix utilities like `sed`, `awk`, or `grep`.
#     - NEVER use shell file redirection operators (`>` or `>>`). For file updates, use self-contained Python one-liners with explicit utf-8 encoding.
#     - If secrets are detected and the user is attempting to stage, commit, or push, classify as CRITICAL_HAZARD.
#     """

#     last_error = None
#     for attempt in range(2):
#         try:
#             response = client.models.generate_content(
#                 model="gemini-3.6-flash",
#                 contents=prompt,
#                 config=gen_config,
#             )
#             return response.parsed
#         except ServerError as e:
#             last_error = e
#             if attempt == 0:
#                 time.sleep(1.5)
#                 continue
#             raise last_error

#     raise RuntimeError("Failed to generate plan after retry attempts.")




# import os
# import time
# from typing import Literal
# from dotenv import load_dotenv
# from pydantic import BaseModel, Field
# from google import genai
# from google.genai import types
# from google.genai.errors import ServerError
# from config import get_global_api_key

# load_dotenv()

# class GitPlan(BaseModel):
#     command: str = Field(description="The suggested bash Git command")
#     explanation: str = Field(description="Brief breakdown of what it does")
#     risk_level: Literal["SAFE", "CAUTION", "CRITICAL_HAZARD"]
#     blast_radius_summary: str = Field(description="Affected scope summary")
#     files_at_risk: list[str] = Field(
#         default_factory=list, 
#         description="Files facing deletion or modification"
#     )
#     undo_command: str = Field(description="Recovery command")

# def analyze_and_plan(user_query: str, git_state: dict, secrets_found: list) -> GitPlan:
#     api_key = get_global_api_key()
#     if not api_key:
#         raise ValueError("Missing Gemini API Key. Run 'git-sentry configure' or set GEMINI_API_KEY.")

#     client = genai.Client(api_key=api_key)
    
#     gen_config = types.GenerateContentConfig(
#         response_mime_type="application/json",
#         response_schema=GitPlan,
#         temperature=0.1,
#     )
    
#     prompt = f"""
#     Context: {git_state}
#     Secrets Detected: {secrets_found}
#     User Intent: {user_query}

#     Task: Formulate the safest, most accurate Git command to achieve the user's intent.

#     RISK CLASSIFICATION RULES:
#     1. SAFE: Read-only inspection commands that do not alter repository state, files, or remotes.
#        Examples: git status, git log, git diff, git show, git branch, git remote -v.
#     2. CAUTION: Operations that create commits, stage files, or switch branches without deleting local work.
#        Examples: git add, git commit, git checkout -b, git switch, git stash.
#     3. CRITICAL_HAZARD: Irreversible operations, destructive resets, forced overwrites, or data discards.
#        Examples: git reset --hard, git clean -fd, git push --force, git restore ., git checkout -- .

#     CRITICAL OS & ENVIRONMENT RULES:
#     - The host operating system is Windows running PowerShell.
#     - NEVER suggest Linux/Unix utilities like `sed`, `awk`, or `grep`.
#     - NEVER use shell file redirection operators (`>` or `>>`).
#     - If secrets are detected and the user is attempting to stage, commit, or push, classify as CRITICAL_HAZARD.
#     """

#     last_error = None
#     for attempt in range(2):
#         try:
#             response = client.models.generate_content(
#                 model="gemini-3.6-flash",
#                 contents=prompt,
#                 config=gen_config,
#             )
#             return response.parsed
#         except ServerError as e:
#             last_error = e
#             if attempt == 0:
#                 time.sleep(1.5)
#                 continue
#             raise last_error

#     raise RuntimeError("Failed to generate plan after retry attempts.")




import os
import time
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from config import get_global_api_key,get_selected_model, get_repo_root

load_dotenv()

class CommandExplanation(BaseModel):
    command: str = Field(description="The command analyzed")
    breakdown: str = Field(description="Plain English explanation of each argument and action")
    state_changes: str = Field(description="What will happen to the working tree, staging area, and commit history")
    risk_level: Literal["SAFE", "CAUTION", "CRITICAL_HAZARD"]
    safe_alternative: str = Field(description="Safer or more standard alternative command, if applicable")

def explain_raw_command(raw_command: str, git_state: dict) -> CommandExplanation:
    api_key = get_global_api_key()
    if not api_key:
        raise ValueError("Missing Gemini API Key. Run 'git-sentry configure'.")

    client = genai.Client(api_key=api_key)
    gen_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=CommandExplanation,
        temperature=0.1,
    )

    prompt = f"""
    Repository State: {git_state}
    Command to Explain: {raw_command}

    Task:
    Provide an accurate breakdown of the provided Git command.
    Detail its side effects on the working directory, stage, and remote branches.
    Classify its risk level and suggest a safer alternative if applicable.
    """

    response = client.models.generate_content(
        model=get_selected_model(),
        contents=prompt,
        config=gen_config
    )
    return response.parsed


class GitPlan(BaseModel):
    command: str = Field(description="The suggested bash Git command")
    explanation: str = Field(description="Brief breakdown of what it does")
    risk_level: Literal["SAFE", "CAUTION", "CRITICAL_HAZARD"]
    blast_radius_summary: str = Field(description="Affected scope summary")
    files_at_risk: list[str] = Field(
        default_factory=list, 
        description="Files facing deletion or modification"
    )
    undo_command: str = Field(description="Recovery command")

# 0ms Latency Fast-Path for simple status queries (Bypasses API & saves quota)
FAST_PATH_MAP = {
    "status": GitPlan(
        command="git status",
        explanation="Displays working tree status and branch state.",
        risk_level="SAFE",
        blast_radius_summary="Read-only operation; zero changes to repo state.",
        files_at_risk=[],
        undo_command="None needed"
    ),
    "branch": GitPlan(
        command="git branch -a",
        explanation="Lists all local and remote branches.",
        risk_level="SAFE",
        blast_radius_summary="Read-only operation.",
        files_at_risk=[],
        undo_command="None needed"
    ),
    "log": GitPlan(
        command="git log --oneline -n 10",
        explanation="Displays recent commit history in compact format.",
        risk_level="SAFE",
        blast_radius_summary="Read-only operation.",
        files_at_risk=[],
        undo_command="None needed"
    ),
    "diff": GitPlan(
        command="git diff",
        explanation="Displays unstaged line changes in the working tree.",
        risk_level="SAFE",
        blast_radius_summary="Read-only operation.",
        files_at_risk=[],
        undo_command="None needed"
    ),
}

def analyze_and_plan(user_query: str, git_state: dict, secrets_found: list) -> GitPlan:
    query_clean = user_query.strip().lower()

    # 1. Check local fast-path first (Instant, zero quota consumed)
    for trigger, fast_plan in FAST_PATH_MAP.items():
        if query_clean == trigger or query_clean == f"git {trigger}":
            return fast_plan

    # 2. Prepare API client
    api_key = get_global_api_key()
    if not api_key:
        raise ValueError("Missing Gemini API Key. Run 'git-sentry configure' or set GEMINI_API_KEY.")

    client = genai.Client(api_key=api_key)
    
    gen_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=GitPlan,
        temperature=0.1,
    )
    
    prompt = f"""
    Context: {git_state}
    Secrets Detected: {secrets_found}
    User Intent: {user_query}

    Task: Formulate the safest, most accurate Git command for Windows PowerShell.

    RISK RULES:
    - SAFE: Read-only (status, log, diff, show, branch).
    - CAUTION: Add, commit, switch, stash.
    - CRITICAL_HAZARD: Hard resets, clean, force push, restores.
    """

    # Low-latency model list: tries fast Flash first, then Flash-Lite if congested
    candidate_models = ["gemini-3.8-flash", "gemini-2.5-flash-lite"]
    last_error = None

    for model_name in candidate_models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=gen_config,
                )
                return response.parsed
            except ServerError as e:
                last_error = e
                time.sleep(1.0)
                continue
            except ClientError as e:
                # 429 quota or rate limits -> fallback to next candidate model
                last_error = e
                break

    raise last_error if last_error else RuntimeError("Inference request failed.")

