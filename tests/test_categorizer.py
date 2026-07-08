"""
Tests for categorizer.py

Verifies:
  • Correct parsing of well-formed LLM responses
  • Graceful fallback to defaults on parse failure
  • All expected keys present in output
"""

import json
import pytest
from unittest.mock import patch


# Mock OpenAI client before importing modules that use it
with patch("openai.OpenAI"):
    from categorizer import categorize


VALID_RESPONSE = {
    "category": "fantasy",
    "themes": ["magic", "courage"],
    "characters": ["a young wizard", "a talking owl"],
    "tone": "gentle and magical",
    "setting_suggestions": ["an enchanted forest", "a crystal cave"],
}


class TestCategorize:
    """Tests for the categorize function."""

    @patch("categorizer.call_model_json")
    def test_returns_parsed_category(self, mock_json):
        """Valid LLM response should be returned as-is."""
        mock_json.return_value = dict(VALID_RESPONSE)

        result = categorize("A story about a wizard and his owl")
        assert result["category"] == "fantasy"
        assert "magic" in result["themes"]
        assert len(result["characters"]) == 2

    @patch("categorizer.call_model_json")
    def test_falls_back_on_parse_error(self, mock_json):
        """Parse failure should return sensible defaults."""
        mock_json.return_value = {"error": "Failed to parse", "raw_response": "..."}

        result = categorize("something weird")
        assert result["category"] == "general"
        assert isinstance(result["themes"], list)
        assert isinstance(result["characters"], list)
        assert "tone" in result

    @patch("categorizer.call_model_json")
    def test_fills_missing_keys(self, mock_json):
        """Partial LLM response should have missing keys filled with defaults."""
        mock_json.return_value = {"category": "mystery"}

        result = categorize("A detective story")
        assert result["category"] == "mystery"
        # Defaults should fill in the rest
        assert "themes" in result
        assert "characters" in result
        assert "tone" in result
        assert "setting_suggestions" in result

    @patch("categorizer.call_model_json")
    def test_prompt_includes_user_request(self, mock_json):
        """The user's request text should appear in the prompt sent to the model."""
        mock_json.return_value = dict(VALID_RESPONSE)

        categorize("a dragon and a princess")
        call_args = mock_json.call_args
        prompt = call_args[0][0]  # first positional arg
        assert "a dragon and a princess" in prompt
