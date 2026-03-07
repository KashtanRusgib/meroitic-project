"""
Nubian / Nilo-Saharan Statistical Comparator
==============================================
Performs statistical comparison between Meroitic vocabulary and
Nubian / Eastern Sudanic / Nilo-Saharan lexical items to evaluate
potential genetic relationships.

Methods:
  - Phonological similarity scoring (Levenshtein-based + weighted phonetic features)
  - Cognate confidence ranking
  - Sound correspondence tables
  - Statistical significance testing via Monte Carlo permutation
"""

import math
from collections import Counter, defaultdict
from typing import Optional


# Phonetic feature classes for weighted comparison
VOWELS = set("aeiou")
STOPS = set("ptk") | set("bdg")
NASALS = set("mn")
LIQUIDS = set("lr")
FRICATIVES = set("sfh")
SEMIVOWELS = set("wy")

# Sound correspondence rules observed in Nubian language family (Rilly 2007)
# Format: (meroitic_sound, nubian_sound, weight)
# Lower weight = more expected/regular correspondence
SOUND_CORRESPONDENCES = [
    ("p", "f", 0.3),   # p > f is regular in Nobiin
    ("p", "p", 0.0),
    ("t", "t", 0.0),
    ("k", "k", 0.0),
    ("k", "g", 0.3),   # voicing alternation
    ("q", "g", 0.3),   # uvular > velar
    ("q", "k", 0.4),
    ("b", "b", 0.0),
    ("d", "d", 0.0),
    ("s", "s", 0.0),
    ("s", "sh", 0.3),
    ("m", "m", 0.0),
    ("n", "n", 0.0),
    ("l", "l", 0.0),
    ("l", "r", 0.3),   # liquid alternation
    ("r", "r", 0.0),
    ("w", "w", 0.0),
    ("y", "y", 0.0),
    ("e", "i", 0.2),   # vowel raising
    ("o", "u", 0.2),   # vowel raising
    ("a", "a", 0.0),
    ("e", "e", 0.0),
    ("i", "i", 0.0),
    ("o", "o", 0.0),
    ("u", "u", 0.0),
]


def _build_correspondence_map() -> dict[tuple[str, str], float]:
    """Build lookup table for sound correspondences."""
    corr_map: dict[tuple[str, str], float] = {}
    for m, n, w in SOUND_CORRESPONDENCES:
        corr_map[(m, n)] = w
        corr_map[(n, m)] = w  # bidirectional
    return corr_map


_CORR_MAP = _build_correspondence_map()


def levenshtein_distance(s1: str, s2: str) -> int:
    """Standard Levenshtein edit distance."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (0 if c1 == c2 else 1)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def weighted_phonetic_distance(s1: str, s2: str) -> float:
    """Compute phonetically-weighted distance using known sound correspondences.

    Uses dynamic programming like Levenshtein but with weighted substitution
    costs based on known Nubian sound correspondences.
    """
    m, n = len(s1), len(s2)
    dp = [[0.0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = float(i)
    for j in range(n + 1):
        dp[0][j] = float(j)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            c1, c2 = s1[i - 1], s2[j - 1]
            if c1 == c2:
                sub_cost = 0.0
            else:
                sub_cost = _CORR_MAP.get((c1, c2), 1.0)
            dp[i][j] = min(
                dp[i - 1][j] + 1.0,      # deletion
                dp[i][j - 1] + 1.0,       # insertion
                dp[i - 1][j - 1] + sub_cost,  # substitution
            )

    return dp[m][n]


def phonetic_similarity(s1: str, s2: str) -> float:
    """Compute a similarity score [0, 1] between two words."""
    s1, s2 = s1.lower(), s2.lower()
    if not s1 or not s2:
        return 0.0
    dist = weighted_phonetic_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return max(0.0, 1.0 - dist / max_len)


def sound_correspondence_table(comparative_data: dict) -> dict[tuple[str, str], int]:
    """Build a table of observed sound correspondences between Meroitic and Nubian.

    Aligns characters of cognate pairs and counts corresponding sounds.
    """
    corr_counts: Counter = Counter()

    for meroitic, data in comparative_data.items():
        for lang_key in ["old_nubian", "nobiin", "dongolawi"]:
            nubian_form = data.get(lang_key, "")
            if not nubian_form:
                continue
            # Simple character-by-character alignment (shortest of the two)
            m_chars = list(meroitic.lower())
            n_chars = list(nubian_form.lower())
            for i in range(min(len(m_chars), len(n_chars))):
                corr_counts[(m_chars[i], n_chars[i])] += 1

    return dict(corr_counts)


def monte_carlo_significance(
    meroitic_words: list[str],
    nubian_words: list[str],
    observed_avg_sim: float,
    n_permutations: int = 5000,
) -> float:
    """Test statistical significance of observed similarity via permutation test.

    Compares observed average similarity against a null distribution generated
    by random pairing.
    Uses a simple deterministic shuffle approximation (no external random needed).
    """
    import hashlib

    similarities_above = 0
    for perm_i in range(n_permutations):
        # Deterministic pseudo-shuffle using hash
        shuffled = sorted(
            nubian_words,
            key=lambda w: hashlib.sha256(f"{w}{perm_i}".encode()).hexdigest()
        )
        perm_sim = 0.0
        count = min(len(meroitic_words), len(shuffled))
        for k in range(count):
            perm_sim += phonetic_similarity(meroitic_words[k], shuffled[k])
        perm_avg = perm_sim / count if count else 0
        if perm_avg >= observed_avg_sim:
            similarities_above += 1

    p_value = similarities_above / n_permutations
    return p_value


def run_nubian_comparison(inscriptions: list[dict], comparative_data: Optional[dict] = None,
                          eastern_sudanic_data: Optional[dict] = None) -> dict:
    """Run the full Nubian/Nilo-Saharan comparison and print results."""
    from .data import NUBIAN_COMPARATIVE, EASTERN_SUDANIC_COMPARATIVE

    if comparative_data is None:
        comparative_data = NUBIAN_COMPARATIVE
    if eastern_sudanic_data is None:
        eastern_sudanic_data = EASTERN_SUDANIC_COMPARATIVE

    print("=" * 70)
    print("NUBIAN / NILO-SAHARAN STATISTICAL COMPARISON")
    print("=" * 70)

    # 1. Cognate pair analysis
    print("\n--- Cognate Pair Analysis (Meroitic ↔ Nubian) ---")
    print(f"{'Meroitic':12s} {'Meaning':20s} {'Old Nubian':12s} {'Nobiin':10s} {'Dongolawi':10s} {'Phon.Sim':8s} {'Conf':5s}")
    print("-" * 85)

    all_similarities = []
    cognate_results = []

    for meroitic, data in sorted(comparative_data.items()):
        sims = []
        for lang in ["old_nubian", "nobiin", "dongolawi"]:
            form = data.get(lang, "")
            if form:
                sim = phonetic_similarity(meroitic, form)
                sims.append(sim)

        avg_sim = sum(sims) / len(sims) if sims else 0
        all_similarities.append(avg_sim)

        old_n = data.get("old_nubian", "-")
        nobiin = data.get("nobiin", "-")
        dong = data.get("dongolawi", "-")
        conf = data.get("confidence", 0)

        print(f"  {meroitic:12s} {data['meroitic_meaning']:20s} {old_n:12s} {nobiin:10s} {dong:10s} {avg_sim:7.3f}  {conf:.2f}")
        cognate_results.append({
            "meroitic": meroitic,
            "meaning": data["meroitic_meaning"],
            "avg_similarity": avg_sim,
            "confidence": conf,
        })

    overall_avg = sum(all_similarities) / len(all_similarities) if all_similarities else 0
    print(f"\n  Overall average phonetic similarity: {overall_avg:.4f}")

    # 2. Statistical significance
    print("\n--- Statistical Significance (Permutation Test) ---")
    mero_words = list(comparative_data.keys())
    nubian_words = [d.get("old_nubian", "") or d.get("nobiin", "") for d in comparative_data.values()]
    nubian_words = [w for w in nubian_words if w]

    p_value = monte_carlo_significance(mero_words, nubian_words, overall_avg, n_permutations=2000)
    print(f"  Observed avg similarity: {overall_avg:.4f}")
    print(f"  P-value (permutation test, n=2000): {p_value:.4f}")
    if p_value < 0.05:
        print(f"  → SIGNIFICANT at p<0.05: Meroitic-Nubian similarity is unlikely due to chance.")
    elif p_value < 0.10:
        print(f"  → MARGINALLY significant (0.05 < p < 0.10).")
    else:
        print(f"  → NOT significant: observed similarity consistent with chance.")

    # 3. Sound correspondence table
    print("\n--- Sound Correspondence Table (Meroitic ↔ Nubian) ---")
    corr_table = sound_correspondence_table(comparative_data)
    sorted_corrs = sorted(corr_table.items(), key=lambda x: -x[1])
    print(f"  {'Meroitic':>10s} → {'Nubian':<10s}  Count")
    for (m, n), count in sorted_corrs[:20]:
        marker = "  (regular)" if (m, n) in _CORR_MAP and _CORR_MAP[(m, n)] < 0.4 else ""
        print(f"  {m:>10s} → {n:<10s}  {count:3d}{marker}")

    # 4. Eastern Sudanic comparison
    print("\n--- Eastern Sudanic (Broader Nilo-Saharan) Comparison ---")
    print(f"  {'Meroitic':12s} {'Taman':10s} {'Taman Meaning':15s} {'Nara':10s} {'Nara Meaning':15s} {'Avg Sim':8s}")
    print("  " + "-" * 75)
    for meroitic, data in eastern_sudanic_data.items():
        taman = data.get("taman", "-")
        nara = data.get("nara", "-")
        sims = []
        if taman and taman != "-":
            sims.append(phonetic_similarity(meroitic, taman))
        if nara and nara != "-":
            sims.append(phonetic_similarity(meroitic, nara))
        avg = sum(sims) / len(sims) if sims else 0
        print(f"  {meroitic:12s} {taman:10s} {data.get('taman_meaning', '-'):15s} {nara:10s} {data.get('nara_meaning', '-'):15s} {avg:7.3f}")

    # 5. Confidence ranking
    print("\n--- Cognate Confidence Ranking ---")
    ranked = sorted(cognate_results, key=lambda x: -(x["avg_similarity"] * x["confidence"]))
    print(f"  {'Rank':5s} {'Meroitic':12s} {'Meaning':20s} {'Similarity':10s} {'Scholar Conf':12s} {'Combined':8s}")
    for i, r in enumerate(ranked, 1):
        combined = r["avg_similarity"] * r["confidence"]
        print(f"  {i:5d} {r['meroitic']:12s} {r['meaning']:20s} {r['avg_similarity']:10.3f} {r['confidence']:12.2f} {combined:8.3f}")

    return {
        "cognate_results": cognate_results,
        "overall_avg_similarity": overall_avg,
        "p_value": p_value,
        "sound_correspondences": corr_table,
    }
