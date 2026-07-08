"""
Categorizer Agent
─────────────────
Analyses a user's story request and classifies it into a category
(adventure, fantasy, animal, friendship, mystery, educational,
fairy-tale, or general) along with extracted themes, characters,
tone, and setting suggestions.
"""

from config import call_model_json, PRECISE_TEMPERATURE
from prompts import CATEGORIZER_PROMPT

# Sensible defaults when the LLM response can't be parsed
_DEFAULTS = {
    "category": "general",
    "themes": ["friendship", "adventure"],
    "characters": [],
    "tone": "warm and playful",
    "setting_suggestions": ["a magical forest"],
}


def categorize(request: str) -> dict:
    """Return a dict with keys: category, themes, characters, tone, setting_suggestions."""
    prompt = CATEGORIZER_PROMPT.format(request=request)
    result = call_model_json(prompt, temperature=PRECISE_TEMPERATURE)

    if "error" in result:
        print("  ⚠  Categorizer: could not parse LLM output — using defaults.")
        return dict(_DEFAULTS)

    # Ensure every expected key is present
    for key, default in _DEFAULTS.items():
        result.setdefault(key, default)

    return result
