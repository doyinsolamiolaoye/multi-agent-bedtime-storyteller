"""
Tests for judge.py

Verifies:
  • Correct parsing of evaluation responses
  • Overall score computation when missing
  • Threshold pass/fail logic (the critical average vulnerability)
  • Graceful fallback on parse failure
"""

import pytest
from unittest.mock import patch


with patch("openai.OpenAI"):
    from judge import evaluate_story, passes_threshold


VALID_EVALUATION = {
    "scores": {
        "age_appropriateness": 9,
        "engagement_and_pacing": 8,
        "narrative_structure": 8,
        "language_and_vocabulary": 9,
        "moral_and_lesson": 8,
    },
    "overall_score": 8.4,
    "feedback": "Well-structured story with vivid language.",
    "strengths": ["good pacing", "age-appropriate vocabulary"],
    "areas_for_improvement": ["could use more dialogue"],
}


class TestEvaluateStory:
    """Tests for the evaluate_story function."""

    @patch("judge.call_model_json")
    def test_returns_parsed_evaluation(self, mock_json):
        """Valid evaluation response should be returned as-is."""
        mock_json.return_value = dict(VALID_EVALUATION)

        result = evaluate_story("Once upon a time...", "a fairy tale")
        assert result["overall_score"] == 8.4
        assert result["scores"]["age_appropriateness"] == 9
        assert len(result["strengths"]) == 2

    @patch("judge.call_model_json")
    def test_computes_overall_when_missing(self, mock_json):
        """If the model omits overall_score, it should be computed from scores."""
        response = {
            "scores": {
                "age_appropriateness": 10,
                "engagement_and_pacing": 8,
                "narrative_structure": 6,
                "language_and_vocabulary": 10,
                "moral_and_lesson": 6,
            },
            "feedback": "Mixed results.",
            "strengths": [],
            "areas_for_improvement": [],
        }
        mock_json.return_value = response

        result = evaluate_story("story text", "request text")
        assert result["overall_score"] == 8.0  # (10+8+6+10+6)/5

    @patch("judge.call_model_json")
    def test_falls_back_on_parse_error(self, mock_json):
        """Parse failure should return default scores."""
        mock_json.return_value = {"error": "Failed", "raw_response": "..."}

        result = evaluate_story("story", "request")
        assert result["overall_score"] == 5.0
        assert "scores" in result
        assert isinstance(result["feedback"], str)

    @patch("judge.call_model_json")
    def test_fills_missing_keys(self, mock_json):
        """Partial response should have defaults for missing keys."""
        mock_json.return_value = {
            "scores": {"age_appropriateness": 7},
            "overall_score": 7.0,
        }

        result = evaluate_story("story", "request")
        assert "feedback" in result
        assert "strengths" in result
        assert "areas_for_improvement" in result


class TestPassesThreshold:
    """Tests for the passes_threshold function — the quality gate."""

    def test_passes_above_threshold(self):
        assert passes_threshold({"overall_score": 8.0}) is True

    def test_passes_at_threshold(self):
        assert passes_threshold({"overall_score": 7.0}) is True

    def test_fails_below_threshold(self):
        assert passes_threshold({"overall_score": 6.9}) is False

    def test_fails_on_missing_score(self):
        """Missing overall_score should default to 0 → fail."""
        assert passes_threshold({}) is False

    def test_average_vulnerability_example(self):
        """Demonstrates the average-score vulnerability.

        A story with 0 on age_appropriateness but 10 on everything else
        has an average of 8.0 — which PASSES the judge threshold (7).
        This is why we need the Safety Filter as a separate gate.
        """
        dangerous_scores = {
            "age_appropriateness": 0,
            "engagement_and_pacing": 10,
            "narrative_structure": 10,
            "language_and_vocabulary": 10,
            "moral_and_lesson": 10,
        }
        average = sum(dangerous_scores.values()) / len(dangerous_scores)
        assert average == 8.0
        assert passes_threshold({"overall_score": average}) is True  # ← This passes!
        # This is exactly why the Safety Filter exists as an independent gate.
