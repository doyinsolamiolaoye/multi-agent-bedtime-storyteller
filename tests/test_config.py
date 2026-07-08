"""
Tests for config.py — JSON parsing logic in call_model_json.

These tests verify the JSON extraction and fallback behaviour WITHOUT
making any API calls (we mock call_model).
"""

import json
import pytest
from unittest.mock import patch

# We need to mock the OpenAI client creation that happens at import time
with patch("openai.OpenAI"):
    from config import call_model_json


class TestCallModelJson:
    """Tests for the call_model_json JSON parsing pipeline."""

    @patch("config.call_model")
    def test_parses_clean_json(self, mock_call):
        """Valid JSON string should be parsed directly."""
        expected = {"category": "adventure", "themes": ["bravery"]}
        mock_call.return_value = json.dumps(expected)

        result = call_model_json("test prompt")
        assert result == expected

    @patch("config.call_model")
    def test_extracts_json_from_prose(self, mock_call):
        """JSON wrapped in explanatory prose should still be extracted."""
        expected = {"score": 8, "feedback": "Good story"}
        mock_call.return_value = (
            "Here is the evaluation:\n"
            f"{json.dumps(expected)}\n"
            "Hope this helps!"
        )

        result = call_model_json("test prompt")
        assert result == expected

    @patch("config.call_model")
    def test_extracts_json_with_markdown_fences(self, mock_call):
        """JSON inside ```json code fences should be extracted."""
        expected = {"is_safe": True, "flags": []}
        mock_call.return_value = (
            "```json\n"
            f"{json.dumps(expected)}\n"
            "```"
        )

        result = call_model_json("test prompt")
        assert result == expected

    @patch("config.call_model")
    def test_returns_error_on_total_garbage(self, mock_call):
        """Completely unparseable text should return an error dict."""
        mock_call.return_value = "I cannot provide a JSON response right now."

        result = call_model_json("test prompt")
        assert "error" in result
        assert "raw_response" in result

    @patch("config.call_model")
    def test_returns_error_on_invalid_json_in_braces(self, mock_call):
        """Text with braces but invalid JSON should return an error dict."""
        mock_call.return_value = "The result is {not: valid: json}"

        result = call_model_json("test prompt")
        assert "error" in result

    @patch("config.call_model")
    def test_preserves_nested_json(self, mock_call):
        """Nested JSON structures should be fully preserved."""
        expected = {
            "scores": {
                "age_appropriateness": 9,
                "engagement_and_pacing": 8,
            },
            "overall_score": 8.5,
            "strengths": ["good pacing", "vivid language"],
        }
        mock_call.return_value = json.dumps(expected)

        result = call_model_json("test prompt")
        assert result == expected

    @patch("config.call_model")
    def test_passes_parameters_to_call_model(self, mock_call):
        """Parameters should be forwarded to the underlying call_model."""
        mock_call.return_value = '{"ok": true}'

        call_model_json(
            "test prompt",
            max_tokens=500,
            temperature=0.5,
            system_prompt="Be a test.",
        )

        mock_call.assert_called_once_with(
            "test prompt",
            500,
            0.5,
            "Be a test.",
        )
