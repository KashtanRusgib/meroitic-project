#!/usr/bin/env python3
"""
Brute-Force v5: Unknown Root Solver with Real Proto-NES Cognate Lookup
=======================================================================
Replaces the placeholder psycopg2/random-score version with actual:
  1. Real Proto-NES cognate similarity via edit-distance + sound-law scoring
  2. Distributional embedding similarity via PPMI cosine vectors
  3. v5.0 Bayesian weights for evidence fusion
  4. Cross-stele consistency from the full 66-inscription corpus

Operates standalone — no database required, uses the in-repo data directly.
"""

import math
import re
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import all in-repo data
from decipher import VOCABULARY, CORPUS, MORPHEMES
from decipher.nes_lexicon import NES_DICTIONARY, SOUND_LAWS
from decipher.cryptanalysis import KNOWN_PREFIXES, KNOWN_SUFFIXES
from decipher.v5_distributional import DistributionalEngine

ROOT = Path(__file__).resolve().parent.parent

# v5.0 Bayesian weights (from the Bayesian decoder evidence fusion)
WEIGHTS = {
    "lexical_match": 0.30,
    "nes_cognate":   0.25,
    "template_fit":  0.15,
    "frequency":     0.10,
    "distributional": 0.10,
    "consistency":   0.10,
}

MIN_CONFIDENCE = 0.20
MAX_MORPHEMES = 4


# ═══════════════════════════════════════════════════════════════════════════════
# PROTO-NES COGNATE SCORING (real implementation)
# ═══════════════════════════════════════════════════════════════════════════════

def _edit_distance(s1: str, s2: str) -> int:
    """Levenshtein edit distance."""
    if len(s1) < len(s2):
        return _edit_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            cost = 0 if c1 == c2 else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[len(s2)]


def _apply_sound_law_bonus(meroitic: str, proto: str) -> float:
    """
    Check how many sound laws connect the proto form to the Meroitic token.
    Returns a bonus score 0.0-0.4 based on matching sound correspondences.
    """
    bonus = 0.0
    for law in SOUND_LAWS:
        mer_phoneme = law.get("mer", "")
        nes_phoneme = law.get("nes", "")
        conf = law.get("conf", 0.5)
        if mer_phoneme in meroitic and nes_phoneme in proto:
            bonus += conf * 0.05
    return min(0.4, bonus)


def compute_nes_cognate_score(token: str) -> Tuple[float, str, str]:
    """
    Score a token against ALL entries in the NES dictionary.
    Returns (score, best_gloss, best_proto_form).
    
    Scoring: normalized edit distance + sound law bonus.
    """
    best_score = 0.0
    best_gloss = ""
    best_proto = ""

    token_clean = token.lower().strip("*-")

    for entry in NES_DICTIONARY:
        proto = entry.get("proto", "").strip("*").lower()
        gloss = entry.get("gloss", "")

        if not proto or len(proto) < 2:
            continue

        # Edit distance normalized to [0, 1]
        max_len = max(len(token_clean), len(proto))
        if max_len == 0:
            continue
        ed = _edit_distance(token_clean, proto)
        sim = 1.0 - (ed / max_len)

        # Sound law bonus
        law_bonus = _apply_sound_law_bonus(token_clean, proto)

        # Also check against attested forms in daughter languages
        daughter_bonus = 0.0
        for lang_key in ["nob", "don", "on", "mid", "bir", "nar", "nyi", "tam"]:
            daughter = entry.get(lang_key, "")
            if daughter:
                d_ed = _edit_distance(token_clean, daughter.lower())
                d_sim = 1.0 - (d_ed / max(len(token_clean), len(daughter)))
                daughter_bonus = max(daughter_bonus, d_sim * 0.3)

        total = sim * 0.6 + law_bonus + daughter_bonus

        if total > best_score:
            best_score = total
            best_gloss = gloss
            best_proto = entry.get("proto", "")

    return (round(min(1.0, best_score), 4), best_gloss, best_proto)


# ═══════════════════════════════════════════════════════════════════════════════
# DISTRIBUTIONAL EMBEDDING SIMILARITY (real implementation)
# ═══════════════════════════════════════════════════════════════════════════════

class EmbeddingSimilarity:
    """
    Uses the v5 distributional engine's PPMI vectors to find
    the most similar known token for each unknown root.
    """

    def __init__(self):
        self.engine = DistributionalEngine()
        self.known_tokens = self.engine.get_known_tokens()

    def most_similar_known(self, token: str) -> Tuple[float, str, str]:
        """
        Find the known token most similar to `token` in distributional space.
        Returns (similarity_score, most_similar_known_token, its_meaning).
        """
        root = self.engine._strip_morphology(token)
        if root not in self.engine.semantic_vectors:
            return (0.0, "", "")

        best_sim = 0.0
        best_token = ""
        best_meaning = ""

        for known in self.known_tokens:
            known_root = self.engine._strip_morphology(known)
            sim = self.engine.cosine_similarity(root, known_root)
            if sim > best_sim:
                best_sim = sim
                best_token = known
                ventry = VOCABULARY.get(known_root, VOCABULARY.get(known, {}))
                best_meaning = ventry.get("translation", "")

        return (round(best_sim, 4), best_token, best_meaning)


# ═══════════════════════════════════════════════════════════════════════════════
# BRUTE FORCE SEGMENTER (v5 enhanced)
# ═══════════════════════════════════════════════════════════════════════════════

class BruteForceV5:
    """
    Exhaustive segmentation + Bayesian scoring with real NES + embeddings.
    """

    def __init__(self):
        self.vocab = VOCABULARY
        self.corpus = CORPUS
        self.known_roots = set(self.vocab.keys())
        self.embeddings = EmbeddingSimilarity()

        # Build token frequency from corpus
        self.token_freq = Counter()
        for insc in self.corpus:
            for tok in insc.get("text", "").split(":"):
                tok = tok.strip().lower()
                if tok:
                    self.token_freq[tok] += 1

    def find_unknown_roots(self) -> Dict[str, List[str]]:
        """Find all tokens with certainty < 0.5 in the corpus."""
        unknowns: Dict[str, List[str]] = {}
        for entry in self.corpus:
            tokens = re.split(r"[\s:.\-]+", entry.get("text", ""))
            cleaned = [t.strip().lower() for t in tokens if t.strip() and len(t.strip()) >= 2]
            for tok in cleaned:
                ventry = self.vocab.get(tok, {})
                if ventry.get("certainty", 0) < 0.5:
                    if tok not in unknowns:
                        unknowns[tok] = []
                    unknowns[tok].append(entry.get("id", ""))
        return unknowns

    def _generate_segmentations(self, token: str) -> List[dict]:
        """Generate all 2-4 morpheme segmentations."""
        token = token.lower().strip()
        results = []

        prefix_options = [("", None)]
        for p_key, p_meta in KNOWN_PREFIXES.items():
            prefix_options.append((p_key.rstrip("-"), p_meta))

        for prefix_str, prefix_meta in prefix_options:
            if prefix_str and not token.startswith(prefix_str):
                continue
            remainder = token[len(prefix_str):]

            for root_end in range(2, len(remainder) + 1):
                root = remainder[:root_end]
                suffix_part = remainder[root_end:]
                suffix_combos = self._all_suffix_decompositions(suffix_part)

                for suffixes in suffix_combos:
                    total = (1 if prefix_str else 0) + 1 + len(suffixes)
                    if total < 1 or total > MAX_MORPHEMES:
                        continue
                    results.append({
                        "prefix": prefix_str or None,
                        "root": root,
                        "suffixes": [s["suffix"] for s in suffixes],
                        "suffix_functions": [s["function"] for s in suffixes],
                        "morpheme_count": total,
                    })
        return results

    def _all_suffix_decompositions(self, suffix_str: str) -> List[List[dict]]:
        """Recursively decompose suffix string into known suffixes."""
        if not suffix_str:
            return [[]]
        decompositions = []
        for suf_key, meta in sorted(KNOWN_SUFFIXES.items(), key=lambda x: -len(x[0])):
            suf_clean = suf_key.lstrip("-")
            if suffix_str.startswith(suf_clean):
                sub = self._all_suffix_decompositions(suffix_str[len(suf_clean):])
                for s in sub:
                    decompositions.append([{
                        "suffix": suf_clean,
                        "function": meta.get("function", ""),
                        "certainty": meta.get("certainty", 0.5),
                    }] + s)
        return decompositions

    def score_segmentation(self, seg: dict, token: str,
                           inscription_type: str = "") -> dict:
        """
        Score a segmentation using all v5.0 evidence streams.
        Returns enriched dict with component scores.
        """
        root = seg["root"]
        score = 0.0

        # 1. Lexical match (0.30)
        lexical = 0.0
        if root in self.known_roots:
            lexical = self.vocab[root].get("certainty", 0.3)
        else:
            # Partial match
            partials = [r for r in self.known_roots if r.startswith(root[:3]) and len(root) >= 3]
            if partials:
                lexical = 0.15
        score += WEIGHTS["lexical_match"] * lexical

        # 2. NES cognate (0.25) — REAL lookup
        nes_score, nes_gloss, nes_proto = compute_nes_cognate_score(root)
        score += WEIGHTS["nes_cognate"] * nes_score

        # 3. Template fit (0.15)
        template = 0.5  # neutral
        ventry = self.vocab.get(root, {})
        cat = ventry.get("category", "")
        if inscription_type == "funerary" and cat in ("funerary", "deity", "religion"):
            template = 0.9
        elif inscription_type == "royal" and cat in ("title", "deity"):
            template = 0.9
        elif inscription_type == "religious" and cat in ("deity", "religion"):
            template = 0.9
        elif cat:
            template = 0.65
        score += WEIGHTS["template_fit"] * template

        # 4. Frequency (0.10)
        freq = self.token_freq.get(root, 0)
        total = max(sum(self.token_freq.values()), 1)
        freq_score = min(1.0, math.log(freq + 1) / math.log(total + 1) * 5) if freq > 0 else 0
        score += WEIGHTS["frequency"] * freq_score

        # 5. Distributional embedding (0.10) — REAL lookup
        emb_sim, emb_nearest, emb_meaning = self.embeddings.most_similar_known(root)
        score += WEIGHTS["distributional"] * emb_sim

        # 6. Cross-stele consistency (0.10)
        root_count = sum(1 for e in self.corpus if root in e.get("text", "").lower())
        if root_count >= 4:
            consistency = 0.9
        elif root_count >= 2:
            consistency = 0.6
        elif root_count >= 1:
            consistency = 0.3
        else:
            consistency = 0.0
        score += WEIGHTS["consistency"] * consistency

        # Suffix coherence bonus
        for suf in seg.get("suffixes", []):
            score += 0.01

        return {
            "token": token,
            "prefix": seg["prefix"],
            "root": root,
            "suffixes": seg["suffixes"],
            "suffix_functions": seg.get("suffix_functions", []),
            "morpheme_count": seg["morpheme_count"],
            "root_known": root in self.known_roots,
            "root_meaning": ventry.get("translation", ""),
            "score": round(min(1.0, score), 4),
            # Evidence breakdown
            "lexical_score": round(lexical, 3),
            "nes_score": round(nes_score, 3),
            "nes_gloss": nes_gloss,
            "nes_proto": nes_proto,
            "template_score": round(template, 3),
            "freq_score": round(freq_score, 3),
            "embedding_sim": round(emb_sim, 3),
            "embedding_nearest": emb_nearest,
            "embedding_meaning": emb_meaning,
            "consistency_score": round(consistency, 3),
        }

    def solve_all(self) -> dict:
        """Run brute-force on all unknown roots with v5 scoring."""
        unknowns = self.find_unknown_roots()
        results = []

        # Map inscriptions to their types for template scoring
        type_map = {}
        for insc in self.corpus:
            for tok in re.split(r"[\s:.\-]+", insc.get("text", "")):
                tok = tok.strip().lower()
                if tok:
                    type_map[tok] = insc.get("type", "")

        for token in sorted(unknowns.keys()):
            segs = self._generate_segmentations(token)
            insc_type = type_map.get(token, "")

            scored = []
            for seg in segs:
                result = self.score_segmentation(seg, token, insc_type)
                scored.append(result)

            # Also score the whole token as a root (no segmentation)
            whole = self.score_segmentation({
                "prefix": None, "root": token, "suffixes": [],
                "suffix_functions": [], "morpheme_count": 1,
            }, token, insc_type)
            scored.append(whole)

            scored.sort(key=lambda x: -x["score"])
            top = scored[:5]

            results.append({
                "token": token,
                "occurrences": len(set(unknowns[token])),
                "inscription_ids": list(set(unknowns[token]))[:5],
                "best": top[0] if top else None,
                "alternatives": top[1:3],
                "confidence_gap": round(
                    (top[0]["score"] - top[1]["score"]) if len(top) > 1 else 0, 4
                ),
            })

        results.sort(key=lambda x: -(x["best"]["score"] if x["best"] else 0))

        solved = [r for r in results if r["best"] and r["best"]["root_known"]]
        partial = [r for r in results if r["best"] and not r["best"]["root_known"]
                   and r["best"]["score"] > 0.3]
        unsolved = [r for r in results if not r["best"] or r["best"]["score"] <= 0.3]

        return {
            "total_unknowns": len(unknowns),
            "solved": solved,
            "partially_solved": partial,
            "unsolved": unsolved,
            "all_results": results,
            "summary": {
                "total_unknown_tokens": len(unknowns),
                "solved_count": len(solved),
                "partially_solved_count": len(partial),
                "unsolved_count": len(unsolved),
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_brute_force_v5() -> dict:
    """Execute v5 brute-force lock solver."""
    solver = BruteForceV5()
    return solver.solve_all()


if __name__ == "__main__":
    print("=" * 72)
    print("  BRUTE-FORCE v5.0 — Unknown Root Solver")
    print("  Real Proto-NES cognates + Distributional embeddings")
    print("=" * 72)

    result = run_brute_force_v5()
    summary = result["summary"]

    print(f"\n  Unknown roots found    : {summary['total_unknown_tokens']}")
    print(f"  Solved (root known)    : {summary['solved_count']}")
    print(f"  Partially solved       : {summary['partially_solved_count']}")
    print(f"  Unsolved               : {summary['unsolved_count']}")

    print("\n  --- TOP RESULTS ---")
    for r in result["all_results"][:20]:
        b = r["best"]
        if not b:
            continue
        status = "KNOWN" if b["root_known"] else "NEW"
        nes_info = f"NES={b['nes_score']:.2f}/{b['nes_gloss']}" if b["nes_gloss"] else ""
        emb_info = f"EMB={b['embedding_sim']:.2f}/{b['embedding_nearest']}" if b["embedding_nearest"] else ""
        print(f"  {r['token']:18s} -> [{b['prefix'] or ''}]{b['root']}+{'+'.join(b['suffixes']) or '-'}"
              f"  score={b['score']:.3f} [{status}]"
              f"  {nes_info}  {emb_info}")

    # Save results
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)

    csv_path = out_dir / "v5_brute_force_proposals.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["token", "root", "prefix", "suffixes", "score",
                         "root_known", "root_meaning", "nes_score", "nes_gloss",
                         "nes_proto", "embedding_sim", "embedding_nearest",
                         "embedding_meaning", "occurrences", "source"])
        for r in result["all_results"]:
            b = r["best"]
            if b:
                writer.writerow([
                    r["token"], b["root"], b["prefix"] or "",
                    "+".join(b["suffixes"]) or "-",
                    b["score"], b["root_known"], b["root_meaning"],
                    b["nes_score"], b["nes_gloss"], b["nes_proto"],
                    b["embedding_sim"], b["embedding_nearest"],
                    b["embedding_meaning"], r["occurrences"], "v5_brute_force",
                ])
    print(f"\n  Results saved: {csv_path}")

    json_path = out_dir / "v5_brute_force_results.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"  Full results: {json_path}")

    print("\n  DONE")
