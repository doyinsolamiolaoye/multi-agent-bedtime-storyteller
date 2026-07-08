"""
Tests for story_arc.py

Verifies:
  • Correct parsing of well-formed LLM responses
  • Graceful fallback to defaults on parse failure
  • All 7 expected arc keys present in output
  • Category metadata is included in the prompt
"""

import pytest
from unittest.mock import patch


with patch("openai.OpenAI"):
    from story_arc import plan_arc


VALID_ARC = {
    "setup": "Luna discovers a hidden garden behind her grandmother's house.",
    "rising_action": "The garden's flowers begin to wilt because of a missing magical stone.",
    "climax": "Luna bravely enters the enchanted cave to find the stone.",
    "falling_action": "Luna returns the stone and the garden begins to bloom again.",
    "resolution": "Luna falls asleep in the garden, surrounded by glowing flowers.",
    "moral": "Bravery and kindness can restore beauty to the world.",
    "character_arc": "Luna goes from being shy to discovering her inner courage.",
}

SAMPLE_CATEGORY = {
    "category": "fantasy",
    "themes": ["bravery", "nature"],
    "characters": ["Luna"],
    "tone": "gentle and magical",
}


class TestPlanArc:
    """Tests for the plan_arc function."""

    @patch("story_arc.call_model_json")
    def test_returns_parsed_arc(self, mock_json):
        """Valid LLM response should be returned with all 7 keys."""
        mock_json.return_value = dict(VALID_ARC)

        result = plan_arc("A story about a magical garden", SAMPLE_CATEGORY)

        for key in VALID_ARC:
            assert key in result
            assert result[key] == VALID_ARC[key]

    @patch("story_arc.call_model_json")
    def test_falls_back_on_parse_error(self, mock_json):
        """Parse failure should return a complete default arc."""
        mock_json.return_value = {"error": "Failed", "raw_response": "..."}

        result = plan_arc("something", SAMPLE_CATEGORY)

        expected_keys = {"setup", "rising_action", "climax", "falling_action",
                         "resolution", "moral", "character_arc"}
        assert set(result.keys()) >= expected_keys

    @patch("story_arc.call_model_json")
    def test_fills_missing_keys(self, mock_json):
        """Partial response should have missing keys filled with defaults."""
        mock_json.return_value = {"setup": "Custom setup", "climax": "Custom climax"}

        result = plan_arc("test", SAMPLE_CATEGORY)
        assert result["setup"] == "Custom setup"
        assert result["climax"] == "Custom climax"
        # Defaults fill the rest
        assert "rising_action" in result
        assert "resolution" in result
        assert "moral" in result

    @patch("story_arc.call_model_json")
    def test_prompt_includes_category_info(self, mock_json):
        """The category, themes, and characters should appear in the prompt."""
        mock_json.return_value = dict(VALID_ARC)

        plan_arc("A magical garden story", SAMPLE_CATEGORY)
        prompt = mock_json.call_args[0][0]

        assert "fantasy" in prompt
        assert "bravery" in prompt
        assert "Luna" in prompt
