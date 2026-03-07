#!/usr/bin/env python3
"""
Meroitic Script Analysis Runner
=================================
Runs all four analysis modules on the sample inscription corpus:
  1. Morpheme pattern identification & boundary detection
  2. Concordance building (KWIC)
  3. Nubian / Nilo-Saharan statistical comparison
  4. Inscription type clustering

Usage:
    python -m analysis.run_analysis           # run all analyses
    python -m analysis.run_analysis morpheme  # run only morpheme analysis
    python -m analysis.run_analysis concordance
    python -m analysis.run_analysis nubian
    python -m analysis.run_analysis clustering
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.data import SAMPLE_INSCRIPTIONS
from analysis.morpheme_analyzer import run_morpheme_analysis
from analysis.concordance import run_concordance
from analysis.nubian_comparator import run_nubian_comparison
from analysis.clustering import run_clustering


def main():
    inscriptions = SAMPLE_INSCRIPTIONS
    print(f"Loaded {len(inscriptions)} sample inscriptions.\n")

    analyses = {"morpheme", "concordance", "nubian", "clustering"}
    requested = set()
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.lower() in analyses:
                requested.add(arg.lower())
    if not requested:
        requested = analyses

    results = {}

    if "morpheme" in requested:
        results["morpheme"] = run_morpheme_analysis(inscriptions)
        print()

    if "concordance" in requested:
        results["concordance"] = run_concordance(inscriptions)
        print()

    if "nubian" in requested:
        results["nubian"] = run_nubian_comparison(inscriptions)
        print()

    if "clustering" in requested:
        results["clustering"] = run_clustering(inscriptions)
        print()

    # Summary
    print("=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    if "morpheme" in results:
        wf = results["morpheme"]["word_frequency"]
        mf = results["morpheme"]["morpheme_frequency"]
        print(f"  Morpheme Analysis: {len(wf)} unique words, {len(mf)} unique morphemes")
        print(f"    Top 5 words: {', '.join(w for w, _ in wf.most_common(5))}")
        affixes = results["morpheme"]["affixes"]
        print(f"    Detected {len(affixes['suffixes'])} suffixes, {len(affixes['prefixes'])} prefixes")

    if "concordance" in results:
        wc = results["concordance"]["word_concordance"]
        mc = results["concordance"]["morpheme_concordance"]
        print(f"  Concordance: {len(wc)} word entries, {len(mc)} morpheme entries")

    if "nubian" in results:
        nr = results["nubian"]
        print(f"  Nubian Comparison: avg similarity={nr['overall_avg_similarity']:.3f}, p={nr['p_value']:.4f}")
        if nr["p_value"] < 0.05:
            print(f"    → Statistically significant Meroitic-Nubian relationship")

    if "clustering" in results:
        cl = results["clustering"]["classifications"]
        correct = sum(1 for c in cl if c["correct"])
        print(f"  Clustering: {correct}/{len(cl)} correctly classified ({100*correct/len(cl):.0f}% accuracy)")

    print("\nDone.")


if __name__ == "__main__":
    main()
