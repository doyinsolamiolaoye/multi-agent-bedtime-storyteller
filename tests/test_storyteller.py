"""
Tests for storyteller.py

Verifies:
  • generate_story constructs prompt with all arc/category data
  • refine_story includes judge feedback and scores
  • apply_user_feedback includes the user's text
  • fix_safety_issues includes safety flags and changes
  • All functions use creative temperature
"""

import pytest
from unittest.mock import patch, call


with patch("openai.OpenAI"):
    from storyteller import (
        generate_story,
        refine_story,
        apply_user_feedback,
        fix_safety_issues,
    )
    from config import CREATIVE_TEMPERATURE


SAMPLE_CATEGORY = {
    "category": "adventure",
    "themes": ["bravery", "exploration"],
    "tone": "exciting and brave",
}

SAMPLE_ARC = {
    "setup": "A young explorer finds a map.",
    "rising_action": "She follows the map into a forest.",
    "climax": "She discovers a hidden waterfall.",
    "falling_action": "She shares the discovery with her village.",
    "resolution": "Everyone celebrates together.",
    "moral": "Sharing discoveries makes them more special.",
    "character_arc": "She learns that adventures are better shared.",
}


class TestGenerateStory:
    """Tests for generate_story."""

    @patch("storyteller.call_model")
    def test_includes_request_in_prompt(self, mock_call):
        """The user's original request should appear in the prompt."""
        mock_call.return_value = "# The Explorer\n\nOnce upon a time..."

        generate_story("a brave explorer", SAMPLE_CATEGORY, SAMPLE_ARC)
        prompt = mock_call.call_args[0][0]
        assert "a brave explorer" in prompt

    @patch("storyteller.call_model")
    def test_includes_category_in_prompt(self, mock_call):
        """Category metadata should appear in the prompt."""
        mock_call.return_value = "story text"

        generate_story("test", SAMPLE_CATEGORY, SAMPLE_ARC)
        prompt = mock_call.call_args[0][0]
        assert "adventure" in prompt
        assert "bravery" in prompt

    @patch("storyteller.call_model")
    def test_includes_arc_beats_in_prompt(self, mock_call):
        """All 5 arc beats should appear in the prompt."""
        mock_call.return_value = "story text"

        generate_story("test", SAMPLE_CATEGORY, SAMPLE_ARC)
        prompt = mock_call.call_args[0][0]

        for beat in ["setup", "rising_action", "climax", "falling_action", "resolution"]:
            assert SAMPLE_ARC[beat] in prompt

    @patch("storyteller.call_model")
    def test_uses_creative_temperature(self, mock_call):
        """Story generation should use the creative (high) temperature."""
        mock_call.return_value = "story text"

        generate_story("test", SAMPLE_CATEGORY, SAMPLE_ARC)
        _, kwargs = mock_call.call_args
        assert kwargs.get("temperature") == CREATIVE_TEMPERATURE


class TestRefineStory:
    """Tests for refine_story."""

    @patch("storyteller.call_model")
    def test_includes_original_story(self, mock_call):
        """The original story text should appear in the refinement prompt."""
        mock_call.return_value = "refined story"
        feedback = {
            "feedback": "Needs more dialogue.",
            "scores": {"engagement_and_pacing": 5},
            "areas_for_improvement": ["Add character conversations"],
        }

        refine_story("Original story here.", feedback)
        prompt = mock_call.call_args[0][0]
        assert "Original story here." in prompt

    @patch("storyteller.call_model")
    def test_includes_feedback(self, mock_call):
        """Judge feedback text should appear in the refinement prompt."""
        mock_call.return_value = "refined story"
        feedback = {
            "feedback": "The pacing is too fast in the middle section.",
            "scores": {},
            "areas_for_improvement": [],
        }

        refine_story("story", feedback)
        prompt = mock_call.call_args[0][0]
        assert "pacing is too fast" in prompt

    @patch("storyteller.call_model")
    def test_includes_areas_for_improvement(self, mock_call):
        """Specific areas for improvement should be listed in the prompt."""
        mock_call.return_value = "refined story"
        feedback = {
            "feedback": "Some issues.",
            "scores": {},
            "areas_for_improvement": ["More sensory details", "Better ending"],
        }

        refine_story("story", feedback)
        prompt = mock_call.call_args[0][0]
        assert "More sensory details" in prompt
        assert "Better ending" in prompt


class TestApplyUserFeedback:
    """Tests for apply_user_feedback."""

    @patch("storyteller.call_model")
    def test_includes_user_feedback(self, mock_call):
        """The user's feedback text should appear in the prompt."""
        mock_call.return_value = "revised story"

        apply_user_feedback("original story", "Make the dragon friendlier")
        prompt = mock_call.call_args[0][0]
        assert "Make the dragon friendlier" in prompt

    @patch("storyteller.call_model")
    def test_includes_original_story(self, mock_call):
        """The original story should appear in the prompt."""
        mock_call.return_value = "revised story"

        apply_user_feedback("The dragon roared loudly.", "make it gentle")
        prompt = mock_call.call_args[0][0]
        assert "The dragon roared loudly." in prompt


class TestFixSafetyIssues:
    """Tests for fix_safety_issues."""

    @patch("storyteller.call_model")
    def test_includes_safety_flags(self, mock_call):
        """Safety flags should appear in the rewrite prompt."""
        mock_call.return_value = "safe story"
        safety_result = {
            "flags": ["Frightening monster description", "Violence with sword"],
            "suggested_changes": ["Make monster friendly", "Replace fight with puzzle"],
            "severity": "high",
        }

        fix_safety_issues("scary story", safety_result)
        prompt = mock_call.call_args[0][0]
        assert "Frightening monster description" in prompt
        assert "Violence with sword" in prompt

    @patch("storyteller.call_model")
    def test_includes_suggested_changes(self, mock_call):
        """Suggested changes should appear in the rewrite prompt."""
        mock_call.return_value = "safe story"
        safety_result = {
            "flags": ["issue"],
            "suggested_changes": ["Replace darkness with starlight"],
            "severity": "medium",
        }

        fix_safety_issues("story", safety_result)
        prompt = mock_call.call_args[0][0]
        assert "Replace darkness with starlight" in prompt

    @patch("storyteller.call_model")
    def test_includes_severity(self, mock_call):
        """Severity level should appear in the rewrite prompt."""
        mock_call.return_value = "safe story"
        safety_result = {
            "flags": ["concern"],
            "suggested_changes": ["fix it"],
            "severity": "high",
        }

        fix_safety_issues("story", safety_result)
        prompt = mock_call.call_args[0][0]
        assert "high" in prompt

    @patch("storyteller.call_model")
    def test_handles_empty_flags(self, mock_call):
        """Empty flags should use a default fallback message."""
        mock_call.return_value = "safe story"
        safety_result = {"flags": [], "suggested_changes": [], "severity": "low"}

        fix_safety_issues("story", safety_result)
        prompt = mock_call.call_args[0][0]
        assert "General safety concern" in prompt
