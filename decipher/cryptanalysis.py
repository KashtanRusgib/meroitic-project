"""
Strategy 4: Computational / Statistical Cryptanalysis
=====================================================
Treats Meroitic as a partially-deciphered cipher and applies computational
linguistics methods proven on Ugaritic (Snyder+ 2010, Luo+ 2021):

  1. Cross-lingual embedding alignment (Meroitic ↔ Nobiin/Old Nubian)
  2. Bayesian morphological inference (every suffix combination tested)
  3. Zipf's law frequency analysis for lexical identification
  4. Mutual information & transitional probability for segmentation
  5. Distributional semantics for unknown tokens

Ref: Luo+ 2021 "Decipherment of Historical Languages"; 2025 ACL paper
     "Towards Ancient Meroitic Decipherment"
"""

import math
import re
from collections import Counter, defaultdict
from typing import Optional

from decipher import (
    VOCABULARY, CORPUS, MORPHEMES, PHONEME_INVENTORY,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  ZIPF'S LAW FREQUENCY ANALYSER
# ═══════════════════════════════════════════════════════════════════════════════

class ZipfAnalyzer:
    """
    Compute token frequencies across the entire corpus and check
    whether they follow Zipf's law.  A well-segmented natural language
    text obeys:  freq(rank=r) ≈ C / r^α, α ≈ 1.
    Deviations point to segmentation errors or foreign loanwords.
    """

    def __init__(self, corpus: Optional[list] = None):
        self.corpus = corpus or CORPUS
        self.token_freq: Counter = Counter()
        self._build()

    def _build(self):
        for entry in self.corpus:
            text = entry.get("text", "")
            tokens = re.split(r"[\s:.\-]+", text)
            for tok in tokens:
                tok = tok.strip().lower()
                if tok and len(tok) >= 2:
                    self.token_freq[tok] += 1

    def zipf_table(self, top_n: int = 60) -> list[dict]:
        """Return ranked frequency table with expected Zipf values."""
        ranked = self.token_freq.most_common(top_n)
        if not ranked:
            return []
        max_freq = ranked[0][1]
        table = []
        for rank, (token, freq) in enumerate(ranked, 1):
            expected = max_freq / rank
            deviation = abs(freq - expected) / max(expected, 1)
            table.append({
                "rank": rank,
                "token": token,
                "observed_freq": freq,
                "expected_zipf": round(expected, 2),
                "deviation": round(deviation, 3),
                "in_vocabulary": token in VOCABULARY,
            })
        return table

    def anomalous_tokens(self, threshold: float = 1.5) -> list[dict]:
        """
        Find tokens whose frequency deviates strongly from Zipf expectations.
        Over-frequent unknowns may be function words; under-frequent known
        words may be segmentation artefacts.
        """
        table = self.zipf_table(top_n=len(self.token_freq))
        return [
            entry for entry in table
            if entry["deviation"] > threshold
        ]

    def zipf_exponent(self) -> float:
        """Estimate the Zipf exponent α via log-log linear regression."""
        ranked = self.token_freq.most_common()
        if len(ranked) < 3:
            return 0.0
        log_ranks = [math.log(r + 1) for r in range(len(ranked))]
        log_freqs = [math.log(max(f, 1)) for _, f in ranked]
        n = len(log_ranks)
        sum_x = sum(log_ranks)
        sum_y = sum(log_freqs)
        sum_xy = sum(x * y for x, y in zip(log_ranks, log_freqs))
        sum_x2 = sum(x * x for x in log_ranks)
        denom = n * sum_x2 - sum_x * sum_x
        if denom == 0:
            return 0.0
        slope = (n * sum_xy - sum_x * sum_y) / denom
        return round(-slope, 4)


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  TRANSITIONAL PROBABILITY & MUTUAL INFORMATION
# ═══════════════════════════════════════════════════════════════════════════════

class TransitionalAnalyzer:
    """
    Compute bigram transitional probabilities and pointwise mutual
    information (PMI) between adjacent tokens or characters.
    High-PMI pairs likely form collocations or compound words.
    """

    def __init__(self, corpus: Optional[list] = None):
        self.corpus = corpus or CORPUS
        self.bigrams: Counter = Counter()
        self.unigrams: Counter = Counter()
        self.total_bigrams = 0
        self.total_unigrams = 0
        self._build()

    def _build(self):
        for entry in self.corpus:
            tokens = re.split(r"[\s:.\-]+", entry.get("text", ""))
            tokens = [t.lower().strip() for t in tokens if t.strip() and len(t.strip()) >= 2]
            for tok in tokens:
                self.unigrams[tok] += 1
                self.total_unigrams += 1
            for i in range(len(tokens) - 1):
                pair = (tokens[i], tokens[i + 1])
                self.bigrams[pair] += 1
                self.total_bigrams += 1

    def pmi(self, w1: str, w2: str) -> float:
        """Pointwise Mutual Information between two tokens."""
        pair_count = self.bigrams.get((w1, w2), 0)
        if pair_count == 0:
            return 0.0
        p_pair = pair_count / max(self.total_bigrams, 1)
        p_w1 = self.unigrams.get(w1, 0) / max(self.total_unigrams, 1)
        p_w2 = self.unigrams.get(w2, 0) / max(self.total_unigrams, 1)
        if p_w1 == 0 or p_w2 == 0:
            return 0.0
        return round(math.log2(p_pair / (p_w1 * p_w2)), 4)

    def high_pmi_pairs(self, min_count: int = 2, top_n: int = 30) -> list[dict]:
        """Return bigrams with highest PMI, filtered by minimum count."""
        results = []
        for (w1, w2), count in self.bigrams.items():
            if count >= min_count:
                score = self.pmi(w1, w2)
                results.append({
                    "pair": (w1, w2),
                    "count": count,
                    "pmi": score,
                    "w1_known": w1 in VOCABULARY,
                    "w2_known": w2 in VOCABULARY,
                })
        results.sort(key=lambda x: -x["pmi"])
        return results[:top_n]

    def transitional_prob(self, w1: str, w2: str) -> float:
        """P(w2 | w1) = count(w1,w2) / count(w1)."""
        w1_count = self.unigrams.get(w1, 0)
        if w1_count == 0:
            return 0.0
        return self.bigrams.get((w1, w2), 0) / w1_count


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  BAYESIAN MORPHOLOGICAL INFERENCE
# ═══════════════════════════════════════════════════════════════════════════════

# Known affixes from existing analysis
KNOWN_PREFIXES = {
    "e-": {"function": "1SG subject", "type": "verbal", "certainty": 0.85},
    "te-": {"function": "2SG subject", "type": "verbal", "certainty": 0.80},
    "ne-": {"function": "1PL subject", "type": "verbal", "certainty": 0.70},
}

KNOWN_SUFFIXES = {
    "-l": {"function": "plural/collective", "type": "nominal", "certainty": 0.90},
    "-li": {"function": "plural/collective (animate)", "type": "nominal", "certainty": 0.85},
    "-se": {"function": "plural (human)", "type": "nominal", "certainty": 0.80},
    "-o": {"function": "genitive/possessive", "type": "nominal", "certainty": 0.85},
    "-ke": {"function": "locative/at", "type": "nominal", "certainty": 0.80},
    "-te": {"function": "dative/for", "type": "nominal", "certainty": 0.80},
    "-wi": {"function": "prepositional/with", "type": "nominal", "certainty": 0.70},
    "-b": {"function": "definite article", "type": "nominal", "certainty": 0.60},
    "-x": {"function": "past tense marker", "type": "verbal", "certainty": 0.70},
    "-to": {"function": "accusative/object", "type": "nominal", "certainty": 0.65},
}


class BayesianMorphology:
    """
    Bayesian inference engine for Meroitic morphology.
    For each unknown token, generate all possible segmentations
    into [prefix + root + suffix(es)] and score each by:
      P(segmentation | token) ∝ P(prefix) × P(root) × P(suffix) × P(coherence)
    """

    def __init__(self, vocabulary: Optional[dict] = None):
        self.vocabulary = vocabulary or VOCABULARY
        self.roots = set()
        self.root_freq: Counter = Counter()
        self._extract_roots()

    def _extract_roots(self):
        """Build set of known roots from vocabulary."""
        for word in self.vocabulary:
            self.roots.add(word.lower())
            self.root_freq[word.lower()] += 1

        # Also extract roots from corpus
        for entry in CORPUS:
            tokens = re.split(r"[\s:.\-]+", entry.get("text", ""))
            for tok in tokens:
                tok = tok.strip().lower()
                if tok in self.vocabulary:
                    self.root_freq[tok] += 1

    def segment(self, token: str) -> list[dict]:
        """
        Generate all valid segmentations of a token.
        Returns ranked list of {prefix, root, suffixes, score}.
        """
        token = token.lower().strip()
        hypotheses = []

        prefixes_to_try = [("", None)] + [
            (p.rstrip("-"), meta) for p, meta in KNOWN_PREFIXES.items()
        ]
        suffixes_to_try = [("", None)] + [
            (s.lstrip("-"), meta) for s, meta in KNOWN_SUFFIXES.items()
        ]

        for prefix_str, prefix_meta in prefixes_to_try:
            if prefix_str and not token.startswith(prefix_str):
                continue
            remainder = token[len(prefix_str):]

            for i in range(len(remainder), 0, -1):
                candidate_root = remainder[:i]
                suffix_str = remainder[i:]

                if len(candidate_root) < 2:
                    continue

                # Try to match suffix (or chain of suffixes)
                suffix_matches = self._match_suffixes(suffix_str)
                if suffix_str and not suffix_matches:
                    continue

                # Score this hypothesis
                score = self._score_hypothesis(
                    prefix_str, prefix_meta, candidate_root, suffix_matches
                )

                hypotheses.append({
                    "token": token,
                    "prefix": prefix_str or None,
                    "root": candidate_root,
                    "suffixes": [s["suffix"] for s in suffix_matches],
                    "suffix_functions": [s["function"] for s in suffix_matches],
                    "score": round(score, 4),
                    "root_known": candidate_root in self.roots,
                })

        hypotheses.sort(key=lambda h: -h["score"])
        return hypotheses[:5]

    def _match_suffixes(self, suffix_str: str) -> list[dict]:
        """Try to decompose suffix_str into known suffix chain."""
        if not suffix_str:
            return []

        results = []
        remaining = suffix_str

        while remaining:
            matched = False
            for suf, meta in sorted(KNOWN_SUFFIXES.items(),
                                     key=lambda x: -len(x[0])):
                suf_clean = suf.lstrip("-")
                if remaining.startswith(suf_clean):
                    results.append({
                        "suffix": suf_clean,
                        "function": meta["function"],
                        "certainty": meta["certainty"],
                    })
                    remaining = remaining[len(suf_clean):]
                    matched = True
                    break

            if not matched:
                return results if remaining == "" else []

        return results

    def _score_hypothesis(self, prefix: str, prefix_meta: Optional[dict],
                          root: str, suffix_matches: list[dict]) -> float:
        """Bayesian-style score for a segmentation hypothesis."""
        score = 0.5  # Base prior

        # Root probability
        if root in self.roots:
            cert = self.vocabulary.get(root, {}).get("certainty", 0.5)
            score += 0.3 * cert
            freq_bonus = min(0.1, self.root_freq.get(root, 0) * 0.01)
            score += freq_bonus
        elif root in {r[:len(root)] for r in self.roots if len(r) >= len(root)}:
            score += 0.1  # Partial root match

        # Prefix probability
        if prefix and prefix_meta:
            score += 0.15 * prefix_meta.get("certainty", 0.5)

        # Suffix probability
        for smatch in suffix_matches:
            score += 0.1 * smatch["certainty"]

        # Coherence: verbal prefix should have verbal suffix
        if prefix_meta and prefix_meta.get("type") == "verbal":
            has_verbal_suffix = any(
                KNOWN_SUFFIXES.get("-" + s["suffix"], {}).get("type") == "verbal"
                for s in suffix_matches
            )
            if has_verbal_suffix:
                score += 0.15

        # Length penalty: very short roots are suspicious
        if len(root) < 3:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def analyze_unknowns(self) -> list[dict]:
        """Segment every low-confidence or unknown token in the corpus."""
        unknown_tokens = set()
        for entry in CORPUS:
            tokens = re.split(r"[\s:.\-]+", entry.get("text", ""))
            for tok in tokens:
                tok = tok.strip().lower()
                if tok and len(tok) >= 3:
                    ventry = self.vocabulary.get(tok, {})
                    if ventry.get("certainty", 0) < 0.5:
                        unknown_tokens.add(tok)

        results = []
        for token in sorted(unknown_tokens):
            segmentations = self.segment(token)
            if segmentations:
                results.append({
                    "token": token,
                    "best_segmentation": segmentations[0],
                    "alternatives": segmentations[1:3],
                })

        return results


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  DISTRIBUTIONAL SEMANTICS
# ═══════════════════════════════════════════════════════════════════════════════

class DistributionalAnalyzer:
    """
    Build co-occurrence vectors for all tokens and use cosine similarity
    to infer meaning of unknown words from their distributional context.
    Words that appear in similar positions likely have related meanings.
    """

    def __init__(self, window: int = 3, corpus: Optional[list] = None):
        self.window = window
        self.corpus = corpus or CORPUS
        self.cooccurrence: dict[str, Counter] = defaultdict(Counter)
        self.token_freq: Counter = Counter()
        self._build()

    def _build(self):
        for entry in self.corpus:
            tokens = re.split(r"[\s:.\-]+", entry.get("text", ""))
            tokens = [t.lower().strip() for t in tokens if t.strip() and len(t.strip()) >= 2]
            for i, tok in enumerate(tokens):
                self.token_freq[tok] += 1
                start = max(0, i - self.window)
                end = min(len(tokens), i + self.window + 1)
                for j in range(start, end):
                    if j != i:
                        self.cooccurrence[tok][tokens[j]] += 1

    def _cosine(self, v1: Counter, v2: Counter) -> float:
        """Cosine similarity between two co-occurrence vectors."""
        shared_keys = set(v1.keys()) & set(v2.keys())
        if not shared_keys:
            return 0.0
        dot = sum(v1[k] * v2[k] for k in shared_keys)
        mag1 = math.sqrt(sum(v * v for v in v1.values()))
        mag2 = math.sqrt(sum(v * v for v in v2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    def similar_to(self, word: str, top_n: int = 10) -> list[dict]:
        """Find tokens with most similar distributional profiles."""
        word = word.lower()
        if word not in self.cooccurrence:
            return []

        target_vec = self.cooccurrence[word]
        similarities = []
        for other, other_vec in self.cooccurrence.items():
            if other == word:
                continue
            sim = self._cosine(target_vec, other_vec)
            if sim > 0:
                similarities.append({
                    "word": other,
                    "similarity": round(sim, 4),
                    "known": other in VOCABULARY,
                    "meaning": VOCABULARY.get(other, {}).get("meaning", ""),
                })

        similarities.sort(key=lambda x: -x["similarity"])
        return similarities[:top_n]

    def infer_unknown_meanings(self) -> list[dict]:
        """
        For each unknown token, find its nearest known neighbours
        and propose meanings by semantic transfer.
        """
        results = []
        for token in sorted(self.cooccurrence.keys()):
            if token in VOCABULARY and VOCABULARY[token].get("certainty", 0) >= 0.5:
                continue
            if self.token_freq[token] < 2:
                continue

            neighbors = self.similar_to(token, top_n=5)
            known_neighbors = [n for n in neighbors if n["known"] and n["meaning"]]
            if known_neighbors:
                results.append({
                    "token": token,
                    "frequency": self.token_freq[token],
                    "nearest_known": known_neighbors[:3],
                    "proposed_field": self._infer_field(known_neighbors),
                    "confidence": round(
                        known_neighbors[0]["similarity"] * 0.8, 3
                    ) if known_neighbors else 0.0,
                })

        results.sort(key=lambda x: -x["confidence"])
        return results

    def _infer_field(self, neighbors: list[dict]) -> str:
        """Infer semantic field from nearest known neighbours."""
        fields = []
        for n in neighbors:
            ventry = VOCABULARY.get(n["word"], {})
            if ventry.get("category"):
                fields.append(ventry["category"])
        if fields:
            return Counter(fields).most_common(1)[0][0]
        return "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  CROSS-LINGUAL ALIGNMENT (simplified embedding proxy)
# ═══════════════════════════════════════════════════════════════════════════════

# Nubian (Nobiin) comparison vocabulary for alignment
NOBIIN_REFERENCE = {
    "ìr": "water", "ág": "mouth", "kàmm": "camel/cattle",
    "dôl": "mountain", "kúr": "house", "nóg": "gold",
    "mássì": "sun", "èssì": "fire", "ŋárrì": "man",
    "ìddì": "woman", "tòg": "land", "kárr": "call",
    "dìpp": "eat/drink", "wêr": "big", "kìddi": "small",
    "tíl": "eye", "ùr": "head", "kúrrì": "dog",
    "ìttì": "milk", "bírr": "seed", "shè": "grain",
    "ìddò": "name", "mèr": "good", "tîn": "give",
    "dèw": "die", "díg": "go", "nòb": "gold (alt)",
    "ùssì": "cook", "bèll": "bring", "kìr": "stone",
    "jír": "fill", "píl": "emerge", "dôg": "see",
    "ánkì": "go out", "tûn": "stand", "kôr": "work",
}


class CrossLingualAligner:
    """
    Simple phonological alignment between Meroitic and Nobiin.
    For each Meroitic unknown, find Nobiin words with maximal
    phonological overlap, weighted by known sound correspondences.
    """

    SOUND_CORRESPONDENCES = {
        ("k", "g"): 0.85,
        ("q", "k"): 0.80,
        ("q", "g"): 0.75,
        ("t", "d"): 0.80,
        ("p", "b"): 0.80,
        ("p", "f"): 0.70,
        ("s", "sh"): 0.75,
        ("l", "r"): 0.85,
        ("w", "b"): 0.60,
        ("n", "ŋ"): 0.75,
        ("e", "è"): 0.95,
        ("i", "ì"): 0.95,
        ("o", "ò"): 0.95,
        ("a", "à"): 0.95,
    }

    def __init__(self):
        self.reference = NOBIIN_REFERENCE

    def align(self, meroitic_root: str, nobiin_form: str) -> float:
        """
        Phonological alignment score between Meroitic root and Nobiin form.
        """
        m = meroitic_root.lower()
        n = nobiin_form.lower()

        if not m or not n:
            return 0.0

        # Simplified edit-distance-like alignment
        matches = 0
        total = max(len(m), len(n))

        i, j = 0, 0
        while i < len(m) and j < len(n):
            if m[i] == n[j]:
                matches += 1.0
                i += 1
                j += 1
            else:
                # Check sound correspondences
                corr = self._sound_corr(m[i], n[j])
                if corr > 0:
                    matches += corr
                    i += 1
                    j += 1
                else:
                    # Gap
                    if len(m) > len(n):
                        i += 1
                    else:
                        j += 1

        return round(matches / max(total, 1), 4)

    def _sound_corr(self, c1: str, c2: str) -> float:
        """Look up sound correspondence score."""
        pair = (c1, c2)
        rev_pair = (c2, c1)
        return self.SOUND_CORRESPONDENCES.get(
            pair, self.SOUND_CORRESPONDENCES.get(rev_pair, 0.0)
        )

    def find_matches(self, meroitic_root: str, min_score: float = 0.4) -> list[dict]:
        """Find all Nobiin matches above threshold for a Meroitic root."""
        results = []
        for nob_form, nob_meaning in self.reference.items():
            score = self.align(meroitic_root, nob_form)
            if score >= min_score:
                results.append({
                    "meroitic": meroitic_root,
                    "nobiin": nob_form,
                    "nobiin_meaning": nob_meaning,
                    "alignment_score": score,
                })
        results.sort(key=lambda x: -x["alignment_score"])
        return results

    def scan_unknowns(self) -> list[dict]:
        """Scan all unknown vocabulary entries for Nobiin alignments."""
        results = []
        for word, entry in VOCABULARY.items():
            if entry.get("certainty", 0) < 0.5:
                matches = self.find_matches(word, min_score=0.45)
                if matches:
                    results.append({
                        "meroitic": word,
                        "best_match": matches[0],
                        "alternatives": matches[1:3],
                        "current_certainty": entry.get("certainty", 0),
                    })
        results.sort(key=lambda x: -x["best_match"]["alignment_score"])
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

def run_cryptanalysis() -> dict:
    """Execute full statistical cryptanalysis pipeline."""
    # 1. Zipf analysis
    zipf = ZipfAnalyzer()
    zipf_table = zipf.zipf_table(top_n=40)
    zipf_alpha = zipf.zipf_exponent()
    anomalous = zipf.anomalous_tokens(threshold=1.2)

    # 2. Transitional probabilities
    trans = TransitionalAnalyzer()
    high_pmi = trans.high_pmi_pairs(min_count=2, top_n=20)

    # 3. Bayesian morphology
    bayes = BayesianMorphology()
    morph_results = bayes.analyze_unknowns()

    # 4. Distributional semantics
    dist = DistributionalAnalyzer(window=3)
    inferred = dist.infer_unknown_meanings()

    # 5. Cross-lingual alignment
    aligner = CrossLingualAligner()
    alignments = aligner.scan_unknowns()

    return {
        "zipf_analysis": {
            "exponent": zipf_alpha,
            "expected_range": "0.8-1.2 for natural language",
            "is_natural": 0.7 <= zipf_alpha <= 1.5,
            "top_tokens": zipf_table[:20],
            "anomalous_tokens": anomalous[:15],
        },
        "transitional_probabilities": {
            "high_pmi_collocations": high_pmi,
            "total_bigrams": trans.total_bigrams,
        },
        "bayesian_morphology": {
            "unknown_tokens_analyzed": len(morph_results),
            "segmentations": morph_results[:20],
        },
        "distributional_semantics": {
            "meanings_inferred": len(inferred),
            "proposals": inferred[:15],
        },
        "cross_lingual_alignment": {
            "nobiin_matches_found": len(alignments),
            "alignments": alignments[:15],
        },
        "summary": {
            "zipf_exponent": zipf_alpha,
            "unique_tokens_in_corpus": len(zipf.token_freq),
            "high_pmi_collocations": len(high_pmi),
            "morphological_analyses": len(morph_results),
            "distributional_inferences": len(inferred),
            "cross_lingual_alignments": len(alignments),
        },
    }
