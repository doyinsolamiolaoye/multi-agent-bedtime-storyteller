"""
Storyteller Agent
─────────────────
Generates, refines, and revises bedtime stories for children ages 5-10.

• generate_story      — first draft from request + category + arc
• refine_story        — improve a draft using judge feedback
• apply_user_feedback — revise a story per the listener's wishes
• fix_safety_issues   — rewrite to address safety filter flags
"""

from config import call_model, CREATIVE_TEMPERATURE, DEFAULT_MAX_TOKENS
from prompts import (
    STORYTELLER_PROMPT,
    STORYTELLER_REFINEMENT_PROMPT,
    USER_FEEDBACK_PROMPT,
    SAFETY_REWRITE_PROMPT,
    get_category_guidelines,
)


def generate_story(request: str, category: dict, arc: dict) -> str:
    """Generate the initial story draft from the planned arc."""
    prompt = STORYTELLER_PROMPT.format(
        request=request,
        category=category.get("category", "general"),
        themes=", ".join(category.get("themes", [])),
        tone=category.get("tone", "warm and playful"),
        setup=arc.get("setup", ""),
        rising_action=arc.get("rising_action", ""),
        climax=arc.get("climax", ""),
        falling_action=arc.get("falling_action", ""),
        resolution=arc.get("resolution", ""),
        moral=arc.get("moral", ""),
        character_arc=arc.get("character_arc", ""),
        category_guidelines=get_category_guidelines(
            category.get("category", "general")
        ),
    )
    return call_model(
        prompt,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=CREATIVE_TEMPERATURE,
    )


def refine_story(story: str, feedback: dict) -> str:
    """Improve the story based on structured judge feedback."""
    # Build a human-readable feedback block for the prompt
    feedback_text = feedback.get("feedback", "No specific feedback provided.")
    areas = feedback.get("areas_for_improvement", [])
    if areas:
        feedback_text += "\n\nSpecific areas to improve:\n"
        feedback_text += "\n".join(f"- {a}" for a in areas)

    prompt = STORYTELLER_REFINEMENT_PROMPT.format(
        story=story,
        feedback=feedback_text,
        scores=_format_scores(feedback.get("scores", {})),
    )
    return call_model(
        prompt,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=CREATIVE_TEMPERATURE,
    )


def apply_user_feedback(story: str, user_feedback: str) -> str:
    """Revise the story to incorporate the listener's change requests."""
    prompt = USER_FEEDBACK_PROMPT.format(
        story=story,
        user_feedback=user_feedback,
    )
    return call_model(
        prompt,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=CREATIVE_TEMPERATURE,
    )


def fix_safety_issues(story: str, safety_result: dict) -> str:
    """Rewrite the story to address all flagged safety concerns.

    This is called when the Safety Filter flags content as inappropriate
    for children. Every flagged issue MUST be resolved.
    """
    flags = safety_result.get("flags", [])
    suggested_changes = safety_result.get("suggested_changes", [])
    severity = safety_result.get("severity", "unknown")

    prompt = SAFETY_REWRITE_PROMPT.format(
        story=story,
        flags="\n".join(f"- {f}" for f in flags) if flags else "- General safety concern",
        suggested_changes="\n".join(f"- {c}" for c in suggested_changes) if suggested_changes else "- Make all content gentle and age-appropriate",
        severity=severity,
    )
    return call_model(
        prompt,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=CREATIVE_TEMPERATURE,
    )


# ── helpers ───────────────────────────────────────────────────────────────

def _format_scores(scores: dict) -> str:
    """Pretty-print the judge score dict for inclusion in a prompt."""
    if not scores:
        return "No scores available."
    lines = []
    for key, value in scores.items():
        label = key.replace("_", " ").title()
        lines.append(f"  {label}: {value}/10")
    return "\n".join(lines)

