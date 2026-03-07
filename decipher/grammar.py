"""
Meroitic Grammar Inference Engine
====================================
Infers grammatical structure from Meroitic inscriptions using:

  1. Positional analysis (where words appear in the sentence)
  2. Morphological parsing (suffix/prefix stacking rules)
  3. Phrase structure recognition (NP, VP, etc.)
  4. Slot-grammar approach (template matching)
  5. Cross-inscription pattern learning

Based on frameworks from:
  - Hintze 1979 "Beiträge zur meroitischen Grammatik"
  - Hofmann 1981 "Material für eine meroitische Grammatik"
  - Rilly 2007 "La langue du royaume de Méroé" Chapter 8 (Grammar)
"""

from collections import defaultdict, Counter
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# MORPHOLOGICAL PARSER
# ═══════════════════════════════════════════════════════════════════════════════

class MorphologicalParser:
    """Parses Meroitic tokens into morpheme chains with grammatical labels."""

    def __init__(self, vocabulary: dict, morphemes: dict, royal_names: dict):
        self.vocabulary = vocabulary
        self.morphemes = morphemes
        self.royal_names = royal_names
        # Build sorted roots (longest first for greedy matching)
        self.roots = sorted(vocabulary.keys(), key=len, reverse=True)
        self.known_names = set(royal_names.keys())

    def parse_token(self, token: str) -> dict:
        """Parse a single token into its constituent morphemes.

        Returns a parse dict with:
          - morphemes: list of {segment, type, meaning, function}
          - pos: inferred part-of-speech
          - gloss: interlinear gloss string
        """
        # First split on explicit hyphens
        raw_parts = [p for p in token.split("-") if p]

        morphemes = []
        for i, part in enumerate(raw_parts):
            parsed = self._identify_morpheme(part, position=i, total=len(raw_parts))
            morphemes.append(parsed)

        # Infer POS from morpheme chain
        pos = self._infer_pos(morphemes)

        # Build gloss
        gloss_parts = []
        for m in morphemes:
            if m["meaning"]:
                gloss_parts.append(m["meaning"])
            elif m["function"]:
                gloss_parts.append(m["function"])
            else:
                gloss_parts.append(m["segment"])
        gloss = "-".join(gloss_parts)

        return {
            "token": token,
            "morphemes": morphemes,
            "pos": pos,
            "gloss": gloss,
        }

    def _identify_morpheme(self, segment: str, position: int, total: int) -> dict:
        """Identify a single morpheme segment."""
        # Check if it's a known root
        if segment.lower() in self.vocabulary:
            entry = self.vocabulary[segment.lower()]
            return {
                "segment": segment,
                "type": "root",
                "category": entry.get("category", ""),
                "meaning": entry.get("translation", ""),
                "function": "",
                "certainty": entry.get("certainty", 0.5),
            }

        # Check if it's a proper name
        if segment in self.known_names:
            return {
                "segment": segment,
                "type": "proper_name",
                "category": "name",
                "meaning": f"[name: {segment}]",
                "function": "",
                "certainty": 0.95,
            }

        # Check if it's a proper name by capitalization
        if segment and segment[0].isupper():
            return {
                "segment": segment,
                "type": "proper_name",
                "category": "name",
                "meaning": f"[name: {segment}]",
                "function": "",
                "certainty": 0.70,
            }

        # Check if it's a known grammatical morpheme
        suffix_key = f"-{segment}"
        prefix_key = f"{segment}-"
        if suffix_key in self.morphemes and position > 0:
            entry = self.morphemes[suffix_key]
            return {
                "segment": segment,
                "type": "suffix",
                "category": entry.get("category", "suffix"),
                "meaning": "",
                "function": entry.get("function", ""),
                "certainty": entry.get("certainty", 0.5),
            }
        if prefix_key in self.morphemes and position == 0:
            entry = self.morphemes[prefix_key]
            return {
                "segment": segment,
                "type": "prefix",
                "category": entry.get("category", "prefix"),
                "meaning": "",
                "function": entry.get("function", ""),
                "certainty": entry.get("certainty", 0.5),
            }

        # Try to decompose into root + unknown suffix
        for root in self.roots:
            if segment.lower().startswith(root) and len(segment) > len(root):
                remainder = segment[len(root):]
                root_entry = self.vocabulary[root]
                return {
                    "segment": segment,
                    "type": "compound",
                    "category": root_entry.get("category", ""),
                    "meaning": root_entry.get("translation", ""),
                    "function": f"+{remainder}",
                    "certainty": root_entry.get("certainty", 0.3) * 0.7,
                }

        return {
            "segment": segment,
            "type": "unknown",
            "category": "",
            "meaning": "",
            "function": "",
            "certainty": 0.0,
        }

    def _infer_pos(self, morphemes: list[dict]) -> str:
        """Infer part-of-speech from morpheme chain."""
        if not morphemes:
            return "UNKNOWN"

        root = morphemes[0]
        has_verbal_suffix = any(
            m["type"] == "suffix" and m["category"] == "verbal_suffix"
            for m in morphemes
        )
        has_nominal_suffix = any(
            m["type"] == "suffix" and m["category"] == "nominal_suffix"
            for m in morphemes
        )

        cat = root.get("category", "")

        if root["type"] == "proper_name":
            return "NOUN.PROPER"
        if cat in ("deity_name", "place_name"):
            return "NOUN.PROPER"
        if cat == "title":
            return "NOUN.TITLE"
        if cat in ("person", "kinship"):
            return "NOUN"
        if cat in ("religion", "funerary", "geography", "architecture", "material", "noun"):
            return "NOUN"
        if cat == "adjective":
            return "ADJ"
        if cat == "verb" or has_verbal_suffix:
            return "VERB"
        if cat == "pronoun":
            return "PRON"
        if cat == "determiner":
            return "DET"
        if cat == "number":
            return "NUM"
        if has_nominal_suffix:
            return "NOUN"
        return "UNKNOWN"


# ═══════════════════════════════════════════════════════════════════════════════
# PHRASE STRUCTURE ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class PhraseAnalyzer:
    """Groups parsed tokens into phrases and clauses."""

    # Phrase boundary heuristics based on Meroitic grammar
    PHRASE_PATTERNS = {
        "INVOCATION": {
            "pattern": ["deity_invocation"],
            "markers": {"wos", "wos-i", "mk", "mk-i", "mk-i-se", "mk-se"},
        },
        "NOUN_PHRASE": {
            "pattern": ["noun", "modifier*", "suffix*"],
        },
        "TITLE_PHRASE": {
            "pattern": ["title_word", "name?"],
        },
        "OFFERING_PHRASE": {
            "pattern": ["offering_noun+", "verb"],
        },
    }

    def analyze_phrase_structure(self, parsed_tokens: list[dict]) -> list[dict]:
        """Group tokens into phrase-level constituents."""
        phrases = []
        current_phrase = {"type": None, "tokens": [], "start": 0}
        i = 0

        while i < len(parsed_tokens):
            tok = parsed_tokens[i]
            pos = tok["pos"]
            cat = tok["morphemes"][0]["category"] if tok["morphemes"] else ""

            # Detect phrase boundaries
            if self._is_invocation_start(tok):
                if current_phrase["tokens"]:
                    phrases.append(current_phrase)
                current_phrase = {"type": "INVOCATION", "tokens": [tok], "start": i}

            elif self._is_offering_term(tok):
                if current_phrase["type"] != "OFFERING":
                    if current_phrase["tokens"]:
                        phrases.append(current_phrase)
                    current_phrase = {"type": "OFFERING", "tokens": [tok], "start": i}
                else:
                    current_phrase["tokens"].append(tok)

            elif pos == "VERB":
                if current_phrase["type"] == "OFFERING":
                    current_phrase["tokens"].append(tok)
                    phrases.append(current_phrase)
                    current_phrase = {"type": None, "tokens": [], "start": i + 1}
                else:
                    if current_phrase["tokens"]:
                        phrases.append(current_phrase)
                    phrases.append({"type": "VERB_PHRASE", "tokens": [tok], "start": i})
                    current_phrase = {"type": None, "tokens": [], "start": i + 1}

            elif pos == "NOUN.PROPER":
                # Name might be part of a title phrase
                if current_phrase["type"] in ("TITLE", "REGENT"):
                    current_phrase["tokens"].append(tok)
                else:
                    if current_phrase["tokens"]:
                        phrases.append(current_phrase)
                    current_phrase = {"type": "NAME_BLOCK", "tokens": [tok], "start": i}

            elif pos == "NOUN.TITLE":
                if current_phrase["tokens"]:
                    phrases.append(current_phrase)
                current_phrase = {"type": "TITLE", "tokens": [tok], "start": i}

            elif pos == "ADJ":
                current_phrase["tokens"].append(tok)

            elif pos == "NOUN" and cat in ("kinship", "person"):
                current_phrase["tokens"].append(tok)

            elif pos == "NOUN" and cat == "geography":
                if current_phrase["type"] != "LOCATION":
                    if current_phrase["tokens"]:
                        phrases.append(current_phrase)
                    current_phrase = {"type": "LOCATION", "tokens": [tok], "start": i}
                else:
                    current_phrase["tokens"].append(tok)

            elif pos == "NOUN" and cat == "religion":
                current_phrase["tokens"].append(tok)

            else:
                current_phrase["tokens"].append(tok)

            i += 1

        if current_phrase["tokens"]:
            phrases.append(current_phrase)

        # Set types for untyped phrases
        for phrase in phrases:
            if phrase["type"] is None:
                phrase["type"] = self._infer_phrase_type(phrase["tokens"])

        return phrases

    def _is_invocation_start(self, tok: dict) -> bool:
        root = tok["morphemes"][0]["segment"].lower() if tok["morphemes"] else ""
        return root in ("wos", "amni", "apedmk", "sebke", "mnp", "aresnp", "hore", "mhe")

    def _is_offering_term(self, tok: dict) -> bool:
        root = tok["morphemes"][0]["segment"].lower() if tok["morphemes"] else ""
        return root in ("ate", "yi")

    def _infer_phrase_type(self, tokens: list[dict]) -> str:
        pos_seq = [t["pos"] for t in tokens]
        if "NOUN.PROPER" in pos_seq:
            return "NAME_BLOCK"
        if "NOUN.TITLE" in pos_seq:
            return "TITLE"
        if any(p.startswith("NOUN") for p in pos_seq):
            return "NOUN_PHRASE"
        if "VERB" in pos_seq:
            return "VERB_PHRASE"
        return "FRAGMENT"


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE MATCHER
# ═══════════════════════════════════════════════════════════════════════════════

class TemplateMatcher:
    """Matches inscriptions against known syntactic templates."""

    def __init__(self, syntactic_rules: dict):
        self.templates = syntactic_rules.get("sentence_templates", {})

    def match_template(self, phrases: list[dict]) -> dict:
        """Determine which template best fits the phrase structure."""
        phrase_types = [p["type"] for p in phrases]

        scores = {}
        for template_name, template in self.templates.items():
            score = self._score_template(phrase_types, phrases, template_name)
            scores[template_name] = score

        best = max(scores, key=scores.get) if scores else "unknown"
        return {
            "best_template": best,
            "confidence": scores.get(best, 0),
            "all_scores": scores,
        }

    def _score_template(self, phrase_types: list[str], phrases: list[dict], template_name: str) -> float:
        """Score how well phrases match a template."""
        score = 0.0

        # Flatten all root segments
        all_roots = set()
        for p in phrases:
            for tok in p["tokens"]:
                for m in tok["morphemes"]:
                    all_roots.add(m["segment"].lower())

        if template_name == "funerary_offering":
            if "INVOCATION" in phrase_types:
                score += 2.0
            if "OFFERING" in phrase_types:
                score += 3.0
            if any(r in all_roots for r in ("ate", "yi")):
                score += 2.0
            if any(r in all_roots for r in ("wos", "mk")):
                score += 1.0
            if any(r in all_roots for r in ("pesto",)):
                score += 1.5
            if any(r in all_roots for r in ("abr", "kdi")):
                score += 0.5

        elif template_name == "royal_enthronement":
            if any(r in all_roots for r in ("qore", "kdke")):
                score += 3.0
            if any(r in all_roots for r in ("amni",)):
                score += 2.0
            if any(r in all_roots for r in ("tenke", "akine", "to")):
                score += 2.0
            if any(r in all_roots for r in ("beke", "selele")):
                score += 1.0
            if "OFFERING" not in phrase_types:
                score += 1.0
            if any(r in all_roots for r in ("qo", "mlo")):
                score += 0.5

        elif template_name == "temple_dedication":
            if any(r in all_roots for r in ("apedmk", "sebke", "mhe", "mnp", "aresnp")):
                score += 3.0
            if any(r in all_roots for r in ("selele",)):
                score += 2.0
            if "OFFERING" not in phrase_types:
                score += 1.5
            if not any(r in all_roots for r in ("qore", "kdke")):
                score += 1.0
            if any(r in all_roots for r in ("mk",)):
                score += 1.0
            if any(r in all_roots for r in ("beke", "mke")):
                score += 0.5

        elif template_name == "genealogical":
            if any(r in all_roots for r in ("lh", "sr", "beke")):
                score += 3.0
            if "NAME_BLOCK" in phrase_types:
                score += 1.5

        return score


# ═══════════════════════════════════════════════════════════════════════════════
# WORD ORDER ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class WordOrderAnalyzer:
    """Analyzes word order patterns to confirm/refine SOV hypothesis."""

    def analyze_word_order(self, inscriptions: list[dict], parser: MorphologicalParser) -> dict:
        """Analyze positional distributions of POS categories."""
        pos_positions: dict[str, list[float]] = defaultdict(list)
        bigram_counter: Counter = Counter()

        for insc in inscriptions:
            tokens = [t.strip() for t in insc["text"].split(":") if t.strip()]
            total = len(tokens)
            if total == 0:
                continue

            parses = [parser.parse_token(t) for t in tokens]
            pos_seq = [p["pos"] for p in parses]

            for i, parse in enumerate(parses):
                # Normalized position [0, 1]
                norm_pos = i / total
                pos_positions[parse["pos"]].append(norm_pos)

                if i < len(parses) - 1:
                    bigram_counter[(pos_seq[i], pos_seq[i + 1])] += 1

        # Compute average positions
        avg_positions = {}
        for pos, positions in pos_positions.items():
            avg_positions[pos] = {
                "mean": sum(positions) / len(positions),
                "count": len(positions),
                "min": min(positions),
                "max": max(positions),
            }

        return {
            "average_positions": avg_positions,
            "pos_bigrams": bigram_counter.most_common(20),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def create_parser(vocabulary: dict, morphemes: dict, royal_names: dict) -> MorphologicalParser:
    return MorphologicalParser(vocabulary, morphemes, royal_names)

def create_phrase_analyzer() -> PhraseAnalyzer:
    return PhraseAnalyzer()

def create_template_matcher(syntactic_rules: dict) -> TemplateMatcher:
    return TemplateMatcher(syntactic_rules)

def create_word_order_analyzer() -> WordOrderAnalyzer:
    return WordOrderAnalyzer()
