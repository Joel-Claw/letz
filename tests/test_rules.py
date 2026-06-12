"""Tests for letz orthography rules."""

import pytest
from letz.rules import (
    load_orthography_rules,
    load_common_errors,
    load_spelling_variants,
    load_n_rule_exceptions,
    COMMON_WORDS,
    COMMON_MISSPELLINGS,
    E_RULES,
    CONSONANT_RULES,
    N_RULE,
    DIPHTHONG_RULES,
)


class TestOrthographyRules:
    def test_load_rules(self):
        rules = load_orthography_rules()
        assert rules["title"] == "D'Lëtzebuerger Orthografie"
        assert rules["edition"] == "6th edition, 2024"
        assert len(rules["chapters"]) == 10

    def test_chapter_titles(self):
        rules = load_orthography_rules()
        # Check all chapters have titles
        for ch_num, ch_data in rules["chapters"].items():
            assert "title_lb" in ch_data
            assert "title_en" in ch_data
            assert "rules" in ch_data

    def test_vowel_rules(self):
        rules = load_orthography_rules()
        ch1 = rules["chapters"][1]
        # Chapter 1 should have vowel quantity rules
        assert "rules" in ch1
        assert len(ch1["rules"]) > 0

    def test_n_rule(self):
        rules = load_orthography_rules()
        ch6 = rules["chapters"][6]
        assert "n_rule" in str(ch6).lower() or "n-Reegel" in str(ch6)


class TestCommonErrors:
    def test_load_errors(self):
        errors = load_common_errors()
        assert len(errors) > 0
        assert all("error" in e and "correct" in e for e in errors)

    def test_letzebuerg_error(self):
        errors = load_common_errors()
        letzebuerg_errors = [e for e in errors if "Letzebuerg" in e["error"] or "Létzebuerg" in e["error"]]
        assert len(letzebuerg_errors) > 0


class TestSpellingVariants:
    def test_load_variants(self):
        variants = load_spelling_variants()
        assert len(variants) > 0

    def test_februar_variant(self):
        variants = load_spelling_variants()
        assert "Februar" in variants
        assert "Feebruar" in variants["Februar"]

    def test_flughafen_variant(self):
        variants = load_spelling_variants()
        assert "Flughafen" in variants
        assert "Fluchhafen" in variants["Flughafen"]


class TestCommonWords:
    def test_basic_words(self):
        assert "Lëtzebuerg" in COMMON_WORDS
        assert "Lëtzebuergesch" in COMMON_WORDS
        assert "ech" in COMMON_WORDS

    def test_articles(self):
        assert "de" in COMMON_WORDS
        assert "den" in COMMON_WORDS
        assert "eng" in COMMON_WORDS

    def test_days(self):
        assert "Méindeg" in COMMON_WORDS
        assert "Sonndeg" in COMMON_WORDS


class TestCommonMisspellings:
    def test_german_influence(self):
        assert "mich" in COMMON_MISSPELLINGS
        assert COMMON_MISSPELLINGS["mich"] == "mech"

    def test_esszet(self):
        assert "Straße" in COMMON_MISSPELLINGS
        assert COMMON_MISSPELLINGS["Straße"] == "Strooss"

    def test_letzebuerg_variants(self):
        assert "Letzebuerg" in COMMON_MISSPELLINGS
        assert "Létzebuerg" in COMMON_MISSPELLINGS


class TestERules:
    def test_long_ee(self):
        assert "long_ee" in E_RULES
        assert "rule" in E_RULES["long_ee"]

    def test_trema(self):
        assert "short_e_trema" in E_RULES
        assert "examples" in E_RULES["short_e_trema"]


class TestConsonantRules:
    def test_doubling(self):
        assert "doubling" in CONSONANT_RULES
        assert "rule" in CONSONANT_RULES["doubling"]

    def test_no_beta(self):
        """ß should be mentioned in the consonant rules."""
        all_text = str(CONSONANT_RULES)
        assert "ß" in all_text or "ss" in all_text


class TestNRule:
    def test_general_rule(self):
        assert "general" in N_RULE
        assert "rule" in N_RULE["general"]

    def test_n_kept(self):
        assert "n_kept" in N_RULE
        assert "before_vowels" in N_RULE["n_kept"]

    def test_n_dropped(self):
        assert "n_dropped" in N_RULE


class TestDiphthongRules:
    def test_all_diphthongs(self):
        for dp in ["au", "ei", "ai", "äi", "éi", "ou", "ie", "ue"]:
            assert dp in DIPHTHONG_RULES, f"Missing diphthong: {dp}"

    def test_ie_note(self):
        assert "ie" in DIPHTHONG_RULES
        assert "diphthong" in DIPHTHONG_RULES["ie"]["note"].lower()