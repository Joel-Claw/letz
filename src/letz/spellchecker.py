"""Luxembourgish spellchecker using orthography rules and dictionary lookup.

The spellchecker combines rule-based checking (orthography rules from the
official 2024 CPLL/ZLS specification) with dictionary lookup (LOD API)
to detect and suggest corrections for spelling errors.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from letz.rules import (
    COMMON_WORDS,
    COMMON_MISSPELLINGS,
    E_RULES,
    CONSONANT_RULES,
    N_RULE,
    DIPHTHONG_RULES,
    VOWEL_QUANTITY_RULES,
    LONG_VOWEL_RULES,
    SHORT_VOWEL_RULES,
    FOREIGN_WORD_RULES,
    load_common_errors,
    load_spelling_variants,
)
from letz.lod import LODClient


@dataclass
class SpellCheckResult:
    """Result of checking a single word."""
    word: str
    is_valid: bool
    confidence: float = 1.0
    suggestions: list[str] = field(default_factory=list)
    rule_violations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class TextCheckResult:
    """Result of checking a text."""
    original: str
    words: list[SpellCheckResult]
    error_count: int
    warning_count: int
    notes: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0

    @property
    def errors(self) -> list[SpellCheckResult]:
        return [w for w in self.words if not w.is_valid]

    @property
    def warnings(self) -> list[SpellCheckResult]:
        return [w for w in self.words if w.is_valid and w.rule_violations]


class Spellchecker:
    """Luxembourgish spellchecker combining rule-based and dictionary approaches.

    Usage:
        checker = Spellchecker()
        result = checker.check("D'Lëtzebuerger Sprooch ass schéin")
        for error in result.errors:
            print(f"{error.word}: {error.suggestions}")
    """

    def __init__(self, use_lod: bool = True, strict: bool = False):
        """Initialize the spellchecker.

        Args:
            use_lod: Whether to use the LOD API for dictionary lookup.
                     Disable for offline-only mode.
            strict: In strict mode, unknown words are flagged as errors.
                    In lenient mode, unknown words are flagged as warnings.
        """
        self.use_lod = use_lod
        self.strict = strict
        self._lod_client: Optional[LODClient] = None
        self._spelling_variants = load_spelling_variants()
        self._common_errors = load_common_errors()

        # Build reverse variant map: variant → standard
        self._variant_to_standard: dict[str, str] = {}
        for standard, variants in self._spelling_variants.items():
            for variant in variants:
                self._variant_to_standard[variant.lower()] = standard

        # Build case-insensitive misspellings lookup
        self._misspellings_ci: dict[str, str] = {}
        for wrong, correct in COMMON_MISSPELLINGS.items():
            self._misspellings_ci[wrong.lower()] = correct

    @property
    def lod_client(self) -> Optional[LODClient]:
        if self.use_lod and self._lod_client is None:
            self._lod_client = LODClient()
        return self._lod_client

    def _tokenize(self, text: str) -> list[tuple[str, int, int]]:
        """Split text into word tokens with positions.

        Handles Luxembourgish article contractions like D', d', en', etc.
        by treating the apostrophe as a token boundary.

        Returns list of (word, start, end) tuples.
        """
        tokens = []
        # Match Luxembourgish words (including ë, é, ä, ö, ü, etc.)
        # Including apostrophes for article contractions
        pattern = re.compile(r"[a-zA-ZëËéÉäÄöÖüÜàÀâÂêÊîÎôÔûÛçÇßñÑæÆœŒ']+")
        for match in pattern.finditer(text):
            word = match.group()
            # Handle D'/d'/en' article contractions: split the word part
            # e.g., D'Lëtzebuergesch → article "D'" + word "Lëtzebuergesch"
            if "'" in word:
                parts = word.split("'")
                pos = match.start()
                for i, part in enumerate(parts):
                    if part:
                        tokens.append((part, pos, pos + len(part)))
                    pos += len(part) + 1  # +1 for the apostrophe
            else:
                clean = word.strip("-")
                if clean:
                    tokens.append((clean, match.start(), match.end()))
        return tokens

    def _check_vowel_doubling(self, word: str) -> list[str]:
        """Check vowel doubling rules."""
        violations = []
        lower = word.lower()

        # Check for doubled vowels where they shouldn't be
        # (short vowel before consonant cluster — no doubling needed)
        # This is complex, so we check known error patterns

        # Check for ß (not used in Luxembourgish)
        if "ß" in word:
            violations.append("ß is not used in Luxembourgish orthography")

        # Check for German-style vowel+h length marking
        # In Luxembourgish, h is NOT used to mark vowel length
        german_h_patterns = [
            (r"[aou]he[mnst]$", "h not used for vowel length in Luxembourgish"),
        ]
        for pattern, msg in german_h_patterns:
            if re.search(pattern, lower):
                violations.append(msg)

        return violations

    def _check_e_rules(self, word: str) -> list[str]:
        """Check rules for the vowel e."""
        violations = []
        lower = word.lower()

        # é should appear before ch, chs, ck, ng, nk, x
        # If we see é elsewhere in a stressed syllable, it might be wrong
        if "é" in lower:
            # Check if é is before one of the expected consonant clusters
            for i, ch in enumerate(lower):
                if ch == "é" and i + 1 < len(lower):
                    following = lower[i+1:] if i+1 < len(lower) else ""
                    # é before ch, chs, ck, ng, nk, x is correct
                    if not any(following.startswith(p) for p in ["ch", "ck", "ng", "nk", "x"]):
                        # Might still be correct (unstressed, or in specific contexts)
                        pass  # Not a violation per se

        # ë should appear before sch
        if "ë" in lower:
            for i, ch in enumerate(lower):
                if ch == "ë" and i + 1 < len(lower):
                    following = lower[i+1:] if i+1 < len(lower) else ""
                    if following.startswith("sch"):
                        pass  # Correct: ë before sch
                    elif following.startswith(("ch", "ck", "ng", "nk", "x")):
                        violations.append("ë should be é before ch/ck/ng/nk/x (not ë)")

        return violations

    def _check_n_rule(self, word: str) -> list[str]:
        """Check the n-rule for context-dependent issues.

        Note: The n-rule is context-dependent (depends on following word),
        so this only catches word-internal issues.
        """
        violations = []
        # This is mainly a context rule, not a word-internal rule
        # Word-internal n-dropping is handled by the common misspellings map
        return violations

    def _check_consonant_doubling(self, word: str) -> list[str]:
        """Check consonant doubling rules."""
        violations = []
        lower = word.lower()

        # After diphthongs, no consonant doubling (except ss)
        diphthong_patterns = ["au", "ei", "ai", "äi", "éi", "ou", "ie", "ue"]
        for dp in diphthong_patterns:
            if dp in lower:
                # Check for ck or tz after diphthong (shouldn't be there)
                idx = lower.find(dp)
                if idx >= 0 and idx + len(dp) < len(lower):
                    rest = lower[idx + len(dp):]
                    if rest.startswith("ck"):
                        violations.append(f"No ck after diphthong {dp} (use k)")
                    if rest.startswith("tz"):
                        violations.append(f"No tz after diphthong {dp} (use z)")

        return violations

    def _check_foreign_words(self, word: str) -> list[str]:
        """Check foreign word spelling conventions."""
        violations = []
        # ß check is now in _check_common_errors for unified handling
        return violations

    def _check_common_errors(self, word: str) -> Optional[SpellCheckResult]:
        """Check against known common misspellings."""
        lower = word.lower()

        # Always check for ß (not used in Luxembourgish)
        violations = []
        if "ß" in word:
            violations.append("ß is not used in Luxembourgish orthography")

        # Check misspellings map (case-insensitive)
        if lower in self._misspellings_ci:
            correction = self._misspellings_ci[lower]
            if correction.lower() != lower:
                violations.append("Known common misspelling")
                return SpellCheckResult(
                    word=word,
                    is_valid=False,
                    suggestions=[correction],
                    rule_violations=violations,
                )

        # If we have ß violations but it's not in the misspellings map
        if violations:
            suggestions = [word.replace("ß", "ss")] if "ß" in word else []
            return SpellCheckResult(
                word=word,
                is_valid=False,
                suggestions=suggestions,
                rule_violations=violations,
            )

        # Check variant map
        if lower in self._variant_to_standard:
            standard = self._variant_to_standard[lower]
            return SpellCheckResult(
                word=word,
                is_valid=True,
                confidence=0.7,
                suggestions=[standard],
                notes=[f"Variant spelling; standard form is '{standard}'"],
            )

        return None

    def _check_dictionary(self, word: str) -> Optional[bool]:
        """Check a word against the LOD dictionary.

        Returns True if found, False if not found, None if LOD unavailable.
        """
        if not self.lod_client:
            return None

        try:
            result = self.lod_client.check_spelling(word)
            return result.get("found", False)
        except Exception:
            return None

    def check_word(self, word: str) -> SpellCheckResult:
        """Check a single word for spelling errors.

        Args:
            word: The word to check (without surrounding punctuation)

        Returns:
            SpellCheckResult with findings
        """
        # Skip very short words and numbers
        if len(word) <= 1 or word.isnumeric():
            return SpellCheckResult(word=word, is_valid=True)

        # Check common errors first
        common_result = self._check_common_errors(word)
        if common_result is not None:
            return common_result

        violations = []
        suggestions = []
        notes = []

        # Apply rule-based checks
        violations.extend(self._check_vowel_doubling(word))
        violations.extend(self._check_e_rules(word))
        violations.extend(self._check_consonant_doubling(word))
        violations.extend(self._check_foreign_words(word))

        # Check against common words list
        lower = word.lower()
        in_common = lower in COMMON_WORDS or lower in {w.lower() for w in COMMON_WORDS}

        # Check LOD dictionary
        in_dictionary = self._check_dictionary(word)

        # Determine validity
        is_valid = True
        if violations:
            # Rule violations mean the word is likely wrong
            is_valid = False
            if not suggestions:
                suggestions = self._generate_suggestions(word)
        elif in_common:
            is_valid = True
        elif in_dictionary is True:
            is_valid = True
        elif in_dictionary is False:
            if self.strict:
                is_valid = False
                suggestions = self._generate_suggestions(word)
            else:
                # Not in common words or dictionary, but might be valid
                notes.append("Word not found in dictionary")
        # If LOD unavailable and not in common words, give benefit of doubt

        return SpellCheckResult(
            word=word,
            is_valid=is_valid,
            suggestions=suggestions,
            rule_violations=violations,
            notes=notes,
        )

    def check_text(self, text: str) -> TextCheckResult:
        """Check a text for spelling errors.

        Args:
            text: The Luxembourgish text to check

        Returns:
            TextCheckResult with per-word findings
        """
        tokens = self._tokenize(text)
        results = []

        for word, start, end in tokens:
            result = self.check_word(word)
            results.append(result)

        error_count = sum(1 for r in results if not r.is_valid)
        warning_count = sum(1 for r in results if r.is_valid and r.rule_violations)

        return TextCheckResult(
            original=text,
            words=results,
            error_count=error_count,
            warning_count=warning_count,
        )

    # Alias for convenience
    check = check_text

    def _generate_suggestions(self, word: str) -> list[str]:
        """Generate spelling suggestions for a misspelled word."""
        suggestions = []

        # Try common corrections
        lower = word.lower()
        if lower in COMMON_MISSPELLINGS:
            suggestions.append(COMMON_MISSPELLINGS[lower])
            return suggestions

        # Try ß → ss
        if "ß" in word:
            suggestions.append(word.replace("ß", "ss"))

        # Try vowel doubling variations
        for vowel in ["a", "e", "i", "o", "u"]:
            doubled = vowel * 2
            if doubled in word.lower():
                # Try single vowel
                idx = word.lower().find(doubled)
                suggestion = word[:idx] + vowel + word[idx+2:]
                suggestions.append(suggestion)
                break
            elif vowel in word.lower() and doubled not in word.lower():
                # Try doubling a vowel (limited to likely positions)
                pass  # Too many false positives

        # Try n-dropping/keeping variants
        if word.endswith("en"):
            suggestions.append(word[:-2])  # Drop -en (n-rule)
        elif not word.endswith("n") and len(word) > 3:
            suggestions.append(word + "n")  # Add n back

        # Try ë ↔ é swaps
        if "ë" in word:
            suggestions.append(word.replace("ë", "é"))
        if "é" in word:
            suggestions.append(word.replace("é", "ë"))

        # Deduplicate and limit
        seen = {word}
        unique = []
        for s in suggestions:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique.append(s)
        return unique[:5]

    def close(self) -> None:
        """Close the LOD client if open."""
        if self._lod_client:
            self._lod_client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()