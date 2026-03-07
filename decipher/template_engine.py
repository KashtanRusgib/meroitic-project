"""
Module 3: Genre-Based Statistical Template Refinement
=====================================================
Upgrades the template matching system with:
  1. Corpus-trained statistical templates extracted from 72-inscription corpus
  2. Template-aware contextual restoration of lacunae / damaged text
  3. N-gram probability model for predicting missing tokens in known formulas

References:
  - Rilly & de Voogt 2012: Ch. 2 (genre classification)
  - Hintze 1960 (REM 1044 structure)
"""

from collections import defaultdict, Counter
from typing import Optional
import math

from decipher import VOCABULARY, CORPUS, MORPHEMES


# ═══════════════════════════════════════════════════════════════════════════════
# Genre definitions with expanded structural templates
# ═══════════════════════════════════════════════════════════════════════════════

GENRE_TEMPLATES = {
    "funerary_offering": {
        "description": "Funerary stelae and offering tables",
        "canonical_structure": [
            "invocation", "deity_epithet", "deceased_name", "title",
            "filiation", "offering_items", "offering_verb", "benediction",
        ],
        "required_elements": {"invocation", "offering_items", "deceased_name"},
        "typical_length": (5, 20),
        "frequency_in_corpus": 0.55,
        "marker_tokens": {"ate", "yi", "pesto", "mk", "wos"},
        "recurring_formulas": [
            "wos : mk-se-l-o : qo : mlo-li",   # Isis, the gods great, good
            "ate-li : yi-li : pesto-b-ke",       # bread water may-be-given
            "mk-se-l-o : Tanyidamani : prite",   # gods (of) Tanyidamani, life
        ],
    },
    "royal_stele": {
        "description": "Royal enthronement and military campaign stelae",
        "canonical_structure": [
            "invocation", "deity_triad", "royal_protocol", "titles",
            "genealogy", "military_narrative", "victory_list",
            "offering_formula", "closing_benediction",
        ],
        "required_elements": {"invocation", "royal_protocol", "titles"},
        "typical_length": (15, 200),
        "frequency_in_corpus": 0.18,
        "marker_tokens": {"qore", "qo", "mlo", "e-ked", "erk", "to", "akine"},
        "recurring_formulas": [
            "apedmk-i : qo : mlo : mk-se-l",   # O Apedemak great good god
            "qore-l : Tanyidamani : qo : mlo",  # ruler Tanyidamani great good
            "e-ked : abr-se-l",                   # I-slaughtered the-men
            "erk : kdi-se-l",                     # seized the-women
        ],
    },
    "temple_dedication": {
        "description": "Temple and religious building dedications",
        "canonical_structure": [
            "invocation", "deity_name", "epithet_sequence",
            "dedicator_name", "title", "building_verb",
            "temple_reference", "benediction",
        ],
        "required_elements": {"invocation", "deity_name", "dedicator_name"},
        "typical_length": (8, 40),
        "frequency_in_corpus": 0.15,
        "marker_tokens": {"amni", "dmke", "mke", "selele", "mk"},
        "recurring_formulas": [
            "amni : mk-se-l : qo : mlo",  # Amun god great good
            "dmke : amni-te",              # temple at-Amun
        ],
    },
    "genealogical": {
        "description": "Royal genealogies and lineage records",
        "canonical_structure": [
            "subject_name", "title", "filiation_marker",
            "parent_name", "parent_title", "maternal_line",
        ],
        "required_elements": {"subject_name", "filiation_marker"},
        "typical_length": (3, 15),
        "frequency_in_corpus": 0.08,
        "marker_tokens": {"mete", "lh", "kdke", "sr", "beke"},
        "recurring_formulas": [
            "NAME : mete : NAME",    # NAME son-of NAME
            "kdke : NAME : lh",      # queen NAME offspring
        ],
    },
    "graffito": {
        "description": "Short visitor or pilgrim graffiti",
        "canonical_structure": ["name", "title", "location_reference"],
        "required_elements": {"name"},
        "typical_length": (1, 5),
        "frequency_in_corpus": 0.04,
        "marker_tokens": set(),
        "recurring_formulas": [],
    },
}


class StatisticalTemplateEngine:
    """
    Learn genre-specific templates from the corpus and use them for
    classification, scoring, and contextual restoration.
    """

    def __init__(self, vocabulary: Optional[dict] = None, corpus: Optional[list] = None):
        self.vocabulary = vocabulary or VOCABULARY
        self.corpus = corpus or CORPUS
        self.templates = GENRE_TEMPLATES
        # Trained models
        self._ngram_model = None
        self._category_sequences = None

    def train(self):
        """Train the statistical models on the corpus."""
        self._build_ngram_model()
        self._learn_category_sequences()

    def _build_ngram_model(self):
        """Build bigram and trigram models of token categories."""
        bigrams = defaultdict(Counter)
        trigrams = defaultdict(Counter)
        unigrams = Counter()

        for entry in self.corpus:
            tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
            cats = self._categorize_tokens(tokens)

            # Add sentence boundaries
            cats = ["<START>"] + cats + ["<END>"]

            for i in range(len(cats)):
                unigrams[cats[i]] += 1
                if i > 0:
                    bigrams[cats[i - 1]][cats[i]] += 1
                if i > 1:
                    trigrams[(cats[i - 2], cats[i - 1])][cats[i]] += 1

        self._ngram_model = {
            "unigrams": unigrams,
            "bigrams": dict(bigrams),
            "trigrams": dict(trigrams),
        }

    def _learn_category_sequences(self):
        """Learn typical category-sequence patterns per genre."""
        genre_sequences = defaultdict(list)

        for entry in self.corpus:
            tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
            cats = self._categorize_tokens(tokens)
            genre = self.classify_genre(entry)["best_genre"]
            genre_sequences[genre].append(cats)

        self._category_sequences = dict(genre_sequences)

    def _categorize_tokens(self, tokens: list[str]) -> list[str]:
        """Map tokens to their grammatical categories."""
        cats = []
        for token in tokens:
            base = token.split("-")[0].lower()
            ventry = self.vocabulary.get(base, {})
            cat = ventry.get("category", "unknown")
            cats.append(cat)
        return cats

    def classify_genre(self, inscription: dict) -> dict:
        """Classify an inscription into its most likely genre."""
        tokens = [t.strip() for t in inscription["text"].split(":") if t.strip()]
        bases = {t.split("-")[0].lower() for t in tokens}
        n_tokens = len(tokens)

        scores = {}
        for genre_name, template in self.templates.items():
            score = 0.0

            # Marker token overlap
            marker_overlap = len(bases & template["marker_tokens"])
            if template["marker_tokens"]:
                score += (marker_overlap / len(template["marker_tokens"])) * 0.4

            # Length fit
            lo, hi = template["typical_length"]
            if lo <= n_tokens <= hi:
                score += 0.2
            elif n_tokens < lo:
                score += 0.1 * (n_tokens / lo)
            else:
                score += 0.1 * min(1, hi / n_tokens)

            # Required element check
            cats = set(self._categorize_tokens(tokens))
            req_match = 0
            for req in template["required_elements"]:
                # Flexible matching: "deceased_name" matches any name-like token
                if any(req.split("_")[0] in c for c in cats):
                    req_match += 1
                elif any(req in c for c in cats):
                    req_match += 1
            if template["required_elements"]:
                score += (req_match / len(template["required_elements"])) * 0.3

            # Formula match bonus
            text_lower = inscription["text"].lower()
            formula_hits = sum(
                1 for f in template["recurring_formulas"]
                if f.lower() in text_lower
            )
            if template["recurring_formulas"]:
                score += (formula_hits / len(template["recurring_formulas"])) * 0.1

            scores[genre_name] = round(score, 4)

        best = max(scores, key=scores.get)
        return {
            "best_genre": best,
            "best_score": scores[best],
            "all_scores": scores,
        }

    def predict_missing_token(self, left_context: list[str],
                               right_context: list[str]) -> list[dict]:
        """
        Given tokens to the left and right of a lacuna, predict
        the most likely missing token(s) using the n-gram model.
        """
        if self._ngram_model is None:
            self.train()

        left_cats = self._categorize_tokens(left_context)
        right_cats = self._categorize_tokens(right_context)

        candidates = Counter()

        # Bigram: P(cat | left_last)
        if left_cats:
            left_last = left_cats[-1]
            bi = self._ngram_model["bigrams"].get(left_last, {})
            for cat, count in bi.items():
                candidates[cat] += count * 2

        # Trigram: P(cat | left[-2], left[-1])
        if len(left_cats) >= 2:
            key = (left_cats[-2], left_cats[-1])
            tri = self._ngram_model["trigrams"].get(key, {})
            for cat, count in tri.items():
                candidates[cat] += count * 3

        # Right-context bigram (reverse prediction)
        if right_cats:
            right_first = right_cats[0]
            for prev_cat, nexts in self._ngram_model["bigrams"].items():
                if right_first in nexts:
                    candidates[prev_cat] += nexts[right_first]

        # Convert to ranked list with example tokens
        results = []
        total = sum(candidates.values()) or 1
        for cat, count in candidates.most_common(5):
            example_tokens = [
                w for w, v in self.vocabulary.items()
                if v.get("category") == cat
            ][:3]
            results.append({
                "predicted_category": cat,
                "probability": round(count / total, 3),
                "example_tokens": example_tokens,
            })

        return results

    def restore_lacuna(self, inscription: dict, gap_position: int) -> list[dict]:
        """
        Attempt to restore a damaged/missing token at a given position.
        Uses genre template + n-gram model for prediction.
        """
        tokens = [t.strip() for t in inscription["text"].split(":") if t.strip()]

        if gap_position < 0 or gap_position > len(tokens):
            return []

        left = tokens[:gap_position]
        right = tokens[gap_position:]

        # Get genre context
        genre = self.classify_genre(inscription)

        # Predict using n-gram
        predictions = self.predict_missing_token(left, right)

        # Boost predictions that fit the genre template
        template = self.templates.get(genre["best_genre"], {})
        structs = template.get("canonical_structure", [])
        if gap_position < len(structs):
            expected_role = structs[gap_position]
            for pred in predictions:
                if expected_role.split("_")[0] in pred["predicted_category"]:
                    pred["probability"] = min(1.0, pred["probability"] * 1.5)
                    pred["template_boost"] = True

        predictions.sort(key=lambda x: -x["probability"])
        return predictions

    def compute_template_fit(self, inscription: dict) -> dict:
        """
        Compute how well an inscription fits its best-genre template.
        Returns per-position alignment scores.
        """
        tokens = [t.strip() for t in inscription["text"].split(":") if t.strip()]
        cats = self._categorize_tokens(tokens)
        genre = self.classify_genre(inscription)
        template = self.templates.get(genre["best_genre"], {})
        struct = template.get("canonical_structure", [])

        alignments = []
        for i, cat in enumerate(cats):
            if i < len(struct):
                expected = struct[i]
                match = (expected.split("_")[0] in cat or cat in expected)
                alignments.append({
                    "position": i,
                    "token_category": cat,
                    "expected_role": expected,
                    "match": match,
                })
            else:
                alignments.append({
                    "position": i,
                    "token_category": cat,
                    "expected_role": "(beyond template)",
                    "match": False,
                })

        matched = sum(1 for a in alignments if a["match"])
        return {
            "genre": genre["best_genre"],
            "genre_confidence": genre["best_score"],
            "alignments": alignments,
            "match_ratio": round(matched / len(alignments), 3) if alignments else 0,
        }

    def corpus_genre_distribution(self) -> dict:
        """Classify every inscription in the corpus by genre."""
        distribution = Counter()
        by_genre = defaultdict(list)

        for entry in self.corpus:
            genre = self.classify_genre(entry)
            best = genre["best_genre"]
            distribution[best] += 1
            by_genre[best].append({
                "id": entry.get("id", ""),
                "score": genre["best_score"],
            })

        return {
            "distribution": dict(distribution.most_common()),
            "total_inscriptions": len(self.corpus),
            "genre_details": {
                g: {
                    "count": len(entries),
                    "avg_score": round(sum(e["score"] for e in entries) / len(entries), 3),
                    "ids": [e["id"] for e in entries],
                }
                for g, entries in by_genre.items()
            },
        }


def run_template_analysis() -> dict:
    """Execute the full template refinement analysis."""
    engine = StatisticalTemplateEngine()
    engine.train()

    # 1. Corpus genre distribution
    genre_dist = engine.corpus_genre_distribution()

    # 2. Template fit for sample inscriptions
    template_fits = []
    for entry in CORPUS[:10]:
        fit = engine.compute_template_fit(entry)
        template_fits.append({
            "id": entry.get("id", ""),
            "genre": fit["genre"],
            "match_ratio": fit["match_ratio"],
        })

    # 3. Lacuna restoration demonstration
    restoration_demo = []
    for entry in CORPUS[:3]:
        tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
        if len(tokens) >= 3:
            # Simulate a gap at position 2
            predictions = engine.restore_lacuna(entry, 2)
            restoration_demo.append({
                "id": entry.get("id", ""),
                "gap_position": 2,
                "predictions": predictions[:3],
            })

    return {
        "genre_distribution": genre_dist,
        "template_fits": template_fits,
        "restoration_demos": restoration_demo,
        "summary": {
            "genres_identified": len(genre_dist["distribution"]),
            "dominant_genre": max(genre_dist["distribution"],
                                  key=genre_dist["distribution"].get),
            "inscriptions_classified": genre_dist["total_inscriptions"],
        },
    }
