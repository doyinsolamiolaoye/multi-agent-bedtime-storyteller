"""
Configuration and shared LLM interface for the Story-Teller Agent.

All agent modules import `call_model` and `call_model_json` from here
to keep the OpenAI interaction in one place and avoid circular imports.
"""

import os
import json

from dotenv import load_dotenv
import openai

# ---------------------------------------------------------------------------
# Load environment variables from .env (if present)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Model configuration  (DO NOT change the model name per assignment rules)
# ---------------------------------------------------------------------------
MODEL_NAME = "gpt-3.5-turbo"
DEFAULT_MAX_TOKENS = 3000
CREATIVE_TEMPERATURE = 0.8   # Used for story generation — more imaginative
PRECISE_TEMPERATURE = 0.1    # Used for judge / categorizer — more deterministic

# ---------------------------------------------------------------------------
# Judge configuration
# ---------------------------------------------------------------------------
JUDGE_PASS_THRESHOLD = 7     # Minimum overall score (out of 10) to accept a story
MAX_REFINEMENT_ITERATIONS = 3  # Cap on judge→refine loops

# ---------------------------------------------------------------------------
# OpenAI client (v1+ SDK)
# ---------------------------------------------------------------------------
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Shared LLM helpers
# ---------------------------------------------------------------------------

def call_model(
    prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = PRECISE_TEMPERATURE,
    system_prompt: str | None = None,
) -> str:
    """Send a chat-completion request and return the assistant's text."""
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content  # type: ignore[return-value]


def call_model_json(
    prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = PRECISE_TEMPERATURE,
    system_prompt: str | None = None,
) -> dict:
    """Call the model and attempt to parse the response as JSON.

    Falls back to substring extraction when the model wraps JSON in prose.
    Returns ``{"error": ..., "raw_response": ...}`` on total failure.
    """
    raw = call_model(prompt, max_tokens, temperature, system_prompt)

    # --- Attempt 1: direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # --- Attempt 2: extract the first top-level { … } block
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass

    return {"error": "Failed to parse JSON from model response", "raw_response": raw}
