# lëtz 🇱🇺

**Most LLMs can't spell Luxembourgish. lëtz gives them the rules they need.**

Luxembourgish (Lëtzebuergesch) is a small language with ~400K native speakers. Most LLMs have barely any Luxembourgish in their training data, and when they try to write it, they make systematic spelling mistakes — mixing in German conventions, misapplying vowel length rules, ignoring the n-rule, and more. Retraining models on Luxembourgish isn't practical; there simply isn't enough data.

**`lëtz` takes a different approach**: instead of hoping LLMs will learn Luxembourgish from training data, it *injects* the rules and dictionary context they need. It packages the official 2024 Luxembourgish orthography rules (from CPLL/ZLS) and LOD dictionary lookups into structured prompts that any LLM can use — even ones that have never seen Luxembourgish before.

This is an experiment, not a guarantee. But it's a fundamentally different strategy: rather than "train the model on more data," it's "give the model the reference material at inference time."

> **Note:** Both `letz` and `lëtz` work as commands. The package name is `letz` (Python/PEP 503 doesn't allow ë), but the project is called **lëtz** — the proper Luxembourgish spelling.

## What it does

- **Spellcheck** Luxembourgish text using official orthography rules + LOD dictionary lookup
- **Normalize** variant spellings to standard forms (e.g., *Feebruar* → *Februar*, *Dame* → *Damm*)
- **Generate LLM prompts** that inject orthography rules so any LLM can spellcheck Luxembourgish — even models with zero Luxembourgish training data
- **LOD dictionary integration** — fetch and cache word definitions from the official Luxembourgish dictionary

## Install

```bash
pip install letz
```

Both `letz` and `lëtz` work as commands after installation.

## CLI Usage

```bash
# Check text for spelling issues
letz check "D'Lëtzebuerger Sprooch ass schéin"
# or
lëtz check "D'Lëtzebuerger Sprooch ass schéin"

# Normalize variant spellings
letz normalize "Feebruar"

# Look up a word in the LOD dictionary
letz lookup "Haus"

# Generate an LLM prompt with orthography context
letz prompt "Check this Luxembourgish text for spelling errors"
```

## Python API

```python
from letz import Spellchecker, Normalizer, LODClient, generate_llm_context

# Spellcheck
checker = Spellchecker()
results = checker.check("D'Letzebuurger Sprooch")

# Normalize
norm = Normalizer()
normalized = norm.normalize("Feebruar")  # → "Februar"

# LOD dictionary
lod = LODClient()
entry = lod.lookup("Haus")

# Generate context for LLMs
context = generate_llm_context()
# Returns structured orthography rules that an LLM can use to spellcheck Luxembourgish
```

## Why this works

The official Luxembourgish orthography rules are prescriptive and well-documented — they're a finite set of conventions that can be communicated in a prompt. The key insight:

1. **LLMs are bad at Luxembourgish because they haven't seen enough of it**, not because they can't follow rules
2. **The rules are bounded** — there are 10 chapters covering vowels, consonants, diphthongs, the n-rule, foreign words, capitalization, etc.
3. **Dictionary lookup fills the gaps** — when rules alone aren't enough, the LOD dictionary provides ground truth
4. **Prompt injection > training data** — for low-resource languages, giving the model the rules at inference time outperforms hoping it absorbed them during training

This approach won't catch every edge case. Luxembourgish has legitimate spelling variants, dialect differences, and words that simply aren't in any dictionary. But for the systematic errors that LLMs make (German ß, wrong vowel doubling, ignoring the n-rule, etc.), it works remarkably well.

## Orthography Rules

This package includes the official Luxembourgish orthography rules from the 6th edition (2024) published by the Conseil fir d'Lëtzebuerger Sprooch (CPLL) and Zenter fir d'Lëtzebuerger Sprooch (ZLS). These rules cover:

1. **Vowels a, i, o, u** — quantity rules, doubling, short/long vowels
2. **The vowel e** — long ee, short e/ä, é, ë, apostrophe
3. **Diphthongs** — au, ei, ai, äi, éi, ou, ie, ue
4. **Consonants** — doubling, word endings, special rules for g/ch, sch, s/ss, ck/tz, j
5. **Verbs** — stem principle, vowel quantity, consonant endings
6. **The n-rule** — n dropping before consonants (the single most distinctive Luxembourgish rule)
7. **Foreign words** — French, English, Greek, Latin integration
8. **Capitalization** — nouns, proper names, adjectives
9. **Compound/separate writing** — hyphenation rules
10. **Punctuation** — guillemets, direct speech

## License

MIT

## Acknowledgments

- **ZLS** (Zenter fir d'Lëtzebuerger Sprooch) and **CPLL** for the official orthography rules
- **LOD** (Lëtzebuerger Online Dictionnaire) for the dictionary API
- **spellchecker.lu** / **spellux** for prior work on Luxembourgish NLP