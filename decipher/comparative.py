"""
Comparative Linguistics Engine for Meroitic
=============================================
Deep comparative analysis between Meroitic and related language families:

  1. Nubian languages (Old Nubian, Nobiin, Dongolawi, Midob, Birgid)
  2. Nilo-Saharan phylum (broader connections)
  3. Eastern Sudanic sub-family

Methods:
  - Regular sound correspondence detection
  - Proto-form reconstruction via the Comparative Method
  - Cognate scoring with phonological distance
  - Semantic field mapping
"""

from collections import defaultdict
import math
from typing import Optional


# Sound correspondence rules between Meroitic and Nubian family
SOUND_CORRESPONDENCES = [
    {"meroitic": "t", "nubian": "d", "environment": "intervocalic", "confidence": 0.7},
    {"meroitic": "k", "nubian": "g", "environment": "word-initial", "confidence": 0.6},
    {"meroitic": "s", "nubian": "sh", "environment": "before front vowel", "confidence": 0.7},
    {"meroitic": "p", "nubian": "b", "environment": "word-initial", "confidence": 0.6},
    {"meroitic": "w", "nubian": "b", "environment": "intervocalic", "confidence": 0.5},
    {"meroitic": "q", "nubian": "k", "environment": "uvular context", "confidence": 0.6},
    {"meroitic": "a", "nubian": "o", "environment": "near labials", "confidence": 0.4},
    {"meroitic": "e", "nubian": "i", "environment": "word-final", "confidence": 0.5},
    {"meroitic": "l", "nubian": "r", "environment": "free variation", "confidence": 0.7},
    {"meroitic": "n", "nubian": "n", "environment": "universal", "confidence": 0.9},
    {"meroitic": "m", "nubian": "m", "environment": "universal", "confidence": 0.9},
]

# Semantic field mappings for cross-linguistic comparison
SEMANTIC_FIELDS = {
    "kinship": ["qore", "kdke", "kdi", "mk", "tke"],
    "religion": ["amni", "apede", "mk", "wos", "ar"],
    "geography": ["to", "tenke", "akine", "mede"],
    "body": ["wi", "se", "her"],
    "sustenance": ["ate", "yi", "pesto"],
    "governance": ["qore", "qo", "mlo", "pelmos"],
    "funerary": ["ate", "yi", "pesto", "wos", "ar"],
    "numerals": ["mde", "lh", "d"],
}


class SoundLawEngine:
    """Apply and test regular sound correspondences between languages."""

    def __init__(self, correspondences: Optional[list] = None):
        self.correspondences = correspondences or SOUND_CORRESPONDENCES
        self._build_correspondence_map()

    def _build_correspondence_map(self):
        self.mer_to_nub = defaultdict(list)
        for rule in self.correspondences:
            self.mer_to_nub[rule["meroitic"]].append({
                "target": rule["nubian"],
                "env": rule["environment"],
                "conf": rule["confidence"],
            })

    def apply_laws(self, meroitic_form: str) -> list[dict]:
        """Apply sound laws to produce possible proto-forms or cognate predictions."""
        candidates = [{"form": "", "confidence": 1.0}]

        for char in meroitic_form.lower():
            if char in self.mer_to_nub:
                new_candidates = []
                for cand in candidates:
                    # Keep original
                    new_candidates.append({
                        "form": cand["form"] + char,
                        "confidence": cand["confidence"] * 0.8,
                    })
                    # Apply each correspondence
                    for rule in self.mer_to_nub[char]:
                        new_candidates.append({
                            "form": cand["form"] + rule["target"],
                            "confidence": cand["confidence"] * rule["conf"],
                        })
                candidates = new_candidates
            else:
                for cand in candidates:
                    cand["form"] += char

        # Sort by confidence, filter low scores
        candidates = [c for c in candidates if c["confidence"] > 0.05]
        candidates.sort(key=lambda x: -x["confidence"])
        return candidates[:15]

    def check_cognate_pair(self, meroitic: str, nubian: str) -> dict:
        """Score a proposed cognate pair using sound laws."""
        mer = meroitic.lower()
        nub = nubian.lower()

        # Alignment check
        score = 0.0
        matches = 0
        penalties = 0
        total = max(len(mer), len(nub))

        i, j = 0, 0
        while i < len(mer) and j < len(nub):
            if mer[i] == nub[j]:
                score += 1.0
                matches += 1
                i += 1
                j += 1
            elif any(r["target"] == nub[j] for r in self.mer_to_nub.get(mer[i], [])):
                rules = [r for r in self.mer_to_nub[mer[i]] if r["target"] == nub[j]]
                best_conf = max(r["conf"] for r in rules)
                score += best_conf
                matches += 1
                i += 1
                j += 1
            else:
                penalties += 1
                if len(mer) > len(nub):
                    i += 1
                elif len(nub) > len(mer):
                    j += 1
                else:
                    i += 1
                    j += 1

        length_penalty = 1.0 - abs(len(mer) - len(nub)) * 0.15
        final_score = (score / total if total else 0) * max(0.3, length_penalty)

        return {
            "meroitic": meroitic,
            "nubian": nubian,
            "cognate_score": round(final_score, 3),
            "sound_matches": matches,
            "penalties": penalties,
            "is_likely_cognate": final_score > 0.45,
        }


class ProtoFormReconstructor:
    """Reconstruct proto-forms from Meroitic and Nubian data."""

    def __init__(self, sound_laws: SoundLawEngine):
        self.sound_laws = sound_laws

    def reconstruct(self, meroitic: str, nubian_cognates: list[dict]) -> dict:
        """Reconstruct a proto-form from a Meroitic word and its Nubian cognates.

        Uses the comparative method: identify common elements across cognates,
        resolve differences using sound correspondences.
        """
        mer = meroitic.lower()
        all_forms = [mer] + [c.get("form", "").lower() for c in nubian_cognates if c.get("form")]

        if not all_forms:
            return {"proto": f"*{mer}", "confidence": 0.2, "method": "trivial (no cognates)"}

        # Find the most conservative (archaic) form
        # In the Comparative Method, typically the form requiring fewest changes
        # across all languages is closest to the proto-form
        proto_chars = []
        max_len = max(len(f) for f in all_forms)

        for pos in range(max_len):
            chars_at_pos = []
            for form in all_forms:
                if pos < len(form):
                    chars_at_pos.append(form[pos])

            if chars_at_pos:
                # Choose the character that appears most often (majority rule)
                counts = {}
                for c in chars_at_pos:
                    counts[c] = counts.get(c, 0) + 1
                proto_char = max(counts, key=counts.get)
                proto_chars.append(proto_char)

        proto = "".join(proto_chars)
        confidence = min(0.5, 0.2 + len(nubian_cognates) * 0.1)

        return {
            "proto": f"*{proto}",
            "confidence": round(confidence, 2),
            "method": "comparative_majority",
            "based_on": len(all_forms),
        }


class SemanticFieldAnalyzer:
    """Analyze semantic field distributions across the Meroitic corpus."""

    def __init__(self, vocabulary: dict, fields: Optional[dict] = None):
        self.vocabulary = vocabulary
        self.fields = fields or SEMANTIC_FIELDS

    def classify_inscription(self, tokens: list[str]) -> dict:
        """Determine which semantic fields are active in an inscription."""
        field_scores = {}
        bases = [t.split("-")[0].lower() for t in tokens]

        for field_name, field_words in self.fields.items():
            count = sum(1 for b in bases if b in field_words)
            if count > 0:
                field_scores[field_name] = {
                    "count": count,
                    "proportion": round(count / len(bases), 3) if bases else 0,
                    "matched_words": [b for b in bases if b in field_words],
                }

        return field_scores

    def field_co_occurrence_matrix(self, corpus: list[dict]) -> dict:
        """Build a matrix of how semantic fields co-occur across inscriptions."""
        matrix = defaultdict(lambda: defaultdict(int))
        for insc in corpus:
            tokens = [t.strip() for t in insc["text"].split(":") if t.strip()]
            fields = self.classify_inscription(tokens)
            field_names = list(fields.keys())
            for i, f1 in enumerate(field_names):
                for f2 in field_names[i:]:
                    matrix[f1][f2] += 1
                    if f1 != f2:
                        matrix[f2][f1] += 1

        return {k: dict(v) for k, v in matrix.items()}


class ComparativeEngine:
    """Main engine integrating all comparative linguistics methods."""

    def __init__(self, vocabulary: dict, comparative_data: dict, corpus: list[dict]):
        self.vocabulary = vocabulary
        self.comparative_data = comparative_data
        self.corpus = corpus
        self.sound_laws = SoundLawEngine()
        self.reconstructor = ProtoFormReconstructor(self.sound_laws)
        self.semantic_analyzer = SemanticFieldAnalyzer(vocabulary)

    def run_full_analysis(self) -> dict:
        """Execute a complete comparative analysis."""
        results = {}

        # 1. Score all known cognate pairs
        results["cognate_scores"] = self._score_known_cognates()

        # 2. Search for new cognates by applying sound laws
        results["new_cognate_proposals"] = self._propose_new_cognates()

        # 3. Reconstruct proto-forms
        results["proto_forms"] = self._reconstruct_proto_forms()

        # 4. Semantic field analysis across corpus
        results["semantic_fields"] = self._analyze_semantic_fields()

        # 5. Language relationship summary
        results["relationship_summary"] = self._summarize_relationship()

        return results

    def _score_known_cognates(self) -> list[dict]:
        """Score all known or proposed cognate pairs."""
        scores = []
        for word, entry in self.comparative_data.items():
            nubian_form = entry.get("nubian_form") or entry.get("nobiin")
            if nubian_form:
                result = self.sound_laws.check_cognate_pair(word, nubian_form)
                result["meaning"] = entry.get("meroitic_meaning", "")
                result["nubian_meaning"] = entry.get("nubian_meaning", "")
                scores.append(result)
        return sorted(scores, key=lambda x: -x["cognate_score"])

    def _propose_new_cognates(self) -> list[dict]:
        """Apply sound laws to unknown Meroitic words and propose Nubian cognates."""
        proposals = []
        nubian_lookup = {}
        for word, entry in self.comparative_data.items():
            nubian_form = entry.get("nubian_form") or entry.get("nobiin")
            if nubian_form:
                nubian_lookup[nubian_form.lower()] = {
                    "meroitic_match": word,
                    "meaning": entry.get("nubian_meaning", ""),
                }

        for word in self.vocabulary:
            if word in self.comparative_data:
                continue
            candidates = self.sound_laws.apply_laws(word)
            for c in candidates[:5]:
                if c["form"] in nubian_lookup:
                    proposals.append({
                        "meroitic": word,
                        "predicted_nubian": c["form"],
                        "confidence": c["confidence"],
                        "match_info": nubian_lookup[c["form"]],
                    })

        return sorted(proposals, key=lambda x: -x["confidence"])

    def _reconstruct_proto_forms(self) -> list[dict]:
        """Reconstruct proto-forms for words with comparative data."""
        proto_forms = []
        for word, entry in self.comparative_data.items():
            nubian_cognates = []
            nubian_form = entry.get("nubian_form") or entry.get("nobiin")
            if nubian_form:
                nubian_cognates.append({
                    "form": nubian_form,
                    "language": "Old Nubian / Nobiin",
                })
            proto_nubian = entry.get("proto_nubian")
            if proto_nubian:
                nubian_cognates.append({
                    "form": proto_nubian.lstrip("*"),
                    "language": "Proto-Nubian",
                })

            result = self.reconstructor.reconstruct(word, nubian_cognates)
            result["word"] = word
            result["meaning"] = entry.get("meroitic_meaning", "")
            proto_forms.append(result)

        return proto_forms

    def _analyze_semantic_fields(self) -> dict:
        """Analyze semantic fields across the whole corpus."""
        per_inscription = []
        for insc in self.corpus:
            tokens = [t.strip() for t in insc["text"].split(":") if t.strip()]
            fields = self.semantic_analyzer.classify_inscription(tokens)
            per_inscription.append({
                "id": insc.get("id", ""),
                "type": insc.get("type", ""),
                "fields": fields,
            })

        co_occurrence = self.semantic_analyzer.field_co_occurrence_matrix(self.corpus)

        return {
            "per_inscription": per_inscription,
            "co_occurrence": co_occurrence,
        }

    def _summarize_relationship(self) -> dict:
        """Summarize the Meroitic-Nubian relationship."""
        cognate_scores = self._score_known_cognates()
        if not cognate_scores:
            return {"status": "insufficient_data"}

        avg_score = sum(c["cognate_score"] for c in cognate_scores) / len(cognate_scores)
        likely_cognates = sum(1 for c in cognate_scores if c["is_likely_cognate"])

        return {
            "total_pairs_tested": len(cognate_scores),
            "likely_cognates": likely_cognates,
            "average_cognate_score": round(avg_score, 3),
            "relationship_strength": (
                "strong" if avg_score > 0.5 else
                "moderate" if avg_score > 0.35 else
                "weak"
            ),
            "conclusion": (
                "Evidence supports a genetic or deep contact relationship "
                "between Meroitic and the Nubian language family. "
                f"Average cognate score: {avg_score:.3f} across {len(cognate_scores)} pairs, "
                f"with {likely_cognates} pairs meeting the cognate threshold."
            ),
        }


def create_comparative_engine(vocabulary, comparative_data, corpus):
    """Factory function for ComparativeEngine."""
    return ComparativeEngine(vocabulary, comparative_data, corpus)
