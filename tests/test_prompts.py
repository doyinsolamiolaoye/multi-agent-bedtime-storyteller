"""
Tests for prompts.py

Verifies:
  • All prompt templates format without KeyError (no missing placeholders)
  • get_category_guidelines returns content for every supported category
  • get_category_guidelines falls back to "general" for unknown categories
  • Prompts contain key instructional elements
"""

import pytest
from unittest.mock import patch


with patch("openai.OpenAI"):
    from prompts import (
        CATEGORIZER_PROMPT,
        STORY_ARC_PROMPT,
        STORYTELLER_PROMPT,
        STORYTELLER_REFINEMENT_PROMPT,
        USER_FEEDBACK_PROMPT,
        SAFETY_FILTER_PROMPT,
        SAFETY_REWRITE_PROMPT,
        JUDGE_PROMPT,
        CATEGORY_GUIDELINES,
        get_category_guidelines,
    )


class TestPromptFormatting:
    """Ensure all prompts can be formatted without errors."""

    def test_categorizer_prompt_formats(self):
        result = CATEGORIZER_PROMPT.format(request="a story about a cat")
        assert "a story about a cat" in result
        assert "JSON" in result

    def test_story_arc_prompt_formats(self):
        result = STORY_ARC_PROMPT.format(
            request="a brave knight",
            category="adventure",
            themes="bravery, honor",
            characters="Sir Lancelot",
            tone="exciting",
        )
        assert "a brave knight" in result
        assert "adventure" in result

    def test_storyteller_prompt_formats(self):
        result = STORYTELLER_PROMPT.format(
            request="a fairy tale",
            category="fairy-tale",
            themes="magic, transformation",
            tone="classic and warm",
            setup="Once upon a time",
            rising_action="A quest begins",
            climax="The big moment",
            falling_action="Resolution starts",
            resolution="Happy ending",
            moral="Be kind",
            character_arc="Growth through kindness",
            category_guidelines="Use classic language",
        )
        assert "a fairy tale" in result
        assert "Once upon a time" in result
        assert "400-600 words" in result

    def test_refinement_prompt_formats(self):
        result = STORYTELLER_REFINEMENT_PROMPT.format(
            story="The quick fox...",
            feedback="Needs more detail.",
            scores="Engagement: 6/10",
        )
        assert "The quick fox..." in result
        assert "Needs more detail." in result

    def test_user_feedback_prompt_formats(self):
        result = USER_FEEDBACK_PROMPT.format(
            story="Original story text",
            user_feedback="Add a dragon please",
        )
        assert "Original story text" in result
        assert "Add a dragon please" in result

    def test_judge_prompt_formats(self):
        result = JUDGE_PROMPT.format(
            story="Story to judge",
            request="original request",
        )
        assert "Story to judge" in result
        assert "original request" in result
        assert "JSON" in result

    def test_safety_filter_prompt_formats(self):
        result = SAFETY_FILTER_PROMPT.format(story="Story to check")
        assert "Story to check" in result
        assert "HARD SAFETY GATE" in result

    def test_safety_rewrite_prompt_formats(self):
        result = SAFETY_REWRITE_PROMPT.format(
            story="Scary story",
            flags="- Frightening imagery",
            suggested_changes="- Make it gentle",
            severity="high",
        )
        assert "Scary story" in result
        assert "Frightening imagery" in result
        assert "high" in result


class TestCategoryGuidelines:
    """Tests for get_category_guidelines and CATEGORY_GUIDELINES."""

    EXPECTED_CATEGORIES = [
        "adventure", "fantasy", "animal", "friendship",
        "mystery", "educational", "fairy-tale", "general",
    ]

    def test_all_categories_have_guidelines(self):
        """Every expected category should have a non-empty guidelines string."""
        for cat in self.EXPECTED_CATEGORIES:
            guidelines = get_category_guidelines(cat)
            assert isinstance(guidelines, str)
            assert len(guidelines) > 20, f"Guidelines for '{cat}' are too short"

    def test_unknown_category_falls_back_to_general(self):
        """An unrecognised category should return the 'general' guidelines."""
        result = get_category_guidelines("sci-fi")
        expected = get_category_guidelines("general")
        assert result == expected

    def test_adventure_has_action_language(self):
        guidelines = get_category_guidelines("adventure")
        assert "action" in guidelines.lower()

    def test_fantasy_has_sparkle_words(self):
        guidelines = get_category_guidelines("fantasy")
        assert "sparkle" in guidelines.lower() or "shimmer" in guidelines.lower()

    def test_animal_has_anthropomorphism(self):
        guidelines = get_category_guidelines("animal")
        assert "anthropomorphism" in guidelines.lower()

    def test_mystery_has_clues(self):
        guidelines = get_category_guidelines("mystery")
        assert "clue" in guidelines.lower()

    def test_fairy_tale_has_classic_language(self):
        guidelines = get_category_guidelines("fairy-tale")
        assert "once upon a time" in guidelines.lower()


class TestPromptContent:
    """Verify that prompts contain critical instructional elements."""

    def test_storyteller_age_range(self):
        """Storyteller prompt should mention the 5-10 age range."""
        prompt = STORYTELLER_PROMPT
        assert "5" in prompt and "10" in prompt

    def test_judge_has_five_criteria(self):
        """Judge prompt should mention all 5 evaluation criteria."""
        prompt = JUDGE_PROMPT
        assert "Age Appropriateness" in prompt
        assert "Engagement" in prompt
        assert "Narrative Structure" in prompt
        assert "Language" in prompt
        assert "Moral" in prompt

    def test_safety_filter_has_six_checks(self):
        """Safety filter prompt should cover all 6 safety categories."""
        prompt = SAFETY_FILTER_PROMPT
        checks = [
            "Frightening",
            "Violence",
            "Inappropriate Themes",
            "Scary Scenarios",
            "Negative Emotional",
            "Inappropriate Language",
        ]
        for check in checks:
            assert check in prompt, f"Safety filter missing check: {check}"

    def test_categorizer_requests_json(self):
        """Categorizer prompt should request JSON output."""
        assert "JSON" in CATEGORIZER_PROMPT

    def test_safety_filter_instructs_strictness(self):
        """Safety filter should instruct the model to be strict."""
        assert "STRICT" in SAFETY_FILTER_PROMPT
