import subprocess
from pathlib import Path
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from config import get_global_api_key, get_selected_model, get_repo_root

class ConflictResolution(BaseModel):
    file_path: str = Field(description="Path to the resolved file")
    resolved_content: str = Field(description="Entire content of the file with conflict markers resolved")
    explanation: str = Field(description="Rationale for merging changes")

def find_conflicted_files() -> list[str]:
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        return files
    except Exception:
        return []

def resolve_file_conflict(file_path: str) -> ConflictResolution:
    api_key = get_global_api_key()
    if not api_key:
        raise ValueError("Missing Gemini API Key. Run 'git-sentry configure' first.")

    root = get_repo_root() or Path(".")
    target_path = root / file_path
    
    if not target_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    raw_content = target_path.read_text(encoding="utf-8", errors="replace")

    client = genai.Client(api_key=api_key)
    gen_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ConflictResolution,
        temperature=0.1,
    )

    prompt = f"""
    The following file has Git merge conflict markers (<<<<<<<, =======, >>>>>>>).
    File Path: {file_path}

    File Contents:
    {raw_content}

    Task:
    Analyze both branches' intents and produce a syntactically correct, reconciled version of the complete file.
    Remove all conflict marker lines entirely.
    """

    response = client.models.generate_content(
        model=get_selected_model(),
        contents=prompt,
        config=gen_config
    )
    return response.parsed