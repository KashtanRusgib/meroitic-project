#!/usr/bin/env python3
"""
Full-Text Meroitic Decoder
=============================
Produces actual word-by-word, phrase-by-phrase decipherment of entire
Meroitic inscriptions. Unlike the template-based translator, this module
renders each token's meaning from its morphological parse and assembles
a compositional English reading that reflects the actual Meroitic text.

Output format for each inscription:
  1. Transliteration line (Meroitic in Latin script)
  2. Morpheme segmentation line
  3. Interlinear gloss line (Leipzig-style)
  4. Phrase-structure brackets
  5. Compositional free translation (word-by-word driven)
  6. Per-token confidence annotation
"""

from collections import defaultdict
from typing import Optional

from decipher import (
    VOCABULARY, MORPHEMES, SYNTACTIC_RULES, CORPUS,
    NUBIAN_COMPARATIVE, EASTERN_SUDANIC_COMPARATIVE,
    KNOWN_ROYAL_NAMES, SITES,
)
from decipher.grammar import (
    create_parser, create_phrase_analyzer, create_template_matcher,
)
from decipher.lexicon import LexiconBuilder

# ═══════════════════════════════════════════════════════════════════════════════
# MORPHEME GLOSS ABBREVIATIONS (Leipzig Glossing Rules)
# ═══════════════════════════════════════════════════════════════════════════════

GLOSS_ABBREV = {
    "plural / collective marker": "PL",
    "genitive / associative marker": "GEN",
    "locative suffix (in, at)": "LOC",
    "vocative / invocation marker": "VOC",
    "nominalizer / agent noun suffix": "NMLZ",
    "copula / focus marker": "COP",
    "3rd person singular (he/she/it)": "3SG",
    "3rd person singular possessive": "3SG.POSS",
    "1st person singular (I)": "1SG",
    "causative prefix": "CAUS",
    "transitivizer prefix": "TR",
    "stative / adjective derivation prefix": "STAT",
}


def abbreviate_gloss(function_str: str) -> str:
    """Convert a morpheme function description to a Leipzig-style abbreviation."""
    if function_str in GLOSS_ABBREV:
        return GLOSS_ABBREV[function_str]
    # Try partial match
    lower = function_str.lower()
    if "plural" in lower:
        return "PL"
    if "genitive" in lower:
        return "GEN"
    if "locative" in lower:
        return "LOC"
    if "vocative" in lower:
        return "VOC"
    if "nominaliz" in lower:
        return "NMLZ"
    if "copula" in lower or "focus" in lower:
        return "COP"
    if "3" in lower and "sing" in lower:
        return "3SG"
    if "1" in lower and "sing" in lower:
        return "1SG"
    if "causative" in lower:
        return "CAUS"
    if "possessive" in lower:
        return "POSS"
    return function_str.upper()[:4] if function_str else "?"


# ═══════════════════════════════════════════════════════════════════════════════
# ENGLISH RENDERING RULES
# ═══════════════════════════════════════════════════════════════════════════════

# How to render each vocabulary category in English phrases
CATEGORY_RENDERERS = {
    "deity_name": lambda word, entry: entry.get("translation", word).split("(")[0].strip(),
    "title": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "person": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "kinship": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "adjective": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "verb": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "geography": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "funerary": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "religion": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "material": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "architecture": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "noun": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "number": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "pronoun": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
    "determiner": lambda word, entry: entry.get("translation", word).split(",")[0].strip(),
}


class FullTextDecoder:
    """Deciphers Meroitic text token-by-token with compositional English output."""

    def __init__(self):
        comparative = dict(NUBIAN_COMPARATIVE)
        comparative.update(EASTERN_SUDANIC_COMPARATIVE)

        self.vocabulary = VOCABULARY
        self.morphemes = MORPHEMES
        self.parser = create_parser(VOCABULARY, MORPHEMES, KNOWN_ROYAL_NAMES)
        self.phrase_analyzer = create_phrase_analyzer()
        self.template_matcher = create_template_matcher(SYNTACTIC_RULES)

        builder = LexiconBuilder(VOCABULARY, MORPHEMES, comparative)
        self.lexicon = builder.build_full_lexicon(CORPUS)

    # ───────────────────────────────────────────────────────────────────────
    # CORE: Decode a single inscription
    # ───────────────────────────────────────────────────────────────────────

    def decode(self, inscription: dict) -> dict:
        """Fully decode a single Meroitic inscription.

        Returns a rich decipherment record with all analytical layers.
        """
        text = inscription.get("text", "")
        tokens = [t.strip() for t in text.split(":") if t.strip()]

        # Parse each token morphologically
        parsed = [self.parser.parse_token(tok) for tok in tokens]

        # Group into phrases
        phrases = self.phrase_analyzer.analyze_phrase_structure(parsed)

        # Template match
        template = self.template_matcher.match_template(phrases)

        # Build the 6-layer decipherment
        transliteration = self._transliteration_line(tokens)
        segmentation = self._segmentation_line(parsed)
        interlinear = self._interlinear_line(parsed)
        phrase_brackets = self._phrase_bracket_line(phrases)
        token_details = self._token_details(parsed)
        free_translation = self._compositional_translation(parsed, phrases, template)

        # Per-token confidence
        confidence_map = self._token_confidence_map(parsed)

        return {
            "id": inscription.get("id", ""),
            "site": inscription.get("site", ""),
            "type": inscription.get("type", ""),
            "period": inscription.get("period", ""),
            "medium": inscription.get("medium", ""),
            "layers": {
                "transliteration": transliteration,
                "segmentation": segmentation,
                "interlinear_gloss": interlinear,
                "phrase_structure": phrase_brackets,
                "token_details": token_details,
                "free_translation": free_translation,
            },
            "template_match": {
                "best": template.get("best_template", ""),
                "score": template.get("confidence", 0),
            },
            "confidence": confidence_map,
        }

    # ───────────────────────────────────────────────────────────────────────
    # Layer 1: Transliteration
    # ───────────────────────────────────────────────────────────────────────

    def _transliteration_line(self, tokens: list[str]) -> str:
        """Raw transliteration preserving original segmentation."""
        return " : ".join(tokens)

    # ───────────────────────────────────────────────────────────────────────
    # Layer 2: Morpheme segmentation
    # ───────────────────────────────────────────────────────────────────────

    def _segmentation_line(self, parsed: list[dict]) -> str:
        """Show morpheme boundaries with hyphens."""
        parts = []
        for p in parsed:
            morphs = p.get("morphemes", [])
            segments = [m["segment"] for m in morphs]
            parts.append("-".join(segments))
        return "  ".join(parts)

    # ───────────────────────────────────────────────────────────────────────
    # Layer 3: Interlinear gloss (Leipzig style)
    # ───────────────────────────────────────────────────────────────────────

    def _interlinear_line(self, parsed: list[dict]) -> str:
        """Leipzig-style interlinear gloss."""
        parts = []
        for p in parsed:
            morphs = p.get("morphemes", [])
            glosses = []
            for m in morphs:
                if m["type"] == "proper_name":
                    glosses.append(m["segment"])  # Names stay as-is
                elif m["type"] == "root":
                    cat = m.get("category", "")
                    meaning = m.get("meaning", "")
                    # Pronouns: use Leipzig abbreviation
                    if cat == "pronoun":
                        seg = m["segment"].lower()
                        if seg == "s":
                            glosses.append("3SG.POSS")
                        elif seg == "ne":
                            glosses.append("DEM")
                        else:
                            glosses.append(abbreviate_gloss(meaning))
                    elif meaning:
                        short = meaning.split(",")[0].split("(")[0].strip()
                        glosses.append(short)
                    else:
                        glosses.append(m["segment"])
                elif m["type"] in ("suffix", "prefix"):
                    func = m.get("function", "")
                    glosses.append(abbreviate_gloss(func))
                elif m["type"] == "compound":
                    meaning = m.get("meaning", "")
                    func = m.get("function", "")
                    short = meaning.split(",")[0].strip() if meaning else m["segment"]
                    if func:
                        short += func
                    glosses.append(short)
                else:
                    glosses.append(m["segment"])
            parts.append("-".join(glosses))
        return "  ".join(parts)

    # ───────────────────────────────────────────────────────────────────────
    # Layer 4: Phrase structure brackets
    # ───────────────────────────────────────────────────────────────────────

    def _phrase_bracket_line(self, phrases: list[dict]) -> str:
        """Show phrase groupings with labeled brackets."""
        parts = []
        for ph in phrases:
            ptype = ph.get("type", "?")
            token_strs = [t.get("token", "?") for t in ph.get("tokens", [])]
            inner = " ".join(token_strs)
            parts.append(f"[{ptype} {inner}]")
        return "  ".join(parts)

    # ───────────────────────────────────────────────────────────────────────
    # Layer 5: Token details
    # ───────────────────────────────────────────────────────────────────────

    def _token_details(self, parsed: list[dict]) -> list[dict]:
        """Detailed per-token analysis."""
        details = []
        for p in parsed:
            morphs = p.get("morphemes", [])
            root_morph = None
            suffix_list = []
            prefix_list = []

            for m in morphs:
                if m["type"] == "root" and root_morph is None:
                    root_morph = m
                elif m["type"] == "suffix":
                    suffix_list.append(m)
                elif m["type"] == "prefix":
                    prefix_list.append(m)
                elif m["type"] == "proper_name" and root_morph is None:
                    root_morph = m

            base_word = root_morph["segment"] if root_morph else p.get("token", "?")
            base_lower = base_word.lower()
            lex_entry = self.lexicon.get(base_lower) or self.lexicon.get(base_word, {})

            details.append({
                "token": p.get("token", "?"),
                "pos": p.get("pos", "UNK"),
                "root": base_word,
                "meaning": root_morph.get("meaning", "") if root_morph else "",
                "category": root_morph.get("category", "") if root_morph else "",
                "certainty": lex_entry.get("certainty", root_morph.get("certainty", 0) if root_morph else 0),
                "suffixes": [{"form": s["segment"], "function": s.get("function", "")} for s in suffix_list],
                "prefixes": [{"form": p["segment"], "function": p.get("function", "")} for p in prefix_list],
                "nubian_cognate": lex_entry.get("nubian_cognate", ""),
            })
        return details

    # ───────────────────────────────────────────────────────────────────────
    # Layer 6: Compositional free translation  (THE KEY PART)
    # ───────────────────────────────────────────────────────────────────────

    def _compositional_translation(self, parsed: list[dict],
                                   phrases: list[dict],
                                   template: dict) -> str:
        """Build a free English translation phrase-by-phrase from actual word meanings.

        This is NOT a template fill — it reads each phrase group and renders
        the actual semantic content of the tokens it contains.
        """
        rendered_phrases = []

        for ph in phrases:
            ptype = ph.get("type", "FRAGMENT")
            tokens = ph.get("tokens", [])

            if ptype == "INVOCATION":
                rendered_phrases.append(self._render_invocation(tokens))
            elif ptype == "OFFERING":
                rendered_phrases.append(self._render_offering(tokens))
            elif ptype == "NAME_BLOCK":
                rendered_phrases.append(self._render_name_block(tokens))
            elif ptype == "TITLE":
                rendered_phrases.append(self._render_title_phrase(tokens))
            elif ptype == "LOCATION":
                rendered_phrases.append(self._render_location(tokens))
            elif ptype == "VERB_PHRASE":
                rendered_phrases.append(self._render_verb_phrase(tokens))
            elif ptype == "NOUN_PHRASE":
                rendered_phrases.append(self._render_noun_phrase(tokens))
            else:
                rendered_phrases.append(self._render_generic(tokens))

        # Join phrases with appropriate punctuation
        return self._join_phrases(rendered_phrases, template)

    def _render_invocation(self, tokens: list[dict]) -> str:
        """Render a deity invocation phrase."""
        # Classify tokens
        deities = []
        religious = []
        adjectives = []
        others = []

        for tok in tokens:
            root = self._get_root(tok)
            base = root["segment"].lower() if root else ""
            cat = root.get("category", "") if root else ""
            pos = tok.get("pos", "")
            word = self._english_word(root)

            has_vocative = any("vocative" in m.get("function", "").lower()
                               for m in tok.get("morphemes", []) if m["type"] == "suffix")
            has_plural = any("plural" in m.get("function", "").lower()
                             for m in tok.get("morphemes", []) if m["type"] == "suffix")

            if cat == "deity_name" or (root and root["type"] == "proper_name"):
                deities.append(word)
            elif cat == "adjective" or pos == "ADJ":
                adjectives.append(word)
            elif cat == "religion" or base == "mk":
                if has_vocative:
                    religious.append(("voc", word))
                elif has_plural:
                    religious.append(("pl", word))
                else:
                    religious.append(("base", word))
            else:
                others.append(word)

        # Build: "O Isis, the great god" or "O Apedemak, great and good god"
        result = ""
        if deities:
            result = "O " + (" and ".join(deities))

        # Build descriptor: adjectives + religious nouns
        # If we have adjectives, attach them to the FIRST religious noun only
        desc_parts = []
        if adjectives and religious:
            adj_str = " and ".join(adjectives) if len(adjectives) <= 2 else ", ".join(adjectives)
            first = True
            for kind, rword in religious:
                if first and kind == "voc":
                    desc_parts.append(f"O {adj_str} {rword}!")
                    first = False
                elif first:
                    desc_parts.append(f"the {adj_str} {rword}")
                    first = False
                elif kind == "voc":
                    desc_parts.append(f"O {rword}!")
                else:
                    desc_parts.append(f"the {rword}")
        elif religious:
            for kind, rword in religious:
                if kind == "voc":
                    desc_parts.append(f"O {rword}!")
                elif kind == "pl":
                    desc_parts.append(f"the {rword}s")
                else:
                    desc_parts.append(f"the {rword}")
        elif adjectives:
            adj_str = " and ".join(adjectives) if len(adjectives) <= 2 else ", ".join(adjectives)
            desc_parts.append(adj_str)

        if others:
            desc_parts.extend(others)

        if desc_parts:
            desc = ", ".join(desc_parts)  # comma-separate "the god, the protection"
            if result:
                result = f"{result}, {desc}"
            else:
                result = desc
        return result if result else "[invocation]"

    def _render_offering(self, tokens: list[dict]) -> str:
        """Render an offering phrase, reading the actual items listed."""
        items = []
        verb_part = ""

        for tok in tokens:
            root = self._get_root(tok)
            pos = tok.get("pos", "")
            base = root["segment"].lower() if root else ""
            cat = root.get("category", "") if root else ""

            # Skip pronouns in offering context (they're structural, not content)
            if cat == "pronoun":
                continue

            if pos == "VERB" or cat == "verb":
                english_verb = self._english_word(root)
                suffixes = [m for m in tok.get("morphemes", []) if m["type"] == "suffix"]
                has_nmlz = any("nominaliz" in m.get("function", "").lower() for m in suffixes)
                has_cop = any("copula" in m.get("function", "").lower() or
                             "focus" in m.get("function", "").lower() for m in suffixes)
                has_3sg = any("3" in m.get("function", "") and "sing" in m.get("function", "") for m in suffixes)

                # Look up proper verb form
                vf = self.VERB_FORMS.get(english_verb, {})
                if has_nmlz and has_cop:
                    verb_part = vf.get("nmlz_passive", f"may it be {english_verb.replace('to ', '')}ed")
                elif has_nmlz:
                    verb_part = vf.get("nmlz", f"the {english_verb.replace('to ', '')}ing")
                elif has_3sg:
                    verb_part = vf.get("3sg", f"he/she {english_verb.replace('to ', '')}s")
                else:
                    verb_part = vf.get("bare", english_verb.replace("to ", ""))
            else:
                item_word = self._english_word(root)
                has_plural = any("plural" in m.get("function", "").lower() for m in tok.get("morphemes", []))
                if has_plural:
                    item_word += "(s)"
                items.append(item_word)

        result = ""
        if items:
            if len(items) == 1:
                result = items[0]
            elif len(items) == 2:
                result = f"{items[0]} and {items[1]}"
            else:
                result = ", ".join(items[:-1]) + f", and {items[-1]}"
        if verb_part:
            if result:
                result = f"{result} — {verb_part}"
            else:
                result = verb_part
        return result if result else "[offering]"

    def _render_name_block(self, tokens: list[dict]) -> str:
        """Render a name block: 'Teritedqe, good man, O offspring!'"""
        name_parts = []    # proper names
        adjectives = []    # adjective words
        nouns = []         # noun descriptors (kinship, person, etc.)
        vocatives = []     # vocative phrases

        for tok in tokens:
            root = self._get_root(tok)
            if root and root["type"] == "proper_name":
                name_parts.append(root["segment"])
            else:
                word = self._english_word(root)
                cat = root.get("category", "") if root else ""
                pos = tok.get("pos", "")
                has_vocative = any("vocative" in m.get("function", "").lower()
                                   for m in tok.get("morphemes", []) if m["type"] == "suffix")
                has_plural = any("plural" in m.get("function", "").lower()
                                 for m in tok.get("morphemes", []) if m["type"] == "suffix")

                if has_vocative:
                    vocatives.append(f"O {word}!")
                elif cat == "adjective" or pos == "ADJ":
                    adjectives.append(word)
                else:
                    if has_plural:
                        word += "s"
                    nouns.append(word)

        # Build: "Name, {adj} {noun}, O {vocative}!"
        result = ", ".join(name_parts) if name_parts else ""
        # Combine adjectives + nouns: "good man"
        desc_parts = adjectives + nouns
        if desc_parts:
            desc_str = " ".join(desc_parts)
            if result:
                result = f"{result}, {desc_str}"
            else:
                result = desc_str
        # Append vocatives
        if vocatives:
            voc_str = " ".join(vocatives)
            if result:
                result = f"{result}, {voc_str}"
            else:
                result = voc_str
        return result if result else "[name]"

    def _render_title_phrase(self, tokens: list[dict]) -> str:
        """Render a title phrase (e.g. 'of ruler Amanitore, O offspring!')."""
        # First pass: classify each token
        elements = []  # list of (kind, text) tuples
        for tok in tokens:
            root = self._get_root(tok)
            cat = root.get("category", "") if root else ""
            is_name = root["type"] == "proper_name" if root else False
            word = self._english_word(root)
            pos = tok.get("pos", "")

            suffixes = [m for m in tok.get("morphemes", []) if m["type"] == "suffix"]
            has_plural = any("plural" in m.get("function", "").lower() for m in suffixes)
            has_gen = any("genitive" in m.get("function", "").lower() for m in suffixes)
            has_voc = any("vocative" in m.get("function", "").lower() for m in suffixes)

            if is_name:
                elements.append(("name", word))
            elif cat == "pronoun":
                elements.append(("pron", word))
            elif cat == "adjective" or pos == "ADJ":
                elements.append(("adj", word))
            elif has_voc:
                elements.append(("voc", word))
            elif has_gen and (cat == "title"):
                elements.append(("gen_title", word))
            elif has_gen:
                elements.append(("gen", word))
            elif has_plural:
                elements.append(("noun_pl", word))
            elif cat == "title":
                elements.append(("title", word))
            else:
                elements.append(("noun", word))

        # Second pass: build English with proper order
        # First, group consecutive adjectives
        grouped = []
        i = 0
        while i < len(elements):
            kind, word = elements[i]
            if kind == "adj":
                # Collect consecutive adjectives
                adj_group = [word]
                while i + 1 < len(elements) and elements[i + 1][0] == "adj":
                    i += 1
                    adj_group.append(elements[i][1])
                grouped.append(("adj_group", adj_group))
            else:
                grouped.append((kind, word))
            i += 1

        parts = []
        i = 0
        while i < len(grouped):
            kind, word = grouped[i]

            if kind == "gen_title":
                parts.append(f"of {word}")
            elif kind == "gen":
                parts.append(f"of {word}")
            elif kind == "name":
                parts.append(word)
            elif kind == "pron":
                # Possessive pronoun: attach to next noun/vocative if any
                if i + 1 < len(grouped):
                    nkind, nword = grouped[i + 1]
                    if nkind == "voc":
                        parts.append(f"O {word} {nword}!")
                        i += 2
                        continue
                    elif nkind in ("noun", "noun_pl", "title"):
                        parts.append(f"{word} {nword}")
                        i += 2
                        continue
                # Else: redundant pronoun after genitive — skip
            elif kind == "voc":
                parts.append(f"O {word}!")
            elif kind == "adj_group":
                # word is actually a list of adjectives here
                adjs = word
                adj_str = " and ".join(adjs) if len(adjs) <= 2 else ", ".join(adjs[:-1]) + f", and {adjs[-1]}"
                # Look ahead: if next is a noun, combine "the great and good {noun}"
                if i + 1 < len(grouped) and grouped[i + 1][0] in ("noun", "noun_pl", "title"):
                    nkind, nword = grouped[i + 1]
                    suffix = "s" if nkind == "noun_pl" else ""
                    parts.append(f"the {adj_str} {nword}{suffix}")
                    i += 2
                    continue
                else:
                    parts.append(f"the {adj_str}")
            elif kind == "noun_pl":
                parts.append(f"the {word}s")
            elif kind == "title":
                parts.append(f"the {word}")
            else:
                parts.append(f"the {word}")
            i += 1

        return " ".join(parts)

    def _render_location(self, tokens: list[dict]) -> str:
        """Render a geographic/locative phrase."""
        parts = []
        for tok in tokens:
            root = self._get_root(tok)
            word = self._english_word(root)
            has_loc = any("locative" in m.get("function", "").lower() for m in tok.get("morphemes", []) if m["type"] == "suffix")
            if has_loc:
                parts.append(f"in {word}")
            else:
                parts.append(word)
        return " ".join(parts)

    def _render_verb_phrase(self, tokens: list[dict]) -> str:
        """Render a verb phrase using proper English verb forms."""
        parts = []
        for tok in tokens:
            root = self._get_root(tok)
            cat = root.get("category", "") if root else ""
            word = self._english_word(root)

            if cat == "verb" or tok.get("pos") == "VERB":
                suffixes = [m for m in tok.get("morphemes", []) if m["type"] == "suffix"]
                has_nmlz = any("nominaliz" in m.get("function", "").lower() for m in suffixes)
                has_cop = any("copula" in m.get("function", "").lower() or
                             "focus" in m.get("function", "").lower() for m in suffixes)
                has_3sg = any("3" in m.get("function", "") and "sing" in m.get("function", "") for m in suffixes)

                vf = self.VERB_FORMS.get(word, {})
                if has_nmlz and has_cop:
                    parts.append(vf.get("nmlz_passive", f"may it be {word.replace('to ', '')}ed"))
                elif has_nmlz:
                    parts.append(vf.get("nmlz", f"the {word.replace('to ', '')}ing"))
                elif has_3sg:
                    parts.append(vf.get("3sg", f"he/she {word.replace('to ', '')}s"))
                else:
                    parts.append(vf.get("bare", word.replace("to ", "")))
            else:
                parts.append(word)
        return " ".join(parts)

    def _render_noun_phrase(self, tokens: list[dict]) -> str:
        """Render a general noun phrase."""
        parts = []
        for tok in tokens:
            root = self._get_root(tok)
            word = self._english_word(root)
            has_plural = any("plural" in m.get("function", "").lower() for m in tok.get("morphemes", []) if m["type"] == "suffix")
            has_gen = any("genitive" in m.get("function", "").lower() for m in tok.get("morphemes", []) if m["type"] == "suffix")
            has_loc = any("locative" in m.get("function", "").lower() for m in tok.get("morphemes", []) if m["type"] == "suffix")

            if has_gen:
                word = f"of {word}"
            if has_plural:
                word += "s"
            if has_loc:
                word = f"in/at {word}"
            parts.append(word)
        return " ".join(parts)

    def _render_generic(self, tokens: list[dict]) -> str:
        """Render tokens we can't classify into a specific phrase type."""
        # Separate adjectives and nouns to produce English word order
        items = []
        for tok in tokens:
            root = self._get_root(tok)
            word = self._english_word(root)
            cat = root.get("category", "") if root else ""
            pos = tok.get("pos", "")
            if cat == "adjective" or pos == "ADJ":
                items.append(("adj", word))
            else:
                items.append(("other", word))

        # Simple: if we have adj + noun pairs, combine them
        result_parts = []
        i = 0
        while i < len(items):
            kind, word = items[i]
            if kind == "adj" and i + 1 < len(items) and items[i + 1][0] == "other":
                result_parts.append(f"{word} {items[i + 1][1]}")
                i += 2
            else:
                result_parts.append(word)
                i += 1
        return " ".join(result_parts)

    # ───────────────────────────────────────────────────────────────────────
    # Helpers
    # ───────────────────────────────────────────────────────────────────────

    def _get_root(self, parsed_token: dict) -> Optional[dict]:
        """Extract the root morpheme from a parsed token."""
        for m in parsed_token.get("morphemes", []):
            if m["type"] in ("root", "proper_name", "compound"):
                return m
        morphemes = parsed_token.get("morphemes", [])
        return morphemes[0] if morphemes else None

    # Pronoun rendering map — converts raw translations to natural English
    PRONOUN_MAP = {
        "s": "his/her",
        "ne": "this",
    }

    # Verb forms for known verbs (base → {nmlz, 3sg, bare})
    VERB_FORMS = {
        "to give": {"nmlz": "the giving", "3sg": "he/she gives", "bare": "give",
                    "nmlz_passive": "may it be given"},
        "to offer": {"nmlz": "the offering", "3sg": "he/she offers", "bare": "offer",
                     "nmlz_passive": "may it be offered"},
        "to build": {"nmlz": "the building", "3sg": "he/she builds", "bare": "build",
                     "nmlz_passive": "may it be built"},
        "to pour": {"nmlz": "the pouring", "3sg": "he/she pours", "bare": "pour",
                    "nmlz_passive": "may it be poured"},
        "to establish": {"nmlz": "the establishing", "3sg": "he/she establishes",
                         "bare": "establish", "nmlz_passive": "may it be established"},
        "to beget": {"nmlz": "the begetting", "3sg": "he/she begets", "bare": "beget",
                     "nmlz_passive": "may it be begotten"},
        "to come": {"nmlz": "the coming", "3sg": "he/she comes", "bare": "come",
                    "nmlz_passive": "may it come to pass"},
        "to go": {"nmlz": "the going", "3sg": "he/she goes", "bare": "go",
                  "nmlz_passive": "may it go forth"},
        "to make": {"nmlz": "the making", "3sg": "he/she makes", "bare": "make",
                    "nmlz_passive": "may it be made"},
        "to protect": {"nmlz": "the protecting", "3sg": "he/she protects",
                       "bare": "protect", "nmlz_passive": "may there be protection"},
        "to bring": {"nmlz": "the bringing", "3sg": "he/she brings", "bare": "bring",
                     "nmlz_passive": "may it be brought"},
        "to consecrate": {"nmlz": "the consecrating", "3sg": "he/she consecrates",
                          "bare": "consecrate", "nmlz_passive": "may it be consecrated"},
    }

    def _english_word(self, morph: Optional[dict]) -> str:
        """Get the best English rendering for a morpheme."""
        if morph is None:
            return "[?]"
        if morph["type"] == "proper_name":
            return morph["segment"]
        meaning = morph.get("meaning", "")
        cat = morph.get("category", "")

        # Special handling for pronouns — use natural English
        if cat == "pronoun":
            seg = morph["segment"].lower()
            if seg in self.PRONOUN_MAP:
                return self.PRONOUN_MAP[seg]
            # Fallback: extract parenthesized form
            if "(" in meaning and ")" in meaning:
                paren = meaning.split("(")[1].split(")")[0]
                return paren
            return meaning.split(",")[0].strip() if meaning else morph["segment"]

        if meaning and not meaning.startswith("["):
            # Take the first short translation
            return meaning.split(",")[0].split("(")[0].strip()
        # If meaning starts with [ it's a distributional guess
        if meaning and meaning.startswith("[similar to"):
            return f"[{morph['segment']}]"
        # Unknown
        if morph["segment"]:
            return f"[{morph['segment']}]"
        return "[?]"

    def _join_phrases(self, rendered: list[str], template: dict) -> str:
        """Join rendered phrase strings into a coherent sentence."""
        if not rendered:
            return "[untranslatable]"

        # Filter empty
        rendered = [r for r in rendered if r and r.strip()]
        if not rendered:
            return "[untranslatable]"

        # Clean up: strip trailing punctuation before joining
        cleaned = []
        for r in rendered:
            r = r.rstrip(".")
            cleaned.append(r)

        # Use semicolons between major clause boundaries, period at end
        if len(cleaned) == 1:
            return cleaned[0] + "."
        elif len(cleaned) == 2:
            return f"{cleaned[0]}; {cleaned[1]}."
        else:
            return "; ".join(cleaned) + "."

    def _token_confidence_map(self, parsed: list[dict]) -> dict:
        """Build a per-token confidence assessment."""
        token_confs = []
        total_cert = 0.0

        for p in parsed:
            root = self._get_root(p)
            base = root["segment"].lower() if root else ""
            lex = self.lexicon.get(base) or self.lexicon.get(root["segment"] if root else "", {})
            cert = lex.get("certainty", root.get("certainty", 0) if root else 0)

            label = "certain" if cert >= 0.8 else "probable" if cert >= 0.6 else "tentative" if cert >= 0.3 else "unknown"
            token_confs.append({
                "token": p.get("token", "?"),
                "certainty": cert,
                "label": label,
            })
            total_cert += cert

        n = len(token_confs)
        avg = total_cert / n if n else 0
        certain_count = sum(1 for t in token_confs if t["label"] == "certain")
        probable_count = sum(1 for t in token_confs if t["label"] == "probable")
        tentative_count = sum(1 for t in token_confs if t["label"] == "tentative")
        unknown_count = sum(1 for t in token_confs if t["label"] == "unknown")

        return {
            "average": round(avg, 3),
            "per_token": token_confs,
            "summary": {
                "certain": certain_count,
                "probable": probable_count,
                "tentative": tentative_count,
                "unknown": unknown_count,
                "total": n,
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PLAIN-TEXT REPORT FORMATTER
# ═══════════════════════════════════════════════════════════════════════════════

def format_decipherment(record: dict) -> str:
    """Format a single inscription's decipherment as a readable text block."""
    lines = []
    rid = record.get("id", "?")
    site = record.get("site", "?")
    itype = record.get("type", "?")
    period = record.get("period", "")
    medium = record.get("medium", "")

    layers = record.get("layers", {})
    conf = record.get("confidence", {})
    summary = conf.get("summary", {})
    avg_conf = conf.get("average", 0)

    tmpl = record.get("template_match", {})

    lines.append(f"{'═' * 76}")
    lines.append(f"  INSCRIPTION {rid}")
    meta_parts = [f"Site: {site}", f"Type: {itype}"]
    if period:
        meta_parts.append(f"Period: {period}")
    if medium:
        meta_parts.append(f"Medium: {medium}")
    lines.append(f"  {' | '.join(meta_parts)}")
    lines.append(f"{'═' * 76}")
    lines.append("")

    # Layer 1: Transliteration
    lines.append(f"  Meroitic:     {layers.get('transliteration', '')}")
    lines.append("")

    # Layer 2: Segmentation
    lines.append(f"  Segmented:    {layers.get('segmentation', '')}")
    lines.append("")

    # Layer 3: Interlinear
    lines.append(f"  Gloss:        {layers.get('interlinear_gloss', '')}")
    lines.append("")

    # Layer 4: Phrase structure
    lines.append(f"  Phrases:      {layers.get('phrase_structure', '')}")
    lines.append("")

    # Layer 5: Token-by-token annotation
    lines.append(f"  Token analysis:")
    for td in layers.get("token_details", []):
        cert = td.get("certainty", 0)
        cert_bar = "●" * int(cert * 5) + "○" * (5 - int(cert * 5))
        meaning = td.get("meaning", "") or "[unknown]"
        short_meaning = meaning.split(",")[0].split("(")[0].strip()
        suffix_str = ""
        if td.get("suffixes"):
            sfx = ", ".join(f"-{s['form']}={s['function']}" for s in td["suffixes"])
            suffix_str = f"  + {sfx}"
        cognate_str = ""
        if td.get("nubian_cognate"):
            cognate_str = f"  (cf. Nubian: {td['nubian_cognate']})"
        lines.append(
            f"    {td['token']:20s}  {td['pos']:14s}  {cert_bar}  "
            f"{short_meaning}{suffix_str}{cognate_str}"
        )
    lines.append("")

    # Layer 6: Free translation
    lines.append(f"  ┌─────────────────────────────────────────────────────────────────────┐")
    translation = layers.get("free_translation", "")
    # Word-wrap at ~67 chars
    words = translation.split()
    wrap_lines = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > 67:
            wrap_lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        wrap_lines.append(cur)
    for wl in wrap_lines:
        lines.append(f"  │  {wl:67s}  │")
    lines.append(f"  └─────────────────────────────────────────────────────────────────────┘")
    lines.append("")

    # Confidence footer
    lines.append(
        f"  Confidence: {avg_conf:.1%}  "
        f"({summary.get('certain', 0)} certain, "
        f"{summary.get('probable', 0)} probable, "
        f"{summary.get('tentative', 0)} tentative, "
        f"{summary.get('unknown', 0)} unknown)"
    )
    if tmpl.get("best"):
        lines.append(f"  Template: {tmpl['best']} (score {tmpl.get('score', 0):.1f})")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CORPUS-LEVEL STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def corpus_statistics(records: list[dict]) -> str:
    """Generate summary statistics across all decoded inscriptions."""
    lines = []
    lines.append(f"{'═' * 76}")
    lines.append(f"  DECIPHERMENT CORPUS STATISTICS")
    lines.append(f"{'═' * 76}")
    lines.append("")

    n = len(records)
    if n == 0:
        lines.append("  No inscriptions decoded.")
        return "\n".join(lines)

    # Overall confidence
    avg_confs = [r["confidence"]["average"] for r in records]
    overall_avg = sum(avg_confs) / n

    # Token stats
    all_certain = sum(r["confidence"]["summary"].get("certain", 0) for r in records)
    all_probable = sum(r["confidence"]["summary"].get("probable", 0) for r in records)
    all_tentative = sum(r["confidence"]["summary"].get("tentative", 0) for r in records)
    all_unknown = sum(r["confidence"]["summary"].get("unknown", 0) for r in records)
    all_tokens = all_certain + all_probable + all_tentative + all_unknown

    lines.append(f"  Inscriptions decoded    : {n}")
    lines.append(f"  Total tokens analyzed   : {all_tokens}")
    lines.append(f"  Average confidence      : {overall_avg:.1%}")
    lines.append("")
    lines.append(f"  Token-level breakdown:")
    lines.append(f"    Certain   (≥80%) : {all_certain:4d}  ({all_certain/all_tokens:.1%})")
    lines.append(f"    Probable  (≥60%) : {all_probable:4d}  ({all_probable/all_tokens:.1%})")
    lines.append(f"    Tentative (≥30%) : {all_tentative:4d}  ({all_tentative/all_tokens:.1%})")
    lines.append(f"    Unknown   (<30%) : {all_unknown:4d}  ({all_unknown/all_tokens:.1%})")
    lines.append("")

    # By inscription type
    type_groups = defaultdict(list)
    for r in records:
        type_groups[r.get("type", "unknown")].append(r)

    lines.append(f"  By inscription type:")
    for itype, group in sorted(type_groups.items()):
        gavg = sum(r["confidence"]["average"] for r in group) / len(group)
        lines.append(f"    {itype:20s}: {len(group):3d} inscriptions, avg confidence {gavg:.1%}")
    lines.append("")

    # By site
    site_groups = defaultdict(list)
    for r in records:
        site_groups[r.get("site", "unknown")].append(r)

    lines.append(f"  By site:")
    for site, group in sorted(site_groups.items()):
        gavg = sum(r["confidence"]["average"] for r in group) / len(group)
        lines.append(f"    {site:20s}: {len(group):3d} inscriptions, avg confidence {gavg:.1%}")
    lines.append("")

    # Unique vocabulary identified
    all_roots = set()
    all_names = set()
    for r in records:
        for td in r["layers"]["token_details"]:
            if td["pos"] == "NOUN.PROPER":
                all_names.add(td["root"])
            elif td.get("meaning") and not td["meaning"].startswith("["):
                all_roots.add(td["root"].lower())

    lines.append(f"  Unique vocabulary items translated : {len(all_roots)}")
    lines.append(f"  Unique proper names identified     : {len(all_names)}")
    lines.append("")

    lines.append(f"  {'─' * 72}")
    lines.append(f"  NOTE: Meroitic remains only partially deciphered as of 2026.")
    lines.append(f"  Phonetic values of signs are securely known (Griffith 1911),")
    lines.append(f"  but most vocabulary meanings derive from contextual inference,")
    lines.append(f"  comparative linguistics, and formulaic pattern analysis.")
    lines.append(f"  Tokens marked 'certain' reflect scholarly consensus;")
    lines.append(f"  'probable' and 'tentative' readings are computational proposals.")
    lines.append(f"  {'─' * 72}")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import json

    print("Initializing Meroitic Full-Text Decoder...")
    decoder = FullTextDecoder()

    print(f"Decoding {len(CORPUS)} inscriptions...\n")

    records = []
    for insc in CORPUS:
        record = decoder.decode(insc)
        records.append(record)

    # Print full decipherment for every inscription
    for record in records:
        print(format_decipherment(record))

    # Print corpus statistics
    print(corpus_statistics(records))

    # Save structured output
    output_path = "decipher/full_decipherment.json"
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2, default=str)
    print(f"  Structured results saved to {output_path}")

    # Also save a plain-text report
    txt_path = "decipher/full_decipherment.txt"
    with open(txt_path, "w") as f:
        f.write("MEROITIC FULL-TEXT DECIPHERMENT\n")
        f.write(f"Generated by meroitic-project decoder\n")
        f.write(f"Corpus: {len(CORPUS)} inscriptions\n\n")
        for record in records:
            f.write(format_decipherment(record))
            f.write("\n")
        f.write(corpus_statistics(records))
    print(f"  Plain-text report saved to {txt_path}")


if __name__ == "__main__":
    main()
