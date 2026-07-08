"""
LLM Judge Agent
───────────────
Evaluates a generated story on five quality criteria and returns
structured scores plus actionable feedback.

Criteria (each 1-10):
  1. Age Appropriateness
  2. Engagement & Pacing
  3. Narrative Structure
  4. Language & Vocabulary
  5. Moral & Lesson
"""

from config import call_model_json, PRECISE_TEMPERATURE, JUDGE_PASS_THRESHOLD
from prompts import JUDGE_PROMPT

# Fallback evaluation when the LLM response can't be parsed
_DEFAULT_EVAL = {
    "scores": {
        "age_appropriateness": 5,
        "engagement_and_pacing": 5,
        "narrative_structure": 5,
        "language_and_vocabulary": 5,
        "moral_and_lesson": 5,
    },
    "overall_score": 5.0,
    "feedback": "Unable to evaluate properly. Consider refining the story.",
    "strengths": [],
    "areas_for_improvement": [],
}


def evaluate_story(story: str, request: str) -> dict:
    """Return an evaluation dict with scores, feedback, strengths, and areas to improve."""
    prompt = JUDGE_PROMPT.format(story=story, request=request)
    result = call_model_json(prompt, temperature=PRECISE_TEMPERATURE)

    if "error" in result:
        print("  ⚠  Judge: could not parse LLM output — using default scores.")
        return dict(_DEFAULT_EVAL)

    # Compute overall_score if the model didn't return one
    if "overall_score" not in result and "scores" in result:
        scores = result["scores"]
        if isinstance(scores, dict) and scores:
            result["overall_score"] = round(
                sum(scores.values()) / len(scores), 1
            )

    # Ensure every expected key is present
    for key, default in _DEFAULT_EVAL.items():
        result.setdefault(key, default)

    return result


def passes_threshold(evaluation: dict) -> bool:
    """Check whether the story's overall score meets the quality bar."""
    return evaluation.get("overall_score", 0) >= JUDGE_PASS_THRESHOLD
