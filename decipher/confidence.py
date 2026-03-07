"""
Decipherment Confidence Scorer
=================================
Multi-dimensional scoring system that evaluates translation quality
and identifies which parts of the decipherment are most/least reliable.

Dimensions:
  1. Lexical coverage  — what fraction of tokens have known meanings
  2. Morphological regularity — do morphological patterns follow known rules
  3. Template conformity — does the text match a known formula/template
  4. Comparative support — are translations corroborated by Nubian/E. Sudanic data
  5. Internal consistency — do repeated words get consistent translations
  6. Contextual plausibility — does the meaning fit the inscription type / site
"""

from collections import Counter, defaultdict
import math
from typing import Optional


class ConfidenceScorer:
    """Comprehensive scoring of Meroitic translation quality."""

    WEIGHTS = {
        "lexical": 0.25,
        "morphological": 0.15,
        "template": 0.15,
        "comparative": 0.15,
        "consistency": 0.15,
        "plausibility": 0.15,
    }

    def __init__(self, vocabulary: dict, morphemes: dict,
                 comparative_data: dict, syntactic_rules: dict):
        self.vocabulary = vocabulary
        self.morphemes = morphemes
        self.comparative = comparative_data
        self.syntactic_rules = syntactic_rules

    def score_translation(self, translation_result: dict, inscription: dict) -> dict:
        """Score a single translation result across all dimensions."""
        interlinear = translation_result.get("interlinear", [])
        template = translation_result.get("template", {})
        text = inscription.get("text", "")
        itype = inscription.get("type", "")

        d1 = self._lexical_score(interlinear)
        d2 = self._morphological_score(interlinear)
        d3 = self._template_score(template)
        d4 = self._comparative_score(interlinear)
        d5 = self._consistency_score(interlinear)
        d6 = self._plausibility_score(interlinear, itype)

        overall = (
            d1["score"] * self.WEIGHTS["lexical"] +
            d2["score"] * self.WEIGHTS["morphological"] +
            d3["score"] * self.WEIGHTS["template"] +
            d4["score"] * self.WEIGHTS["comparative"] +
            d5["score"] * self.WEIGHTS["consistency"] +
            d6["score"] * self.WEIGHTS["plausibility"]
        )

        dim_scores = {
            "lexical": d1["score"],
            "morphological": d2["score"],
            "template": d3["score"],
            "comparative": d4["score"],
            "consistency": d5["score"],
            "plausibility": d6["score"],
        }

        return {
            "overall": round(overall, 3),
            "grade": self._grade(overall),
            "dimensions": {
                "lexical": d1,
                "morphological": d2,
                "template": d3,
                "comparative": d4,
                "consistency": d5,
                "plausibility": d6,
            },
            "per_token_confidence": self._per_token_confidence(interlinear),
            "weakest_dimension": min(dim_scores, key=dim_scores.get),
        }

    def score_corpus(self, translations: list[dict], corpus: list[dict]) -> dict:
        """Score an entire translated corpus and produce summary statistics."""
        scores = []
        grade_dist = Counter()

        corpus_lookup = {insc.get("id", i): insc for i, insc in enumerate(corpus)}

        for t in translations:
            insc_id = t.get("inscription_id", "")
            insc = corpus_lookup.get(insc_id, {})
            s = self.score_translation(t, insc)
            s["inscription_id"] = insc_id
            scores.append(s)
            grade_dist[s["grade"]] += 1

        overall_scores = [s["overall"] for s in scores]
        avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0

        # Dimension averages
        dim_avgs = {}
        dim_names = ["lexical", "morphological", "template",
                     "comparative", "consistency", "plausibility"]
        for dim in dim_names:
            vals = [s["dimensions"][dim]["score"] for s in scores]
            dim_avgs[dim] = round(sum(vals) / len(vals), 3) if vals else 0

        return {
            "total_inscriptions": len(scores),
            "average_score": round(avg, 3),
            "grade_distribution": dict(grade_dist),
            "dimension_averages": dim_avgs,
            "weakest_overall_dimension": min(dim_avgs, key=dim_avgs.get) if dim_avgs else None,
            "strongest_overall_dimension": max(dim_avgs, key=dim_avgs.get) if dim_avgs else None,
            "per_inscription": scores,
        }

    def _lexical_score(self, interlinear: list[dict]) -> dict:
        """Score based on how many tokens have known translations."""
        if not interlinear:
            return {"score": 0, "detail": "no tokens"}

        known = sum(1 for row in interlinear
                    if row.get("certainty", 0) > 0)
        high_confidence = sum(1 for row in interlinear
                             if row.get("certainty", 0) >= 0.6)
        total = len(interlinear)

        coverage = known / total
        quality = high_confidence / total

        score = coverage * 0.6 + quality * 0.4
        return {
            "score": round(score, 3),
            "known_tokens": known,
            "high_confidence_tokens": high_confidence,
            "total_tokens": total,
        }

    def _morphological_score(self, interlinear: list[dict]) -> dict:
        """Score based on morphological parse success."""
        if not interlinear:
            return {"score": 0, "detail": "no tokens"}

        parsed_count = 0
        for row in interlinear:
            analysis = row.get("morpheme_analysis", "")
            if analysis and "-" in analysis:
                parsed_count += 1

        score = parsed_count / len(interlinear)
        return {
            "score": round(score, 3),
            "parsed_tokens": parsed_count,
            "total_tokens": len(interlinear),
        }

    def _template_score(self, template_result: dict) -> dict:
        """Score based on template matching strength."""
        best_score = template_result.get("best_score", 0)
        best_match = template_result.get("best_match", "")
        # Normalize: template raw scores can be high; sigmoid-like cap at 1.0
        normalized = min(1.0, best_score / 10.0) if best_score > 0 else 0
        return {
            "score": round(normalized, 3),
            "matched_template": best_match,
        }

    def _comparative_score(self, interlinear: list[dict]) -> dict:
        """Score based on comparative support from Nubian data."""
        if not interlinear:
            return {"score": 0, "detail": "no tokens"}

        supported = 0
        for row in interlinear:
            base = row.get("base", "").lower()
            if base in self.comparative:
                supported += 1

        score = min(1.0, supported / len(interlinear) * 3)  # boost: even a few is good
        return {
            "score": round(score, 3),
            "supported_tokens": supported,
            "total_tokens": len(interlinear),
        }

    def _consistency_score(self, interlinear: list[dict]) -> dict:
        """Score based on whether the same base word always gets the same translation."""
        if not interlinear:
            return {"score": 0, "detail": "no tokens"}

        translations_per_base = defaultdict(set)
        for row in interlinear:
            base = row.get("base", "").lower()
            trans = row.get("translation", "?")
            if trans and trans != "?":
                translations_per_base[base].add(trans)

        if not translations_per_base:
            return {"score": 0.5, "detail": "no translations to check"}

        consistent = sum(1 for t in translations_per_base.values() if len(t) == 1)
        total = len(translations_per_base)
        score = consistent / total if total else 0.5

        return {
            "score": round(score, 3),
            "consistent_words": consistent,
            "total_unique_words": total,
        }

    def _plausibility_score(self, interlinear: list[dict], itype: str) -> dict:
        """Score contextual plausibility of the translation."""
        if not interlinear:
            return {"score": 0, "detail": "no tokens"}

        # Check if translated semantic content matches the expected inscription type
        expected_categories = {
            "funerary": {"sustenance", "funerary", "religion", "kinship"},
            "royal": {"governance", "religion", "geography"},
            "religious": {"religion", "sustenance"},
            "administrative": {"governance", "geography"},
        }

        expected = expected_categories.get(itype, set())
        if not expected:
            return {"score": 0.5, "detail": "unknown inscription type"}

        found_categories = set()
        for row in interlinear:
            base = row.get("base", "").lower()
            entry = self.vocabulary.get(base, {})
            cat = entry.get("category", "")
            if cat:
                found_categories.add(cat)

        if not found_categories:
            return {"score": 0.3, "detail": "no categorized tokens"}

        overlap = found_categories & expected
        score = len(overlap) / len(expected) if expected else 0.5

        return {
            "score": round(min(1.0, score), 3),
            "expected_categories": sorted(expected),
            "found_categories": sorted(found_categories),
            "overlap": sorted(overlap),
        }

    def _per_token_confidence(self, interlinear: list[dict]) -> list[dict]:
        """Return per-token confidence for visualization."""
        return [
            {
                "token": row.get("token", ""),
                "confidence": row.get("certainty", 0.0),
                "grade": self._grade(row.get("certainty", 0.0)),
            }
            for row in interlinear
        ]

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 0.7:
            return "A"
        if score >= 0.5:
            return "B"
        if score >= 0.3:
            return "C"
        return "D"


def create_confidence_scorer(vocabulary, morphemes, comparative_data, syntactic_rules):
    """Factory function for ConfidenceScorer."""
    return ConfidenceScorer(vocabulary, morphemes, comparative_data, syntactic_rules)
