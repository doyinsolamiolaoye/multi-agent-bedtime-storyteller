"""
Story Arc Planner Agent
───────────────────────
Given a user request and its category metadata, produces a structured
5-beat narrative outline (Setup → Rising Action → Climax → Falling
Action → Resolution) with a moral and character arc description.
"""

from config import call_model_json, PRECISE_TEMPERATURE
from prompts import STORY_ARC_PROMPT

# Fallback outline when the LLM response can't be parsed
_DEFAULT_ARC = {
    "setup": "Introduce the main character and their world.",
    "rising_action": "A challenge or adventure begins.",
    "climax": "The most exciting moment of the story.",
    "falling_action": "The character finds a solution.",
    "resolution": "A happy ending with a gentle lesson.",
    "moral": "Be kind and brave.",
    "character_arc": "The character grows through their experience.",
}


def plan_arc(request: str, category: dict) -> dict:
    """Return a dict describing the 5-beat story arc plus moral & character arc."""
    prompt = STORY_ARC_PROMPT.format(
        request=request,
        category=category.get("category", "general"),
        themes=", ".join(category.get("themes", [])),
        characters=", ".join(category.get("characters", [])),
        tone=category.get("tone", "warm and playful"),
    )
    result = call_model_json(prompt, temperature=PRECISE_TEMPERATURE)

    if "error" in result:
        print("  ⚠  Arc Planner: could not parse LLM output — using defaults.")
        return dict(_DEFAULT_ARC)

    # Ensure every expected key is present
    for key, default in _DEFAULT_ARC.items():
        result.setdefault(key, default)

    return result
