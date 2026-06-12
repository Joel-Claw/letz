"""Structured Luxembourgish orthography rules.

Based on the official "D'Lëtzebuerger Orthografie" (6th edition, 2024)
published by the Conseil fir d'Lëtzebuerger Sprooch (CPLL) and
Zenter fir d'Lëtzebuerger Sprooch (ZLS).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent.parent / "data"


@dataclass
class Rule:
    """A single orthography rule."""
    id: str
    title: str
    title_lb: str
    description: str
    description_lb: str
    examples: list[str] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    sub_rules: list["Rule"] = field(default_factory=list)


@dataclass
class VowelRule:
    """Rule about vowel spelling."""
    vowel: str
    context: str  # "long_stressed", "short_stressed", "unstressed", "end_of_word"
    spelling: str
    condition: str
    examples: list[str] = field(default_factory=list)


@dataclass
class ConsonantRule:
    """Rule about consonant spelling."""
    consonant: str
    context: str
    spelling: str
    condition: str
    examples: list[str] = field(default_factory=list)


# =============================================================================
# VOWEL RULES (Chapter 1-2)
# =============================================================================

VOWEL_QUANTITY_RULES: dict[str, str] = {
    "long_before_consonants": "A long vowel in a stressed syllable before two or more consonants is doubled: Aarbecht, laang, liichten, Luucht",
    "long_before_single_consonant": "A long vowel at the end of a word or before a single consonant is written once: blo, Fra, kal, Otem",
    "short_vowel": "A short vowel is always written once: Album, blann, Lastik, Schong",
    "stumm_h": "The silent h is NOT used in Luxembourgish to mark vowel length: Ausnahme (not Ausnahhme). Exception: some words have German spelling as variant (Fürerschäin/Führerschäin)",
}

LONG_VOWEL_RULES: dict[str, list[str]] = {
    "before_single_consonant": [
        "Af, al, aner, Biz, Dag, du otems, falen, Libeslidd, molen, schif, tuten"
    ],
    "at_word_end": [
        "A, Fra, Mo, ni, Su",
        "Exception: Zoo keeps doubled vowel"
    ],
    "before_multiple_consonants": [
        "Aarbecht, laang, liichten, Luucht, riicht, Sprooch",
        "du mools, hie moolt (but: ech molen)",
        "du tuuts (but: ech tuten, hien tut)",
    ],
}

SHORT_VOWEL_RULES: dict[str, list[str]] = {
    "consonant_doubling": [
        "änneren, Ball, Bidden, gutt, Hummer, iwwer, Kapp, kromm, Resümmee"
    ],
    "consonant_cluster": [
        "Dünger, fuschen, Hirsch, Hong, Kand, Krich, Land, Paschtouer, picken, Planz, Stand, Zant"
    ],
    "no_doubling_possible": [
        "x: Box, faxen",
        "g (as fricative): Spigel, Vugel",
        "j: Knujel, vijenzeg",
        "soft s: Dosen, Musel",
    ],
}

# Vowel e rules (Chapter 2)
E_RULES: dict[str, dict] = {
    "long_ee": {
        "rule": "The long vowel e is written 'ee' when stressed or in certain unstressed endings",
        "examples": ["eeneg", "Reegel", "weeder nach", "Ee", "een", "deen", "Fleesch", "jee", "Reen", "Wee"],
        "unstressed_endings": ["angeneem", "Bëbee", "Feierlechkeet", "Fräiheet", "Schéinheet"],
        "exceptions": {
            "country_names": "Chile, Nepal, Norwegen, Schweden (single e even when long)",
            "derivatives_double": "Chileen, Chinees, Italieener, nepaleesesch, schweedesch",
            "foreign_prefixes": "beta-, de-, demo(-), dezi-, ego(-), epi-, geo-, hetero(-), mega(-), meta-, meteo(-), metro(-), neo-, (-)ped(-), peri-, pre-, re-, retro(-), steno(-), stereo(-), tele-, theo-, xeno- → single e only",
            "foreign_endings": "Substantives on -um/-us: Evangelium, Klerus, Plenum, Tetanus",
            "variant_forms": "Problem/Probleem, Alphabet/Alphabeet, Februar/Feebruar, Medien/Meedien, Meter/Meeter",
        }
    },
    "short_e_ae": {
        "rule": "The sound like short ä is written 'e' by default: Blech, Dreck, Fleck, keng, kennen, Persoun. Written 'ä' when derived from a word with 'a': Schwämm (from schwammen), Träpplek (from Trap)",
    },
    "short_e_acute": {
        "rule": "The short stressed [e] is written 'é' before ch, chs, ck, ng, nk, x",
        "examples": ["hie brécht", "dréchen", "sécher", "Spréch", "héchstens", "déck", "zéng", "blénken", "féx"],
        "unstressed_no_accent": "Diddeleng, Dippech, Éislek, Heemecht, Musek, zwanzeg",
        "pronoun_exceptions": "ech, mech, dech, sech, meng, deng, seng",
    },
    "short_e_trema": {
        "rule": "The sound like short ö is written 'ë' (e with trema) in stressed syllables",
        "examples": ["Bëbee", "Bevëlkerung", "ëffentlech", "fënnef", "Mënsch", "Stëbs"],
        "unstressed_no_trema": "Aen, Apel, Bouwen, droen, elo, emol, eraus, héieren, kachen",
        "function_words_no_trema": "Artikel: dem, den, der; Pronomen: de, em, en, er, es, et, mer, se; Negatioun: net; Partikel: ze; Prefixen: be-, ge-",
        "never_before": "Never ë before ch, chs, ck, ng, nk, x (those take é)",
        "always_before_sch": "Always ë before sch: Brëscht, Dësch, Fëscher, Këscht, mëschen",
    },
    "apostrophe": {
        "rule": "Apostrophe used for: d' (feminine/neuter article), d' (plural article). The word 'ze' keeps its e: 'ze iessen'. In informal text, 'et' and 'ze' can drop e with apostrophe: 't ass waarm', 'z'entdecken'",
    },
}

# Diphthong rules (Chapter 3)
DIPHTHONG_RULES: dict[str, dict] = {
    "au": {
        "sounds": ["[ɑʊ]", "[æːʊ]"],
        "examples": {
            "[ɑʊ]": "Bauer, haut, jaus, maulen",
            "[æːʊ]": "Braut, dauschen, Haut, lauter",
        },
    },
    "ei": {
        "sounds": ["[ɑɪ]"],
        "examples": "Feier, nei, reimen",
    },
    "ai": {
        "rule": "ai is the umlaut of au: Daum→Daimchen, bauen→Gebai, Maus→Mais",
        "examples": "Raiber, Saier, Pai (for French paye)",
    },
    "äi": {
        "sounds": ["[æːɪ]"],
        "examples": "Äis, bäissen, däitlech, fläisseg, mäin, näischnotzeg",
        "note": "Can also be umlaut of au: Fauscht→Fäischt, dauschen→Gedäischs",
    },
    "éi": {
        "sounds": ["[ɜɪ]"],
        "examples": "béis, Kéier, léinen",
    },
    "ou": {
        "sounds": ["[əʊ]"],
        "examples": "Bouf, lounen, wouer",
    },
    "ie": {
        "sounds": ["[iə]"],
        "examples": "bieden, Biesem, lieweg",
        "note": "ie is always a diphthong in Luxembourgish, NOT a long i as in German. hatt liest (not like German sie liest)",
    },
    "ue": {
        "sounds": ["[uə]"],
        "examples": "Buedem, bueden, lues",
    },
}

# R-rule (Chapter 3.2)
R_RULES: dict[str, dict] = {
    "i_before_r": {
        "rule": "When i is long before r, an e is inserted → ier diphthong",
        "examples": "Bierg, Bierger, duerch, Fierschter, Kierch, Muert, natierlech, Tuerm, Wiert, Wuert",
        "exceptions": "dir, Dir, mir, hir; vir, fir, zur; ur- prefix: ural, Ursaach; foreign -ir: Saphir, Souvenir; feminine -ur: Kultur, Natur, Struktur",
    },
    "u_before_r": {
        "rule": "When u is long before r, an e is inserted → uer diphthong",
        "examples": "Buer, bueren, fueren, Gehier, Geschier, huerelen, Spuer, Tuer",
        "short_u_exception": "When u is short before r, no e is inserted: Hirsch, Kirsch, Wirschtchen, Wurscht",
    },
    "o_before_r": {
        "rule": "o before r often has e as hiatus: boer, Hoer, Joer, kloer, moer",
        "inflection": "e drops in inflected forms: boert, kloert, Joren, jorelaang, horeg",
    },
    "ae_before_r": {
        "rule": "Long ä before r + consonant is written äe: Äerd, Päerd, dir wäert",
        "single_r": "When r is the only consonant after ä, no e: äre Bouf, däreg, gären, Här, Märerchen",
    },
}

# =============================================================================
# CONSONANT RULES (Chapter 4)
# =============================================================================

CONSONANT_RULES: dict[str, dict] = {
    "doubling": {
        "rule": "After a short stressed vowel, more than one consonant must follow. Either the consonant is doubled or a cluster of different consonants follows.",
        "doubled": "änneren, Ball, Bidden, gutt, Hummer, iwwer, Kapp, kromm",
        "cluster": "Dünger, fuschen, Hirsch, Hong, Kand, Krich, Land, Paschtouer",
        "cannot_double": "x, g (as fricative), j, soft s cannot be doubled",
        "function_words": "am, an, bis, drop, drun, eran, erop, him, hin, mam, mat, ob, op, um, un, vum, vun, zum — short vowel + single consonant in function words",
        "known_exceptions": "Appetit, Bus, Echec, Fabrik, Hit, Job, Katholik, Klinik, Liter, Lok, Medezin, Minett, Modell, parallel, Politik, Titel — consonant not doubled in base form",
    },
    "word_end_devoicing": {
        "rule": "At the end of a word, a hard consonant is usually heard even when written with b, d, g, v, w. Writing follows the German spelling model.",
        "examples": {
            "f_v_w": "Léiw (German Löwe), léif (German lieb), brav — Bouf, Bréif, Buschtaf",
            "b_p": "Ribb, ob / Koup, Krop, Rëpp, op",
            "g_k": "analog, Drog / Bok, Schnok, Tubak",
            "d_t": "Doud, Lidd, midd, Rad / dat, dout, Muert, Rat",
        },
        "alternation": "Consonant alternates in inflection: Blutt→bluddeg, Bréif→Bréiwer, dout→doudeg, gutt→gudden",
    },
    "h": {
        "rule": "The letter h is only written when pronounced: doheem, geheien, hannen, hatt, haut, hien, hiewen, Hoer. NOT used to mark vowel length: Anung, berüümt, Bün, Erfarung, Faart, wärend",
    },
    "g_and_ch": {
        "g_as_g": "g at word start usually [g]: Gäns, Geld, giel, Glace",
        "g_fricative": "g as fricative is NOT doubled after short stressed vowel: Bigel, Spigel, Vigel, Kugel",
        "g_or_ch": "After long vowel/diphthong, fricative follows German spelling: Bierg (Berg), Buerg (Burg), Dag (Tag) / aacht, brooch, Daach, duerch, Nuecht",
        "short_vowel_ch": "In stressed final syllable after short vowel, always ch: Ausfluch, ewech, Fluch, genuch, Krich, Zich",
    },
    "sch": {
        "rule": "sch represents [ʃ]. Never doubled: maschen, Fëscher, Schwämm. Before sch, é never appears — always ë: Brëscht, Dësch, Fëscher",
    },
    "s_ss": {
        "rule": "Sharp s [s] at end of word or before consonant: Haus, Eis, las, mais. Voiced s [z] between vowels: Haiser, Meedchen, risen. ss for sharp s between vowels to distinguish from voiced: bäissen, dobaussen, Fass",
        "sz_note": "ß is NOT used in Luxembourgish",
    },
    "ck_tz": {
        "rule": "ck replaces kk (Bréck, Déck, Geschéck, zréck). tz replaces zz (Glitz, Härz, hitzeg, Plaz, schmatzen). After diphthongs, no ck or tz: Bauz, Biesem, eraus, Mous",
    },
    "j": {
        "rule": "j is [j] or [ʒ]. Cannot be doubled: Jalousie, Jangli, Jar, jécken, jidder, Jofferen, Jugement",
    },
}

# =============================================================================
# N-RULE (Chapter 6)
# =============================================================================

N_RULE: dict[str, dict] = {
    "general": {
        "rule": "n is dropped before consonants in Luxembourgish",
        "example": "e schéint Meedchen (not: eng schéint), bei gudden Zäiten (not: gudden), dat si schéi Lidder (not: schéin)",
    },
    "n_kept": {
        "before_vowels": "n is kept before vowels: eng schéin a kleng Kand",
        "before_d_t": "n is kept before words starting with d or t: eng schéin Dach, villen Dank",
        "prefix_on_in": "n is kept in prefixes on- and in-: onbehollef, ongär, onméiglech, inkompetent",
        "before_punctuation": "n is always kept before punctuation: Mir wollte froen, wéini et ufänkt.",
        "before_quotes": "n is kept before typographic emphasis: Et nennt een hien de „Kropemann“.",
    },
    "n_dropped": {
        "before_consonants": "n drops before consonants: e schéint Meedchen, bei gudden Zäiten",
        "adjectives_en": "Adjectives ending in -en drop n: e Meedche gesinn, de Moie kommen",
        "substantives_aen_een": "Substantives on -äin optionally drop n: de Wäi/Schwäi/Latäi or de Wäin/Schwäin/Latäin",
        "before_si_se_etc": "n is optional before si, se, säin, seng, sech, sou: hu si or hunn si",
    },
    "names": {
        "rule": "n is kept at the end of personal names and brands: Madamm Rinnen, Ruben, Bahlsenkichelcher",
    },
    "place_names": {
        "rule": "Place names on -en follow n-rule: an Italie/Italien, an Asien/Asie",
        "optional": "Place names can optionally keep n: zu Lëntge/zu Lëntgen, op München/op Münche",
    },
}

# =============================================================================
# FOREIGN WORDS (Chapter 7)
# =============================================================================

FOREIGN_WORD_RULES: dict[str, dict] = {
    "general": {
        "rule": "Foreign words keep their spelling. Foreign substantives are capitalized: Abus, Accent, Jeep, Weekend",
        "integration": "Lautlich integrated foreign words can be fully assimilated: Büfdeck, Diwwi, Fissi, Jelli, Koseng, Monnonk, Schantjen, Tëlee, Vëlo, Wallis",
    },
    "french": {
        "diacritics": "French accent grave and circonflexe are kept. French accent aigu only in final syllable: Barrière, Bréifboîte, Decisioun, Employé, Musée",
        "silent_e": "Silent e kept in -ie, -ue, -ée words and when word unrecognizable without it: Poesie, Avenue, Renommée, Avantage, Chance, Garage",
        "silent_e_dropped": "Otherwise, Luxembourgish spelling drops silent e: Bott, Gripp, Initiativ, Mall, Pist, Tax, Vitess, Zon",
        "consonant_doubling": "When short stressed vowel before final consonant in Luxembourgish spelling: Agraff, Damm, Etapp, Finall, Limitt, Vitaminn",
    },
    "english": {
        "plural_s": "English words can take Luxembourgish plural -en/-er or English -s: ee Fan, zwee Fannen/Fans",
        "n_rule": "n-rule applies to English words: en Job, en User; but: e One-Night-Stand",
    },
}

# =============================================================================
# CAPITALIZATION (Chapter 8)
# =============================================================================

CAPITALIZATION_RULES: dict[str, dict] = {
    "nouns": "All nouns and nominalizations are capitalized: d'Aarbecht, e Schéinheet",
    "fixed_expressions": "Fixed expressions with nouns keep capitalization: an der Rei, e Kéiers, op der Plaz",
    "days_times": "Days of week and times of day are nouns (capitalized): de Méindeg, den Owend; but as adverbs lowercase: moindes, owes",
    "letters": "Individual letters and letter groups: den A, vun A bis Z",
    "abbreviations": "Abbreviations keep capitalization: d'DPD, EU, NATO",
    "numbers": "Numbers and number adjectives when used as nouns: den Drëttel, eng Millioun",
    "names_titles": "Proper names and titles: d'Madamm Schmit, de Professer Weber",
}

# =============================================================================
# COMPOUND/SEPARATE WRITING (Chapter 9)
# =============================================================================

COMPOUND_RULES: dict[str, dict] = {
    "nouns": "Compound nouns are written together: Alstad, Bamschoul, Futtball, Hammbier, Sonndeg",
    "fractions": "Fraction expressions: eng Hallef Appel, eng Drëttel Liter",
    "adjectives": "Compound adjectives together: kalbliddeg, nërdlech. With noun: e kalt Blutt (separate)",
    "verbs": "Separable verbs together when finite: stallhalen, zoustëmmen. Infinitive with ze: stallzehalen, zoustëmmen",
}

# =============================================================================
# PUNCTUATION (Chapter 10)
# =============================================================================

PUNCTUATION_RULES: dict[str, dict] = {
    "direct_speech": {
        "rule": "Direct speech uses guillemets: «Ech kommen muer», seet hien.",
        "nested": "Nested quotes: «Hien huet gesot: ‚Dat ass net richteg!‘»",
        "alternative": "Alternative quotation marks are also valid: „Ech kommen muer“, seet hien.",
    },
}


def load_orthography_rules() -> dict:
    """Load the complete orthography rules as a structured dictionary."""
    return {
        "title": "D'Lëtzebuerger Orthografie",
        "edition": "6th edition, 2024",
        "publisher": "Conseil fir d'Lëtzebuerger Sprooch (CPLL) & Zenter fir d'Lëtzebuerger Sprooch (ZLS)",
        "isbn": "978-99959-1-163-8",
        "chapters": {
            1: {
                "title_lb": "D'Vokaler a, i, o an u",
                "title_en": "The vowels a, i, o, and u",
                "rules": VOWEL_QUANTITY_RULES,
                "long_vowels": LONG_VOWEL_RULES,
                "short_vowels": SHORT_VOWEL_RULES,
            },
            2: {
                "title_lb": "De Vokal e",
                "title_en": "The vowel e",
                "rules": E_RULES,
            },
            3: {
                "title_lb": "D'Diphthongen",
                "title_en": "The diphthongs",
                "rules": DIPHTHONG_RULES,
                "r_rules": R_RULES,
            },
            4: {
                "title_lb": "D'Konsonanten",
                "title_en": "The consonants",
                "rules": CONSONANT_RULES,
            },
            5: {
                "title_lb": "D'Verben",
                "title_en": "The verbs",
                "rules": {
                    "stem_principle": "Verb stems are the base: ech molen, du mools, hie moolt (stem: mol-)",
                    "vowel_quantity": "Long vowels in stems: ech riffen, du riffs, hie rifft — but oo: ech molen, du mools, hie moolt",
                    "consonant_endings": "Verb endings follow general consonant rules. Past participle: ge- prefix, -t or -en ending",
                },
            },
            6: {
                "title_lb": "D'n-Reegel",
                "title_en": "The n-rule",
                "rules": N_RULE,
            },
            7: {
                "title_lb": "D'Friemwierder",
                "title_en": "Foreign words",
                "rules": FOREIGN_WORD_RULES,
            },
            8: {
                "title_lb": "D'Grouss- a Klengschreiwung",
                "title_en": "Capitalization",
                "rules": CAPITALIZATION_RULES,
            },
            9: {
                "title_lb": "D'Getrennt- an Zesummeschreiwung",
                "title_en": "Compound and separate writing",
                "rules": COMPOUND_RULES,
            },
            10: {
                "title_lb": "D'Interpunktioun",
                "title_en": "Punctuation",
                "rules": PUNCTUATION_RULES,
            },
        },
    }


def load_common_errors() -> list[dict]:
    """Load common Luxembourgish spelling errors and corrections."""
    return [
        # Vowel doubling errors
        {"error": "Arbecht", "correct": "Aarbecht", "rule": "Long vowel before 2+ consonants must be doubled"},
        {"error": "Otem", "correct": "Otem", "rule": "Long vowel before single consonant: NOT doubled at end of word", "note": "But: du otems, hie moolt with doubled vowel in inflected forms"},
        {"error": "Létzebuerg", "correct": "Lëtzebuerg", "rule": "ë (trema) for short ö sound, not é"},
        {"error": "Lëtzebuergesch", "correct": "Lëtzebuergesch", "rule": "Correct spelling uses ë"},
        {"error": "schön", "correct": "schéin", "rule": "German schön → Luxembourgish schéin. German ö → Luxembourgish é before ch, or ë elsewhere"},
        {"error": "mich", "correct": "mech", "rule": "German ich→ech, mich→mech. Luxembourgish does not use German pronoun spellings"},
        {"error": "dass", "correct": "datt", "rule": "Consonant doubling after short vowel: datt (not dass). Luxembourgish uses tt, not ss for [s] here"},
        {"error": "Haus", "correct": "Haus", "rule": "This IS correct. au=[ɑʊ/æːʊ] is a diphthong, no doubling after it"},
        # Common confusions
        {"error": "esou", "correct": "esou", "rule": "Correct. Initial e can be dropped: sou (Niewevariant)"},
        {"error": "eréischt", "correct": "eréischt", "rule": "Correct. Initial e can be dropped: réischt (Niewevariant)"},
        # n-rule errors
        {"error": "eng schéin Dach", "correct": "eng schéin Dach", "rule": "n is kept before d/t: NOT 'ei schéi Dach'"},
        {"error": "ei schéit Meedchen", "correct": "e schéint Meedchen", "rule": "n drops before consonants: eng→e, schéin→schéint"},
        # e-rules
        {"error": "sechs", "correct": "sechs", "rule": "Correct in German but in Luxembourgish: sechs (also correct, German loan)"},
        {"error": "dreckeg", "correct": "dreklech", "rule": "Adjective suffix is -lech, not -eg (unless from specific root)"},
        # Capitalization
        {"error": "de méindeg", "correct": "de Méindeg", "rule": "Days of the week are capitalized nouns"},
        {"error": "d'äerdm", "correct": "d'Äerd", "rule": "Nouns are always capitalized; Äerd has äe for long ä before r+consonant"},
    ]


def load_spelling_variants() -> dict[str, list[str]]:
    """Load known Luxembourgish spelling variants and their standard forms.

    Maps variant spellings to their accepted forms.
    """
    return {
        # e/ee variants
        "Alphabet": ["Alphabeet"],
        "Februar": ["Feebruar"],
        "Medien": ["Meedien"],
        "Meter": ["Meeter"],
        "Problem": ["Probleem"],
        "eben": ["eeben"],
        "extrem": ["extreem"],
        "Gen": ["Geen"],
        "heterogen": ["heterogeen"],
        "Trema": ["Veen"],
        # e/ë variants
        "äifreg": ["äifereg"],
        "goureg": ["gouereg"],
        "iwwregens": ["iwweregens"],
        "traureg": ["trauereg"],
        "waakreg": ["wakereg"],
        "Wourecht": ["Wouerecht"],
        # Variant spellings
        "Bot": ["Boot"],
        "Mos": ["Moos"],
        "Stat": ["Staat"],
        # Foreign word variants
        "Damm": ["Dame"],
        "Ekipp": ["Equipe"],
        "Mull": ["Moule"],
        "effikass": ["efficace"],
        "Pedagog": ["Pädagog"],
        # Place name n-variants
        "Lëntgen": ["Lëntge"],
        "München": ["Münche"],
        # Compound variants
        "Moolzecht": ["Molzecht"],
        "Flughafen": ["Fluchhafen"],
    }


def load_n_rule_exceptions() -> dict[str, str]:
    """Load n-rule exceptions — words where n is always kept or always dropped."""
    return {
        # n always kept before d/t
        "den": "kept before d/t and vowels",
        "eng": "kept before vowels; drops n before consonants",
        "een": "optional n-dropping: ee/een",
        "fein": "n drops: fei (schéin→schéi pattern)",
        "schéin": "n drops: schéi",
        "zwéin": "n drops: zwéi",
        # Words where n never drops
        "onbehollef": "prefix on- keeps n",
        "ongär": "prefix on- keeps n",
        "inkompetent": "prefix in- keeps n",
        # Place names (optional n)
        "Lëtzebuerg": "n kept (no -en ending)",
        "Berlin": "n kept (no -en ending)",
        "Asien": "n drops: an Asie; but can keep: an Asien",
    }


# =============================================================================
# COMMON WORD LIST (for spellchecking without API)
# =============================================================================

# High-frequency Luxembourgish words for offline spellchecking
COMMON_WORDS: set[str] = {
    # Articles & pronouns
    "de", "den", "d'", "e", "en", "eng", "dat", "wat", "dee", "déi",
    "ech", "du", "hien", "hatt", "si", "mir", "dir", "sech",
    "meng", "deng", "seng", "eist", "är", "hir",
    # Prepositions
    "an", "am", "op", "vum", "mat", "fir", "zu", "bei", "no", "virun",
    "hanner", "iwwer", "ënner", "tëschent", "duerch", "ouni", "bis",
    # Common nouns
    "Dag", "Nuecht", "Joer", "Zäit", "Haus", "Kand", "Mënsch", "Fra",
    "Mann", "Papp", "Mamm", "Schof", "Bouf", "Meedchen",
    "Aarbecht", "Schoul", "Land", "Stad", "Wee", "Saach",
    "Lëtzebuerg", "Lëtzebuergesch",
    # Common ë-words (ë is always short, no doubling needed)
    "Mëllech", "ëffentlech", "ëmmer", "Mëttwoch", "Këscht", "Fëscher",
    "gëtt", "bëtzen", "Zënter", "Gëtt",
    # Common food/drink
    "Botter", "Kaffi", "Béier", "Wäin", "Brout",
    "Kas", "Fleesch", "Geméis", "Kartoffel", "Schwéng",
    # Animals
    "Kaz", "Hond", "Maus", "Päerd", "Kou", "Schof",
    "Vull", "Fësch", "Krott", "Hues",
    # Verbs (past participles)
    "gelieft", "gemaacht", "geschriwwen", "gelies", "gesinn",
    "gefonnt", "geholl", "gelooss", "gefrot", "gesot",
    "gefaangen", "geschlofen", "gelaf", "gefall",
    # Common places
    "Lampertsbierg", "Bouneweg", "Esch", "Diddeleng", "Esch-Sauer",
    "Kleng", "Grouss", "Bierg", "Dall", "Feld", "Bësch",
    # Common adjectives
    "gutt", "schléi", "schéin", "grouss", "kleng", "nei", "al",
    "wäiss", "schwaarz", "rout", "blo", "gréng", "giel",
    # Common verbs
    "sinn", "hunn", "goen", "kommen", "maachen", "sinn", "wëllen",
    "kënnen", "mussen", "daten", "gesinn", "huelen", "fannen",
    "schreiwen", "liesen", "schwätzen", "molen", "faulen",
    # Numbers
    "een", "zwee", "dräi", "véier", "fënnef", "sechs", "siwen",
    "aacht", "néng", "zéng", "fofzéng", "nonzéng", "honnert",
    # Days
    "Méindeg", "Dënschdeg", "Mëttwoch", "Donneschdeg", "Freideg",
    "Samschdeg", "Sonndeg",
    # Seasons
    "Fréijoer", "Summer", "Hierscht", "Wanter",
    # Greetings & common phrases
    "Moien", "Äddi", "Merci", "Wannechgelift", "Entschëllegt",
    "keng", "weeder", "nach", "awer", "och", "duerch", "well",
    "wéi", "dat", "dës", "dësen", "hier", "eis", "är",
}

# Common misspellings mapped to corrections
COMMON_MISSPELLINGS: dict[str, str] = {
    # German influence
    "Letzebuerg": "Lëtzebuerg",
    "Letzebuergesch": "Lëtzebuergesch",
    "Létzebuerg": "Lëtzebuerg",
    "schön": "schéin",
    "mich": "mech",
    "dich": "dech",
    "sich": "sech",
    "dass": "datt",
    "ist": "ass",
    "ein": "eng",
    "nicht": "net",
    "auch": "och",
    "aber": "awer",
    "für": "fir",
    "und": "an",
    "oder": "oder",
    "mit": "mat",
    "von": "vun",
    "zur": "zur",
    "zum": "zum",
    # Vowel doubling errors
    "Arbecht": "Aarbecht",
    "Strass": "Strooss",
    "Fro": "Fro",  # correct - long vowel before single consonant
    "Frau": "Fra",  # Luxembourgish uses Fra, not Frau
    "Haus": "Haus",  # correct - diphthong
    "Buch": "Buch",  # correct - short u + ch cluster
    # Common confusion
    "ei Schéin": "e schéint",  # n-rule
    "ei schéin Dach": "eng schéin Dach",  # n kept before d
    # ë vs e confusion
    "Lëtzebuurg": "Lëtzebuerg",
    "gëttlech": "gëttlech",  # correct
    "gëtt": "gëtt",  # correct
    # ee vs e
    "ebben": "eeben",
    "extreem": "extreem",  # correct
    "extrem": "extrem",  # also correct variant
    # ß (not used in Luxembourgish)
    "Straße": "Strooss",
    "daß": "datt",
    "Fuß": "Fouss",
    "groß": "grouss",
    "außen": "baussen",
    "heißen": "heeschen",
}