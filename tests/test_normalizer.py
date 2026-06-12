"""Tests for letz normalizer."""

import pytest
from letz.normalizer import Normalizer


@pytest.fixture
def norm():
    return Normalizer()


class TestNormalizeWord:
    def test_variant_to_standard(self, norm):
        """Variant spellings should normalize to standard form."""
        result = norm.normalize_word("Feebruar")
        assert result == "Februar"

    def test_variant_case_preserved(self, norm):
        """Capitalization should be preserved."""
        result = norm.normalize_word("Alphabeet")
        assert result == "Alphabet"

    def test_already_standard(self, norm):
        """Words already in standard form should be unchanged."""
        result = norm.normalize_word("Februar")
        assert result == "Februar"

    def test_beta_replacement(self, norm):
        """German ß should be replaced with ss."""
        result = norm.normalize_word("Straße")
        assert "ß" not in result
        assert "ss" in result


class TestNormalizeText:
    def test_full_text(self, norm):
        """Full text normalization."""
        result = norm.normalize_text("Ech sinn zu Lëtzebuerg")
        assert "Lëtzebuerg" in result

    def test_beta_in_text(self, norm):
        """ß should be replaced in full text."""
        result = norm.normalize_text("D'Strooss as groß")
        assert "ß" not in result
        assert "ss" in result


class TestVariantLookup:
    def test_list_variants(self, norm):
        """Should list all variants for a word."""
        variants = norm.list_variants("Februar")
        assert "Februar" in variants
        assert "Feebruar" in variants

    def test_to_standard_form(self, norm):
        """Should return standard form for variant."""
        result = norm.to_standard_form("Feebruar")
        assert result == "Februar"

    def test_to_standard_unknown(self, norm):
        """Should return None for unknown words."""
        result = norm.to_standard_form("xyzabc")
        assert result is None


class TestNRule:
    def test_n_rule_basic(self, norm):
        """n-rule should be context-dependent."""
        # This is mostly a placeholder — full n-rule requires context parsing
        text = "eng schéin Dach"
        result = norm.apply_n_rule(text)
        assert isinstance(result, str)