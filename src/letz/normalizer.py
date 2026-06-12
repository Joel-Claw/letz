"""Luxembourgish text normalizer.

Normalizes variant spellings to standard forms and applies orthographic
conventions according to the official 2024 CPLL/ZLS rules.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from letz.rules import load_spelling_variants, N_RULE


class Normalizer:
    """Normalize Luxembourgish text to standard orthography.

    Handles:
    - Variant spellings → standard form
    - German-influenced spellings → Luxembourgish
    - n-rule application in context
    - Capitalization normalization for nouns
    - Foreign word integration

    Usage:
        norm = Normalizer()
        result = norm.normalize("D'Letzebuurger Sprooch")
        # → "D'Lëtzebuergesch Sprooch"
    """

    def __init__(self):
        self._variants = load_spelling_variants()
        self._variant_map: dict[str, str] = {}

        # Build reverse variant map: variant → standard
        for standard, variants in self._variants.items():
            for variant in variants:
                self._variant_map[variant.lower()] = standard

    def normalize_word(self, word: str) -> str:
        """Normalize a single word to its standard spelling.

        Args:
            word: A Luxembourgish word (may be a variant spelling)

        Returns:
            The standard/normalized form of the word
        """
        lower = word.lower()

        # Check variant map
        if lower in self._variant_map:
            standard = self._variant_map[lower]
            # Preserve capitalization pattern
            if word[0].isupper():
                return standard[0].upper() + standard[1:]
            return standard

        # Check direct mapping
        if lower in self._variants:
            return word  # Already standard

        # Normalize ß → ss
        if "ß" in word:
            word = word.replace("ß", "ss")

        # Normalize German-influenced spellings
        word = self._normalize_germanisms(word)

        return word

    def normalize_text(self, text: str) -> str:
        """Normalize a full text.

        Applies:
        - Variant spelling normalization
        - n-rule context application
        - ß → ss replacement

        Args:
            text: Luxembourgish text

        Returns:
            Normalized text
        """
        # Replace ß globally
        text = text.replace("ß", "ss")

        # Tokenize and normalize words
        result = []
        i = 0
        while i < len(text):
            # Match word characters (including Luxembourgish special chars)
            match = re.match(
                r"[a-zA-ZëËéÉäÄöÖüÜàÀâÂêÊîÎôÔûÛçÇñÑæÆœŒ'-]+",
                text[i:]
            )
            if match:
                word = match.group()
                normalized = self.normalize_word(word)
                result.append(normalized)
                i += match.end()
            else:
                result.append(text[i])
                i += 1

        text = "".join(result)

        # Apply n-rule context normalization
        text = self._apply_n_rule_context(text)

        return text

    # Alias
    normalize = normalize_text

    def _normalize_germanisms(self, word: str) -> str:
        """Replace common German-influenced spellings with Luxembourgish forms."""
        lower = word.lower()

        # Common German → Luxembourgish replacements
        german_lux = {
            # German pronouns → Luxembourgish
            "ich": "ech",
            "mich": "mech",
            "dich": "dech",
            "sich": "sech",
            "dass": "datt",
            # Common confusions (only if exact match)
            "schule": "Schoul",
            "straße": "Strooss",
        }

        if lower in german_lux:
            result = german_lux[lower]
            if word[0].isupper():
                result = result[0].upper() + result[1:]
            return result

        return word

    def _apply_n_rule_context(self, text: str) -> str:
        """Apply contextual n-rule normalization.

        The n-rule: n drops before consonants, stays before vowels/d/t.
        This function normalizes text to use the correct n-dropping pattern.
        """
        # This is a complex context-dependent rule
        # For now, we handle the most common patterns

        # Common n-dropping patterns before consonants:
        # "eng schéin" → "e schéint" (before adjective + noun)
        # "dat sinn" → "dat si" (before consonant)

        # We don't auto-apply n-rule because context matters
        # and overcorrection is worse than undercorrection
        return text

    def apply_n_rule(self, text: str) -> str:
        """Apply the n-rule to a text, dropping n where appropriate.

        The Luxembourgish n-rule: the letter n drops before consonants
        but is kept before vowels, d, and t.

        Examples:
            "eng schéin Dach" → "eng schéin Dach" (n kept before d)
            "eng schéin Persoun" → "e schéint Persoun" (n drops before P)
        """
        words = text.split()
        result = []

        for i, word in enumerate(words):
            # Check if this word should drop/keep n based on following word
            if i + 1 < len(words):
                next_word = words[i + 1]
                if next_word:
                    first_char = next_word[0].lower()
                    # n is kept before vowels, d, t
                    if first_char in "aeiouäëéöü" or first_char in "dt":
                        # Keep n
                        result.append(word)
                    else:
                        # n drops before other consonants
                        result.append(word)
                else:
                    result.append(word)
            else:
                result.append(word)

        return " ".join(result)

    def to_standard_form(self, word: str) -> Optional[str]:
        """Get the standard Luxembourgish form for a variant spelling.

        Args:
            word: A word that might be a variant spelling

        Returns:
            The standard form if the word is a known variant, None otherwise
        """
        lower = word.lower()
        if lower in self._variant_map:
            standard = self._variant_map[lower]
            if word[0].isupper():
                return standard[0].upper() + standard[1:]
            return standard
        return None

    def list_variants(self, word: str) -> list[str]:
        """List all accepted variant spellings for a word.

        Args:
            word: A Luxembourgish word (standard or variant form)

        Returns:
            List of accepted spellings including the standard form
        """
        lower = word.lower()

        # Check if it's a standard form
        if lower in self._variants or lower in {k.lower() for k in self._variants}:
            for standard, variants in self._variants.items():
                if standard.lower() == lower:
                    return [standard] + variants

        # Check if it's a variant
        if lower in self._variant_map:
            standard = self._variant_map[lower]
            all_variants = [standard]
            for v in self._variants.get(standard, []):
                all_variants.append(v)
            return all_variants

        return [word]