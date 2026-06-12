"""Tests for letz LLM context generator."""

import pytest
from letz.llm_context import generate_llm_context, generate_spellcheck_prompt, generate_normalization_prompt


class TestGenerateLLMContext:
    def test_basic_context(self):
        context = generate_llm_context()
        assert "Luxembourgish" in context
        assert "Lëtzebuergesch" in context
        assert "n-rule" in context.lower() or "n-rule" in context

    def test_context_contains_key_rules(self):
        context = generate_llm_context()
        # Must mention the critical differences from German
        assert "ß" in context
        assert "n" in context  # n-rule
        assert "ë" in context or "trema" in context

    def test_focus_areas(self):
        context = generate_llm_context(focus_areas=["n-rule"])
        assert "n-rule" in context or "n-Reegel" in context or "n drops" in context

    def test_without_examples(self):
        context = generate_llm_context(include_examples=False)
        # Should still have rules but maybe fewer examples
        assert "Luxembourgish" in context

    def test_without_variants(self):
        context = generate_llm_context(include_variants=False)
        assert "Accepted Variants" not in context

    def test_without_errors(self):
        context = generate_llm_context(include_errors=False)
        assert "Common Errors" not in context

    def test_max_rules(self):
        context_full = generate_llm_context()
        context_limited = generate_llm_context(max_rules=5)
        assert len(context_limited) < len(context_full)

    def test_contains_header(self):
        context = generate_llm_context()
        assert "NOT German" in context
        assert "No silent h" in context or "silent h" in context.lower()


class TestSpellcheckPrompt:
    def test_basic_prompt(self):
        prompt = generate_spellcheck_prompt("Ech sinn Lëtzebuerger")
        assert "Ech sinn Lëtzebuerger" in prompt
        assert "Luxembourgish" in prompt
        assert "REVIEW:" in prompt

    def test_prompt_with_focus(self):
        prompt = generate_spellcheck_prompt("E schéint Meedchen", focus_areas=["n-rule"])
        assert "E schéint Meedchen" in prompt


class TestNormalizationPrompt:
    def test_basic_prompt(self):
        prompt = generate_normalization_prompt("Feebruar")
        assert "Feebruar" in prompt
        assert "NORMALIZED" in prompt