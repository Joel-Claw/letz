"""LLM context generator for Luxembourgish spellchecking.

Generates structured prompts that inject orthography rules and dictionary
context so LLMs can spellcheck Luxembourgish — even models with zero
Luxembourgish training data.
"""

from __future__ import annotations

from typing import Optional

from letz.rules import load_orthography_rules, load_common_errors, load_spelling_variants, E_RULES
from letz.lod import LODClient


def generate_llm_context(
    focus_areas: Optional[list[str]] = None,
    include_examples: bool = True,
    include_variants: bool = True,
    include_errors: bool = True,
    max_rules: Optional[int] = None,
) -> str:
    """Generate a structured prompt context for LLM spellchecking of Luxembourgish.

    This is the core innovation of letz: instead of hoping LLMs learned
    Luxembourgish from training data, we inject the orthography rules at
    inference time so any LLM can follow them.

    Args:
        focus_areas: Specific rule areas to focus on (e.g., ["n-rule", "vowels"]).
                     If None, includes all areas.
        include_examples: Whether to include example words in the context.
        include_variants: Whether to include known spelling variants.
        include_errors: Whether to include common error → correction pairs.
        max_rules: Maximum number of rules to include (for token budget).

    Returns:
        A string containing structured orthography rules suitable for LLM prompts.
    """
    rules = load_orthography_rules()
    sections = []

    sections.append(HEADER.strip())

    # Core rules by chapter
    chapters = rules["chapters"]
    focus_set = set(focus_areas) if focus_areas else None

    for ch_num, ch_data in chapters.items():
        ch_title = f"Chapter {ch_num}: {ch_data['title_lb']} ({ch_data['title_en']})"
        ch_rules = ch_data.get("rules", {})

        # Check if this chapter should be included
        if focus_set and not _chapter_matches(ch_num, ch_data, focus_set):
            continue

        section = f"\n## {ch_title}\n"
        section += _format_rules(ch_rules, include_examples, max_rules)
        sections.append(section)

    # Common errors section
    if include_errors:
        errors = load_common_errors()
        error_section = "\n## Common Errors\n"
        error_section += _format_errors(errors[:30])  # Limit for token budget
        sections.append(error_section)

    # Spelling variants section
    if include_variants:
        variants = load_spelling_variants()
        variant_section = "\n## Accepted Variants\n"
        variant_section += _format_variants(variants)
        sections.append(variant_section)

    context = "\n".join(sections)

    if max_rules:
        # Truncate if needed for token budget
        context = _truncate_context(context, max_rules)

    return context


def generate_spellcheck_prompt(
    text: str,
    focus_areas: Optional[list[str]] = None,
    detailed: bool = True,
) -> str:
    """Generate a complete prompt for LLM spellchecking of Luxembourgish text.

    Args:
        text: The Luxembourgish text to spellcheck.
        focus_areas: Specific orthography areas to focus on.
        detailed: If True, includes full rule explanations; if False, just key rules.

    Returns:
        A complete prompt ready to send to an LLM.
    """
    context = generate_llm_context(
        focus_areas=focus_areas,
        include_examples=detailed,
        include_variants=True,
        include_errors=True,
    )

    prompt = f"""{context}

---

Now check the following Luxembourgish text for spelling errors. For each error:
1. Quote the exact misspelled word
2. Provide the correct spelling
3. Cite the specific orthography rule that applies
4. If it's an accepted variant, note that

If the text is correct, say so. Do not "correct" valid Luxembourgish spellings.

TEXT TO CHECK:
\"\"\"
{text}
\"\"\"

REVIEW:"""

    return prompt


def generate_normalization_prompt(
    text: str,
) -> str:
    """Generate a prompt for normalizing Luxembourgish text to standard spelling.

    Args:
        text: The text to normalize.

    Returns:
        A complete prompt for an LLM to normalize the text.
    """
    context = generate_llm_context(
        focus_areas=["vowels", "n-rule", "foreign-words", "consonants"],
        include_examples=True,
        include_variants=True,
        include_errors=False,
    )

    prompt = f"""{context}

---

Normalize the following Luxembourgish text to standard orthography. Apply these rules:
- Replace German ß with ss
- Use the standard form of variant spellings (but accept both if both are valid)
- Apply the n-rule where appropriate
- Use ë before sch, é before ch/ck/ng/nk/x
- Use doubled vowels before multiple consonants in stressed syllables
- Do NOT use silent h to mark vowel length

TEXT TO NORMALIZE:
\"\"\"
{text}
\"\"\"

NORMALIZED TEXT:"""

    return prompt


def _chapter_matches(ch_num: int, ch_data: dict, focus_set: set) -> bool:
    """Check if a chapter matches the focus areas."""
    focus_map = {
        1: {"vowels", "vowel", "vowel-quantity"},
        2: {"e", "vowel-e", "e-rule"},
        3: {"diphthong", "diphthongs", "r-rule"},
        4: {"consonant", "consonants"},
        5: {"verb", "verbs"},
        6: {"n-rule", "n-rule"},
        7: {"foreign", "foreign-words"},
        8: {"capitalization", "capital"},
        9: {"compound", "compounds", "hyphenation"},
        10: {"punctuation"},
    }
    matches = focus_map.get(ch_num, set())
    return bool(matches & focus_set)


def _format_rules(rules: dict, include_examples: bool = True, max_rules: Optional[int] = None) -> str:
    """Format rules dictionary into readable text."""
    lines = []
    count = 0

    for key, value in rules.items():
        if max_rules and count >= max_rules:
            lines.append("... (truncated)")
            break

        if isinstance(value, str):
            lines.append(f"- **{key}**: {value}")
            count += 1
        elif isinstance(value, dict):
            lines.append(f"\n### {key}")
            for sub_key, sub_value in value.items():
                if max_rules and count >= max_rules:
                    break
                if isinstance(sub_value, str):
                    lines.append(f"- **{sub_key}**: {sub_value}")
                    count += 1
                elif isinstance(sub_value, dict):
                    sub_lines = _format_rules({sub_key: sub_value}, include_examples, max_rules)
                    lines.append(sub_lines)
                    count += 1
                elif isinstance(sub_value, list):
                    if include_examples:
                        lines.append(f"- **{sub_key}**: {', '.join(str(v) for v in sub_value[:10])}")
                    count += 1
        elif isinstance(value, list):
            if include_examples:
                items = ", ".join(str(v) for v in value[:10])
                lines.append(f"- **{key}**: {items}")
            count += 1

    return "\n".join(lines)


def _format_errors(errors: list) -> str:
    """Format common errors into readable text."""
    lines = []
    for err in errors:
        if isinstance(err, dict):
            error_word = err.get("error", "?")
            correct = err.get("correct", "?")
            rule = err.get("rule", "")
            line = f"- ❌ **{error_word}** → ✅ **{correct}** ({rule})"
            note = err.get("note")
            if note:
                line += f" [Note: {note}]"
            lines.append(line)
    return "\n".join(lines)


def _format_variants(variants: dict) -> str:
    """Format spelling variants into readable text."""
    lines = []
    for standard, variant_list in variants.items():
        variants_str = ", ".join(variant_list)
        lines.append(f"- **{standard}** ← also accepted: {variants_str}")
    return "\n".join(lines)


def _truncate_context(context: str, max_items: int) -> str:
    """Truncate context to fit within a token budget (rough approximation)."""
    # Rough: 1 item ≈ 50 tokens, max_items items
    lines = context.split("\n")
    # Keep header + max_items content lines
    result_lines = []
    content_count = 0
    for line in lines:
        if line.startswith("#") or line.startswith("==") or not line.strip():
            result_lines.append(line)
        elif content_count < max_items:
            result_lines.append(line)
            content_count += 1

    result = "\n".join(result_lines)
    result += "\n\n... (context truncated for token budget)"
    return result


# Header for the LLM context
HEADER = """# Luxembourgish (Lëtzebuergesch) Orthography Rules

You are working with Luxembourgish text. Luxembourgish is a West-Germanic language
spoken by ~400,000 people, primarily in Luxembourg. It has an official orthography
defined by the Conseil fir d'Lëtzebuerger Sprooch (CPLL) and the Zenter fir d'Lëtzebuerger
Sprooch (ZLS). The current rules are from the 6th edition (2024).

CRITICAL: Luxembourgish is NOT German. Do NOT apply German spelling rules. Key differences:

1. **No ß** — Luxembourgish uses `ss` where German uses `ß` (Straße → Strooss)
2. **The n-rule** — `n` drops before consonants: *eng schéin Dach* (not *ei schéi Dach*),
   but `n` stays before vowels and d/t: *eng schéin Dach*, *den Dach*
3. **Vowel doubling** — Long vowels before multiple consonants are doubled: *Aarbecht* (not *Arbecht*)
4. **ë (trema)** — Short ö-like sound is written `ë`, not `ö`: *Lëtzebuerg* (not *Lötzebuerg*)
5. **é before ch/ck/ng** — Short e sound before ch, ck, ng, nk, x is written `é`: *dréchen, zéng*
6. **No silent h** — h does NOT mark vowel length: *Anung* (not *Ahnung*), *Faart* (not *Fahrt*)
7. **Diphthongs are always long** — No consonant doubling after diphthongs: *gelies* (not *geliess*)
8. **Capitalized nouns** — All nouns are capitalized, like German
9. **Foreign words keep their spelling** — French accents preserved: *Barrière, Employé*
10. **ie is a diphthong** — ie = [iə], NOT a long i like in German

The following sections contain the complete orthography rules you need."""