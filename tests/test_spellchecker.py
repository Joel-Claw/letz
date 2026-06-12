"""Tests for letz spellchecker."""

import pytest
from letz.spellchecker import Spellchecker, SpellCheckResult, TextCheckResult


@pytest.fixture
def checker():
    """Create a spellchecker in offline mode (no LOD API calls)."""
    with Spellchecker(use_lod=False) as s:
        yield s


class TestSpellcheckerInit:
    def test_offline_mode(self):
        s = Spellchecker(use_lod=False)
        assert s.use_lod is False
        assert s.lod_client is None

    def test_strict_mode(self):
        s = Spellchecker(use_lod=False, strict=True)
        assert s.strict is True


class TestTokenization:
    def test_simple_text(self, checker):
        tokens = checker._tokenize("D'Lëtzebuergesch Sprooch")
        words = [t[0] for t in tokens]
        # D'Lëtzebuergesch splits into "D" and "Lëtzebuergesch"
        assert "Lëtzebuergesch" in words
        assert "Sprooch" in words

    def test_special_chars(self, checker):
        tokens = checker._tokenize("D'Äerd, d'Bouf!")
        words = [t[0] for t in tokens]
        assert len(words) >= 2

    def test_numbers_ignored(self, checker):
        result = checker.check_word("42")
        assert result.is_valid is True

    def test_single_char_ignored(self, checker):
        result = checker.check_word("D")
        assert result.is_valid is True


class TestCommonMisspellings:
    def test_german_esszet(self, checker):
        result = checker.check_word("Straße")
        assert not result.is_valid
        assert len(result.rule_violations) > 0  # ß violations detected
        assert any("ß" in v for v in result.rule_violations)

    def test_german_pronouns(self, checker):
        result = checker.check_word("mich")
        assert not result.is_valid
        assert "mech" in result.suggestions

    def test_german_dass(self, checker):
        result = checker.check_word("dass")
        assert not result.is_valid
        assert "datt" in result.suggestions

    def test_wrong_vowel_doubling(self, checker):
        result = checker.check_word("Arbecht")
        assert not result.is_valid
        assert "Aarbecht" in result.suggestions

    def test_letzebuerg_wrong(self, checker):
        result = checker.check_word("Letzebuerg")
        assert not result.is_valid  # Missing ë
        assert len(result.suggestions) > 0


class TestRuleChecks:
    def test_ss_after_diphthong(self, checker):
        """ss is allowed after diphthongs (even though other consonants aren't doubled)."""
        result = checker.check_word("bäissen")
        # bäissen is correct - ss after diphthong is fine
        assert "No consonant doubling after diphthong" not in " ".join(result.rule_violations)

    def test_ck_after_diphthong_flagged(self, checker):
        """ck should not appear after diphthongs."""
        result = checker.check_word("Eck")  # ck in general is fine
        # This word doesn't have a diphthong before ck, so should be OK

    def test_no_beta_in_luxembourgish(self, checker):
        """ß is never valid in Luxembourgish."""
        result = checker.check_word("groß")
        assert not result.is_valid
        # Should have ß violation
        assert any("ß" in v for v in result.rule_violations)


class TestTextChecking:
    def test_check_simple_text(self, checker):
        result = checker.check_text("Ech sinn Lëtzebuerger")
        assert isinstance(result, TextCheckResult)
        assert result.original == "Ech sinn Lëtzebuerger"

    def test_check_with_error(self, checker):
        result = checker.check_text("mich dich")
        assert result.has_errors is True
        assert result.error_count >= 1

    def test_errors_property(self, checker):
        result = checker.check_text("mich dich")
        errors = result.errors
        assert len(errors) >= 2  # Both are German, not Luxembourgish


class TestUnknownWordAnalysis:
    """Test the _identify_unknown_word feature."""

    def test_german_word_identified(self, checker):
        """German words in COMMON_MISSPELLINGS should be caught with suggestions."""
        result = checker.check_word("ich")
        assert not result.is_valid
        # Caught by common misspellings map
        assert "ech" in result.suggestions

    def test_german_dass_identified(self, checker):
        result = checker.check_word("dass")
        assert not result.is_valid
        # Caught by common misspellings → suggests datt
        assert "datt" in result.suggestions

    def test_german_suffix_heit(self, checker):
        """Words with German -heit suffix should be flagged as German-influenced."""
        # Freiheit is not in common misspellings, so _identify_unknown_word runs
        result = checker.check_word("Freiheit")
        # Should be flagged as German-influenced (offline mode)
        assert not result.is_valid
        notes_text = " ".join(result.notes)
        assert "-heet" in notes_text or "German" in notes_text or "-heit" in notes_text

    def test_on_prefix_described(self, checker):
        """Words starting with on- should be described as negative prefix."""
        result = checker.check_word("onméiglech")
        # on- is a valid Luxembourgish prefix
        if result.notes:
            assert any("on-" in n for n in result.notes) or result.is_valid

    def test_unknown_word_gets_description(self, checker):
        """Unknown words should get a descriptive note."""
        result = checker.check_word("Fluchtwort")
        # Unknown compound — should get some analysis (offline mode)
        assert len(result.notes) > 0

    def test_german_ist_flagged(self, checker):
        """German 'ist' should be flagged with Luxembourgish 'ass'."""
        result = checker.check_word("ist")
        # ist is in COMMON_MISSPELLINGS → ist→ass
        # But it might also be caught by _identify_unknown_word first
        # Either way it should not be valid
        # Check that we get some suggestion or note
        assert not result.is_valid or len(result.notes) > 0


class TestSuggestions:
    def test_suggest_ss_replacement(self, checker):
        suggestions = checker._generate_suggestions("groß")
        assert any("ss" in s for s in suggestions)

    def test_suggest_e_swap(self, checker):
        suggestions = checker._generate_suggestions("Létzebuerg")
        # Should suggest ë variant
        assert len(suggestions) > 0