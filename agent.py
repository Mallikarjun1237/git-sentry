import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from typing import Literal
import time
from google.genai.errors import ServerError
from google.genai import types

load_dotenv()

class GitPlan(BaseModel):
    command: str = Field(description="The suggested bash Git command")
    explanation: str = Field(description="Brief breakdown of what it does")
    risk_level: Literal["SAFE", "CAUTION", "CRITICAL_HAZARD"]
    blast_radius_summary: str = Field(description="Affected scope summary")
    files_at_risk: list[str] = Field(description="Files facing deletion/modification")
    undo_command: str = Field(description="Recovery command")

def analyze_and_plan(user_query: str, git_state: dict, secrets_found: list) -> GitPlan:
    gen_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=GitPlan,
        temperature=0.2,
    )
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    prompt = f"""
    Context: {git_state}
    Secrets Detected: {secrets_found}
    User Intent: {user_query}

    Task: Provide a Git command. 
    Rules:
    1. If user asks to reset, clean, or force push, risk is CRITICAL_HAZARD.
    2. Never use shell redirection ('>').
    3. If secrets were found and the user is trying to 'push' or 'commit', warn them.
    CRITICAL OS ENVIRONMENT RULE:
    The host operating system is Windows running PowerShell.
    - NEVER suggest Linux/Unix-only utilities like `sed`, `awk`, or `grep`.
    - For file updates or text replacements, output standard Git commands or self-contained Python one-liners.
    """

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",  # fallback or stable flash
                contents=prompt,
                config=gen_config,
            )
            return response.parsed
        except ServerError:
            if attempt == 0:
                time.sleep(1.5)  # brief wait for temporary spike to clear
                continue
            raise

    return response.parsed