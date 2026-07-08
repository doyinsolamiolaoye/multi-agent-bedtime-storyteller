"""
Safety Filter Agent
───────────────────
Scans generated stories for content that could be frightening, violent,
or otherwise inappropriate for children ages 5-10.  Acts as a hard
guardrail *in addition to* the Judge's scoring — a story must pass
both the Judge AND the Safety Filter before being shown to a child.

Checks for:
  • Frightening imagery (monsters, darkness, being trapped/lost/alone)
  • Violence or aggression (fighting, weapons, hurting)
  • Inappropriate themes (death, divorce, substance abuse, crime)
  • Scary scenarios (abandonment, kidnapping, natural disasters)
  • Negative emotional tone (hopelessness, despair, intense fear)
  • Inappropriate language (insults, name-calling, exclusion)
"""

from config import call_model_json, PRECISE_TEMPERATURE
from prompts import SAFETY_FILTER_PROMPT

# Fallback result when parsing fails — defaults to SAFE so we don't
# block the pipeline on a parsing error (the Judge still provides
# a separate quality gate).
_DEFAULT_RESULT = {
    "is_safe": True,
    "flags": [],
    "severity": "none",
    "explanation": "Unable to evaluate safety — defaulting to safe.",
    "suggested_changes": [],
}


def check_safety(story: str) -> dict:
    """Scan a story and return a safety evaluation.

    Returns a dict with:
        is_safe (bool)           — True if the story passes all checks
        flags (list[str])        — List of specific safety concerns found
        severity (str)           — "none", "low", "medium", or "high"
        explanation (str)        — Human-readable summary of concerns
        suggested_changes (list) — Actionable fixes for each flagged issue
    """
    prompt = SAFETY_FILTER_PROMPT.format(story=story)
    result = call_model_json(prompt, temperature=PRECISE_TEMPERATURE)

    if "error" in result:
        print("  ⚠  Safety Filter: could not parse LLM output — defaulting to safe.")
        return dict(_DEFAULT_RESULT)

    # Normalise the is_safe field (model might return string "true")
    raw_safe = result.get("is_safe", True)
    if isinstance(raw_safe, str):
        result["is_safe"] = raw_safe.lower() in ("true", "yes", "1")

    # Ensure every expected key is present
    for key, default in _DEFAULT_RESULT.items():
        result.setdefault(key, default)

    return result


def is_safe(evaluation: dict) -> bool:
    """Convenience check: does this evaluation represent a safe story?"""
    return bool(evaluation.get("is_safe", False))
