"""
Meroitic Translation Pipeline
================================
Integrates grammar parsing, lexicon, comparative data, and formulas
to produce full translations of Meroitic inscriptions.

Pipeline stages:
  1. Tokenize and segment the inscription text
  2. Morphological parsing of each token
  3. Template matching to identify inscription type / formula
  4. Word-by-word gloss using the lexicon
  5. Phrase-level grouping and semantic coherence check
  6. Full sentence rendering with confidence scores
"""

from typing import Optional

from decipher.grammar import (
    create_parser, create_phrase_analyzer, create_template_matcher,
)
from decipher.lexicon import LexiconBuilder


class TranslationPipeline:
    """End-to-end translation pipeline for Meroitic inscriptions."""

    def __init__(self, vocabulary: dict, morphemes: dict,
                 comparative_data: dict, corpus: list[dict],
                 syntactic_rules: dict):
        # Build sub-components
        self.parser = create_parser(vocabulary, morphemes, {})
        self.phrase_analyzer = create_phrase_analyzer()
        self.template_matcher = create_template_matcher(syntactic_rules)

        # Build the lexicon
        builder = LexiconBuilder(vocabulary, morphemes, comparative_data)
        self.lexicon = builder.build_full_lexicon(corpus)

        self.vocabulary = vocabulary
        self.morphemes = morphemes
        self.syntactic_rules = syntactic_rules

    def translate(self, inscription: dict) -> dict:
        """Translate a single Meroitic inscription.

        Returns a dict with:
          - interlinear: token-by-token gloss
          - phrase_groups: semantic phrase groupings
          - template: matched template / inscription type
          - free_translation: best attempt at an English rendering
          - confidence: overall confidence score
        """
        text = inscription.get("text", "")
        tokens = [t.strip() for t in text.split(":") if t.strip()]

        # Stage 1: Morphological parse
        parsed = [self.parser.parse_token(tok) for tok in tokens]

        # Stage 2: Phrase grouping
        phrases = self.phrase_analyzer.analyze_phrase_structure(parsed)

        # Stage 3: Template match
        template_result = self.template_matcher.match_template(phrases)
        # Normalize keys for downstream use
        template_result["best_match"] = template_result.get("best_template", "")
        template_result["best_score"] = template_result.get("confidence", 0)

        # Stage 4: Interlinear gloss
        interlinear = self._build_interlinear(parsed)

        # Stage 5: Free translation
        free = self._render_free_translation(
            parsed, phrases, template_result, inscription
        )

        # Stage 6: Confidence scoring
        confidence = self._compute_confidence(parsed, template_result)

        return {
            "source": text,
            "interlinear": interlinear,
            "phrase_groups": phrases,
            "template": template_result,
            "free_translation": free,
            "confidence": confidence,
        }

    def translate_corpus(self, corpus: list[dict]) -> list[dict]:
        """Translate every inscription in the corpus."""
        results = []
        for insc in corpus:
            result = self.translate(insc)
            result["inscription_id"] = insc.get("id", "")
            result["inscription_type"] = insc.get("type", "")
            result["site"] = insc.get("site", "")
            results.append(result)
        return results

    def _get_base(self, parsed_token: dict) -> str:
        """Extract the root/base form from a parsed token."""
        morphemes = parsed_token.get("morphemes", [])
        for m in morphemes:
            if m.get("type") == "root":
                return m["segment"]
        # Fall back to first morpheme segment or token
        if morphemes:
            return morphemes[0].get("segment", "")
        return parsed_token.get("token", "")

    def _build_interlinear(self, parsed_tokens: list[dict]) -> list[dict]:
        """Build an interlinear gloss from parsed tokens."""
        rows = []
        for p in parsed_tokens:
            base = self._get_base(p)
            base_lower = base.lower()

            # Look up meaning in lexicon
            entry = (self.lexicon.get(base_lower) or
                     self.lexicon.get(base) or {})
            translation = entry.get("translation", "?")
            certainty = entry.get("certainty", 0.0)

            # Build morpheme gloss string
            morpheme_glosses = []
            for morph in p.get("morphemes", []):
                mg = morph.get("meaning") or morph.get("function") or morph.get("segment", "")
                morpheme_glosses.append(mg)

            rows.append({
                "token": p.get("token", base),
                "base": base,
                "pos": p.get("pos", "UNK"),
                "translation": translation,
                "certainty": certainty,
                "morpheme_analysis": "-".join(morpheme_glosses) if morpheme_glosses else base,
            })

        return rows

    def _render_free_translation(self, parsed, phrases, template_result,
                                 inscription) -> str:
        """Render a best-effort free English translation."""
        parts = []

        # Use template-based translation if we have a strong match
        best_template = template_result.get("best_match")
        template_score = template_result.get("best_score", 0)

        if best_template and template_score > 0.4:
            parts.append(self._template_based_translation(
                parsed, best_template, inscription
            ))
        else:
            parts.append(self._sequential_translation(parsed, phrases))

        return " ".join(parts).strip()

    def _template_based_translation(self, parsed, template_name: str,
                                    inscription: dict) -> str:
        """Generate translation using a known template structure."""
        # Extract names from parsed tokens
        names = [self._get_base(p) for p in parsed if p.get("pos") == "NOUN.PROPER"]
        name_str = " ".join(names) if names else "[PN]"

        if template_name == "funerary_offering":
            return (
                f"An offering which the king gives "
                f"(for) {name_str}: "
                f"bread, water, and all good things."
            )

        if template_name == "royal_enthronement":
            deity_parts = [self._get_base(p) for p in parsed
                          if self.vocabulary.get(self._get_base(p).lower(), {}).get("category") == "deity_name"]
            deity_str = " and ".join(deity_parts) if deity_parts else "Amun"
            return (
                f"By the grace of {deity_str}, "
                f"King {name_str}, great and good, "
                f"ruler of the western land and Akine."
            )

        if template_name == "temple_dedication":
            deity_parts = [self._get_base(p) for p in parsed
                          if self.vocabulary.get(self._get_base(p).lower(), {}).get("category") == "deity_name"]
            deity_str = " and ".join(deity_parts) if deity_parts else "the god"
            return (
                f"This temple is dedicated to {deity_str} "
                f"by {name_str}, "
                f"for the protection and prosperity of the land."
            )

        if template_name == "genealogical":
            return (
                f"{name_str}, "
                f"born of [mother], begotten of [father], "
                f"of the royal house."
            )

        return self._sequential_translation(parsed, [])

    def _sequential_translation(self, parsed, phrases) -> str:
        """Translate word-by-word and stitch into English."""
        words = []
        for p in parsed:
            base = self._get_base(p).lower()
            entry = self.lexicon.get(base) or self.lexicon.get(self._get_base(p)) or {}
            translation = entry.get("translation", "")

            if not translation or translation == "?":
                words.append(f"[{self._get_base(p)}]")
            elif translation.startswith("["):
                words.append(translation)
            else:
                words.append(translation)

        return " ".join(words)

    def _compute_confidence(self, parsed, template_result) -> dict:
        """Compute translation confidence metrics."""
        total = len(parsed)
        if total == 0:
            return {"overall": 0.0, "breakdown": {}}

        known_count = 0
        certainty_sum = 0.0

        for p in parsed:
            base = self._get_base(p).lower()
            entry = self.lexicon.get(base) or {}
            cert = entry.get("certainty", 0.0)
            certainty_sum += cert
            if cert >= 0.3:
                known_count += 1

        lexical_coverage = known_count / total
        avg_certainty = certainty_sum / total

        template_score = template_result.get("best_score", 0)
        template_bonus = template_score * 0.2

        overall = (lexical_coverage * 0.4 +
                   avg_certainty * 0.4 +
                   template_bonus)
        overall = min(1.0, overall)

        return {
            "overall": round(overall, 3),
            "lexical_coverage": round(lexical_coverage, 3),
            "average_certainty": round(avg_certainty, 3),
            "template_match_score": round(template_score, 3),
            "known_tokens": known_count,
            "total_tokens": total,
            "grade": (
                "A" if overall >= 0.7 else
                "B" if overall >= 0.5 else
                "C" if overall >= 0.3 else
                "D"
            ),
        }


def create_translation_pipeline(vocabulary, morphemes, comparative_data,
                                corpus, syntactic_rules):
    """Factory function for TranslationPipeline."""
    return TranslationPipeline(
        vocabulary, morphemes, comparative_data, corpus, syntactic_rules
    )
