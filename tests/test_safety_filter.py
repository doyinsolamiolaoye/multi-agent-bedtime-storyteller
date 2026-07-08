"""
Tests for safety_filter.py

Verifies:
  • Correct parsing of safe / unsafe results
  • Boolean normalisation (string "true" / "false")
  • is_safe convenience function
  • Graceful fallback on parse failure
"""

import pytest
from unittest.mock import patch


with patch("openai.OpenAI"):
    from safety_filter import check_safety, is_safe


SAFE_RESULT = {
    "is_safe": True,
    "flags": [],
    "severity": "none",
    "explanation": "No safety concerns found.",
    "suggested_changes": [],
}

UNSAFE_RESULT = {
    "is_safe": False,
    "flags": [
        "Frightening imagery: the monster is described with sharp teeth and red eyes",
        "Violence: the character fights the beast with a sword",
    ],
    "severity": "high",
    "explanation": "Story contains frightening and violent content inappropriate for ages 5-10.",
    "suggested_changes": [
        "Replace the scary monster with a grumpy but friendly creature",
        "Replace the sword fight with a creative puzzle-solving scene",
    ],
}


class TestCheckSafety:
    """Tests for the check_safety function."""

    @patch("safety_filter.call_model_json")
    def test_safe_story_returns_safe(self, mock_json):
        """A safe evaluation should return is_safe=True."""
        mock_json.return_value = dict(SAFE_RESULT)

        result = check_safety("A gentle story about a bunny.")
        assert result["is_safe"] is True
        assert result["flags"] == []
        assert result["severity"] == "none"

    @patch("safety_filter.call_model_json")
    def test_unsafe_story_returns_flags(self, mock_json):
        """An unsafe evaluation should return is_safe=False with specific flags."""
        mock_json.return_value = dict(UNSAFE_RESULT)

        result = check_safety("A violent dragon story.")
        assert result["is_safe"] is False
        assert len(result["flags"]) == 2
        assert result["severity"] == "high"
        assert len(result["suggested_changes"]) == 2

    @patch("safety_filter.call_model_json")
    def test_normalises_string_true(self, mock_json):
        """String 'true' should be normalised to boolean True."""
        mock_json.return_value = {
            "is_safe": "true",
            "flags": [],
            "severity": "none",
            "explanation": "Safe.",
            "suggested_changes": [],
        }

        result = check_safety("some story")
        assert result["is_safe"] is True

    @patch("safety_filter.call_model_json")
    def test_normalises_string_false(self, mock_json):
        """String 'false' should be normalised to boolean False."""
        mock_json.return_value = {
            "is_safe": "false",
            "flags": ["concern"],
            "severity": "medium",
            "explanation": "Issue found.",
            "suggested_changes": ["fix it"],
        }

        result = check_safety("some story")
        assert result["is_safe"] is False

    @patch("safety_filter.call_model_json")
    def test_normalises_string_yes(self, mock_json):
        """String 'yes' should be normalised to boolean True."""
        mock_json.return_value = {"is_safe": "yes", "flags": []}

        result = check_safety("some story")
        assert result["is_safe"] is True

    @patch("safety_filter.call_model_json")
    def test_falls_back_on_parse_error(self, mock_json):
        """Parse failure should default to safe (with warning printed)."""
        mock_json.return_value = {"error": "Failed", "raw_response": "..."}

        result = check_safety("some story")
        assert result["is_safe"] is True  # default safe
        assert result["severity"] == "none"

    @patch("safety_filter.call_model_json")
    def test_fills_missing_keys(self, mock_json):
        """Partial response should have defaults for missing keys."""
        mock_json.return_value = {"is_safe": False, "severity": "low"}

        result = check_safety("some story")
        assert result["is_safe"] is False
        assert "flags" in result
        assert "explanation" in result
        assert "suggested_changes" in result


class TestIsSafe:
    """Tests for the is_safe convenience function."""

    def test_safe_evaluation(self):
        assert is_safe({"is_safe": True}) is True

    def test_unsafe_evaluation(self):
        assert is_safe({"is_safe": False}) is False

    def test_missing_key_defaults_false(self):
        """Missing is_safe key should be treated as unsafe."""
        assert is_safe({}) is False

    def test_truthy_value(self):
        """Non-boolean truthy values should work."""
        assert is_safe({"is_safe": 1}) is True

    def test_falsy_value(self):
        """Non-boolean falsy values should work."""
        assert is_safe({"is_safe": 0}) is False
