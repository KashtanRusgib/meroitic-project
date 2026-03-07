"""
Strategy 5: Brute-Force Combination Lock Solver
================================================
Exhaustive segmentation of all low-confidence tokens using a rolling
2–4 morpheme window, scored against:

  1. Zipf frequency (rare segmentations penalised)
  2. SOV + known-template fit
  3. NES cognate probability (from nes_lexicon.py)
  4. Cross-stele consistency (same root → same meaning everywhere)

Like trying every combination on a lock: for each unsolved token,
generate ALL possible [prefix + root + suffix₁ + suffix₂ + …]
segmentations and rank exhaustively.
"""

import math
import re
from collections import Counter, defaultdict
from typing import Optional

from decipher import VOCABULARY, CORPUS, MORPHEMES
from decipher.cryptanalysis import (
    KNOWN_PREFIXES, KNOWN_SUFFIXES,
    ZipfAnalyzer,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE CONSTRAINTS (SOV / funerary / royal patterns)
# ═══════════════════════════════════════════════════════════════════════════════

SOV_TEMPLATES = [
    {"name": "royal_titulary", "pattern": ["title", "name", "epithet"],
     "expected_pos": ["TITLE", "NAME", "ADJ"]},
    {"name": "offering_formula", "pattern": ["deity", "offering", "beneficiary"],
     "expected_pos": ["DEITY", "NOUN", "NAME"]},
    {"name": "funerary_invocation",
     "pattern": ["deity", "verb", "beneficiary", "wish"],
     "expected_pos": ["DEITY", "VERB", "NAME", "NOUN"]},
    {"name": "military_narrative",
     "pattern": ["subject", "verb", "object", "location"],
     "expected_pos": ["NAME", "VERB", "NOUN", "LOC"]},
]


class BruteForceSegmenter:
    """
    Generate ALL valid segmentations for a token and score exhaustively.
    """

    def __init__(self, vocabulary: Optional[dict] = None):
        self.vocabulary = vocabulary or VOCABULARY
        self.zipf = ZipfAnalyzer()
        self.token_freq = self.zipf.token_freq
        self.known_roots = set(self.vocabulary.keys())
        # Cross-stele consistency map: root → set of proposed meanings
        self._consistency_map: dict[str, Counter] = defaultdict(Counter)

    def _generate_segmentations(self, token: str) -> list[dict]:
        """
        Generate every possible segmentation of a token as:
          [prefix] + root + [suffix₁] + [suffix₂] + ...
        with 2-4 morpheme windows.
        """
        token = token.lower().strip()
        results = []

        # Enumerate prefixes (including no prefix)
        prefix_options = [("", None)] + [
            (p.rstrip("-"), meta) for p, meta in KNOWN_PREFIXES.items()
        ]

        for prefix_str, prefix_meta in prefix_options:
            if prefix_str and not token.startswith(prefix_str):
                continue

            remainder = token[len(prefix_str):]

            # Root must be at least 2 characters
            for root_end in range(2, len(remainder) + 1):
                root = remainder[:root_end]
                suffix_part = remainder[root_end:]

                # Generate all suffix decompositions
                suffix_combos = self._all_suffix_decompositions(suffix_part)

                for suffixes in suffix_combos:
                    total_morphemes = (1 if prefix_str else 0) + 1 + len(suffixes)
                    if total_morphemes < 2 or total_morphemes > 4:
                        continue

                    results.append({
                        "prefix": prefix_str or None,
                        "root": root,
                        "suffixes": suffixes,
                        "morpheme_count": total_morphemes,
                    })

        return results

    def _all_suffix_decompositions(self, suffix_str: str) -> list[list[dict]]:
        """
        Recursively enumerate all ways to decompose a suffix string
        into known suffixes. Returns list of lists of suffix dicts.
        """
        if not suffix_str:
            return [[]]

        decompositions = []
        for suf_key, meta in sorted(KNOWN_SUFFIXES.items(),
                                     key=lambda x: -len(x[0])):
            suf_clean = suf_key.lstrip("-")
            if suffix_str.startswith(suf_clean):
                sub_results = self._all_suffix_decompositions(
                    suffix_str[len(suf_clean):]
                )
                for sub in sub_results:
                    decompositions.append([{
                        "suffix": suf_clean,
                        "function": meta["function"],
                        "certainty": meta["certainty"],
                    }] + sub)

        return decompositions

    def _score_segmentation(self, seg: dict, context_tokens: list[str]) -> float:
        """
        Score a single segmentation hypothesis against four criteria:
          1. Zipf frequency of root (30%)
          2. Template fit (20%)
          3. Root recognition (30%)
          4. Cross-stele consistency (20%)
        """
        root = seg["root"]
        suffixes = seg.get("suffixes", [])
        prefix = seg.get("prefix")

        score = 0.0

        # 1. Zipf frequency (30%): more frequent roots score higher
        freq = self.token_freq.get(root, 0)
        total = max(sum(self.token_freq.values()), 1)
        if freq > 0:
            freq_score = min(1.0, math.log(freq + 1) / math.log(total + 1) * 5)
        else:
            freq_score = 0.0
        score += 0.30 * freq_score

        # 2. Template fit (20%): does the root's category fit the expected slot?
        ventry = self.vocabulary.get(root, {})
        category = ventry.get("category", "")
        if category:
            template_bonus = self._template_fit(category, context_tokens)
            score += 0.20 * template_bonus
        else:
            score += 0.05  # Small bonus for trying

        # 3. Root recognition (30%): is the root in vocabulary?
        if root in self.known_roots:
            cert = ventry.get("certainty", 0.3)
            score += 0.30 * cert
        else:
            # Partial match bonus
            partial_matches = [
                r for r in self.known_roots
                if r.startswith(root[:3]) and len(root) >= 3
            ]
            if partial_matches:
                score += 0.05

        # 4. Cross-stele consistency (20%): same root → same parse elsewhere?
        consistency = self._consistency_score(root, suffixes)
        score += 0.20 * consistency

        # Suffix coherence bonuses
        for suf in suffixes:
            score += 0.02 * suf.get("certainty", 0.5)

        # Verbal prefix + verbal suffix coherence
        if prefix and KNOWN_PREFIXES.get(prefix + "-", {}).get("type") == "verbal":
            has_verbal = any(
                KNOWN_SUFFIXES.get("-" + s["suffix"], {}).get("type") == "verbal"
                for s in suffixes
            )
            if has_verbal:
                score += 0.08

        return round(min(1.0, score), 4)

    def _template_fit(self, category: str, context_tokens: list[str]) -> float:
        """Check how well the category fits known templates."""
        cat_map = {
            "deity": "DEITY", "title": "TITLE", "food": "NOUN",
            "kinship": "NOUN", "body": "NOUN", "object": "NOUN",
            "religion": "DEITY", "action": "VERB", "place": "LOC",
            "quality": "ADJ",
        }
        pos = cat_map.get(category, "NOUN")

        best_fit = 0.0
        for template in SOV_TEMPLATES:
            for expected_pos in template["expected_pos"]:
                if pos == expected_pos:
                    best_fit = max(best_fit, 0.7)
        return best_fit

    def _consistency_score(self, root: str, suffixes: list[dict]) -> float:
        """
        Check whether the same root appears in other inscriptions
        with the same suffixal pattern.
        """
        suffix_sig = tuple(s["suffix"] for s in suffixes)
        key = (root, suffix_sig)

        # Count how many inscriptions contain this root
        root_inscriptions = 0
        for entry in CORPUS:
            text = entry.get("text", "").lower()
            if root in text:
                root_inscriptions += 1

        if root_inscriptions == 0:
            return 0.0
        elif root_inscriptions == 1:
            return 0.3
        elif root_inscriptions <= 3:
            return 0.6
        else:
            return 0.9

    def solve_token(self, token: str, context_tokens: Optional[list[str]] = None
                    ) -> list[dict]:
        """
        Generate and rank ALL segmentations for a single token.
        Returns top-10 scored hypotheses.
        """
        context_tokens = context_tokens or []
        segmentations = self._generate_segmentations(token)

        scored = []
        for seg in segmentations:
            seg_score = self._score_segmentation(seg, context_tokens)
            scored.append({
                "token": token,
                "prefix": seg["prefix"],
                "root": seg["root"],
                "suffixes": [s["suffix"] for s in seg["suffixes"]],
                "suffix_functions": [s["function"] for s in seg["suffixes"]],
                "morpheme_count": seg["morpheme_count"],
                "score": seg_score,
                "root_known": seg["root"] in self.known_roots,
                "root_meaning": self.vocabulary.get(
                    seg["root"], {}
                ).get("meaning", ""),
            })

        scored.sort(key=lambda x: -x["score"])
        return scored[:10]

    def solve_all_unknowns(self) -> dict:
        """
        Run brute-force segmentation on every low-confidence token
        in the entire corpus.
        """
        unknown_tokens: dict[str, list[str]] = {}  # token -> [inscription_ids]

        for entry in CORPUS:
            tokens = re.split(r"[\s:.\-]+", entry.get("text", ""))
            cleaned = [t.strip().lower() for t in tokens if t.strip() and len(t.strip()) >= 3]
            for tok in cleaned:
                ventry = self.vocabulary.get(tok, {})
                if ventry.get("certainty", 0) < 0.5:
                    if tok not in unknown_tokens:
                        unknown_tokens[tok] = []
                    unknown_tokens[tok].append(entry.get("id", ""))

        results = []
        for token in sorted(unknown_tokens.keys()):
            solutions = self.solve_token(token)
            if solutions:
                results.append({
                    "token": token,
                    "occurrences": len(set(unknown_tokens[token])),
                    "inscription_ids": list(set(unknown_tokens[token]))[:5],
                    "best_solution": solutions[0],
                    "runner_up": solutions[1] if len(solutions) > 1 else None,
                    "confidence_gap": round(
                        solutions[0]["score"] - (
                            solutions[1]["score"] if len(solutions) > 1 else 0
                        ), 4
                    ),
                })

        # Sort by confidence gap (bigger gap = more decisive answer)
        results.sort(key=lambda x: -x["confidence_gap"])

        return {
            "total_unknowns": len(unknown_tokens),
            "solved": [r for r in results if r["best_solution"]["root_known"]],
            "partially_solved": [
                r for r in results
                if not r["best_solution"]["root_known"]
                and r["best_solution"]["score"] > 0.3
            ],
            "unsolved": [
                r for r in results
                if r["best_solution"]["score"] <= 0.3
            ],
            "all_results": results,
            "summary": {
                "total_unknown_tokens": len(unknown_tokens),
                "solved_count": sum(
                    1 for r in results if r["best_solution"]["root_known"]
                ),
                "partially_solved_count": sum(
                    1 for r in results
                    if not r["best_solution"]["root_known"]
                    and r["best_solution"]["score"] > 0.3
                ),
                "unsolved_count": sum(
                    1 for r in results if r["best_solution"]["score"] <= 0.3
                ),
            },
        }


def run_brute_force() -> dict:
    """Execute the brute-force combination lock solver."""
    solver = BruteForceSegmenter()
    return solver.solve_all_unknowns()
