#!/usr/bin/env python3
"""
Bayesian Corpus Ingestion Engine
==================================
Feeds the expanded 103-inscription corpus (and any future discoveries)
through the v5 Bayesian decoder, producing updated posteriors and
detecting new vocabulary candidates.

Usage:
    PYTHONPATH=. python3 scripts/bayesian_ingest.py
"""

import json
import csv
from pathlib import Path
from collections import Counter, defaultdict

from decipher import VOCABULARY, CORPUS
from decipher.v5_distributional import DistributionalEngine
from decipher.v5_reconstruction import ReconstructionEngine
from decipher.v5_bayesian_decoder import BayesianDecoder
from decipher.v5_new_readings import NewReadingsCompiler

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def run_bayesian_ingestion() -> dict:
    """Full Bayesian pipeline over the expanded corpus."""
    RESULTS.mkdir(exist_ok=True)

    print(f"  Corpus size: {len(CORPUS)} inscriptions")

    # Stage 1 — Distributional analysis on full corpus
    print("\n  [1/5] Distributional analysis …")
    dist = DistributionalEngine()
    dist_results = dist.run_full_analysis()
    print(f"        Tokens: {dist_results.get('corpus_tokens', '?')}, "
          f"Clusters: {len(dist_results.get('semantic_clusters', {}))}")

    # Stage 2 — Proto-NES reconstruction scan
    print("  [2/5] Proto-NES reconstruction …")
    recon = ReconstructionEngine()
    recon_results = recon.run_full_analysis()
    print(f"        NES entries: {recon_results.get('total_nes_entries', '?')}, "
          f"Matches: {recon_results.get('total_matches', 0)}")

    # Stage 3 — Bayesian decoding of ALL 103 inscriptions
    print("  [3/5] Bayesian decoding …")
    decoder = BayesianDecoder(
        distributional_results=dist_results,
        reconstruction_results=recon_results,
    )
    decoded = decoder.decode_corpus()
    stats = decoder.compute_corpus_statistics(decoded)
    print(f"        Decoded: {len(decoded)} inscriptions, "
          f"avg posterior: {stats.get('average_posterior', 0):.3f}")

    # Stage 4 — New readings compilation
    print("  [4/5] New readings compilation …")
    bayes_full = decoder.run_full_analysis()
    compiler = NewReadingsCompiler(
        distributional_results=dist_results,
        reconstruction_results=recon_results,
        bayesian_results=bayes_full,
    )
    new_readings = compiler.run_full_analysis()
    print(f"        New proposals: {new_readings.get('proposal_count', 0)}")

    # Stage 5 — Cross-corpus token census
    print("  [5/5] Token census …")
    tok_counts = Counter()
    tok_sites = defaultdict(set)
    tok_types = defaultdict(set)
    for insc in CORPUS:
        for tok in insc.get("text", "").split(":"):
            tok = tok.strip().lower()
            if tok and len(tok) >= 2:
                tok_counts[tok] += 1
                tok_sites[tok].add(insc.get("site", ""))
                tok_types[tok].add(insc.get("type", ""))

    # Identify tokens appearing in 3+ sites (strong cross-stele evidence)
    multi_site = {t: {"count": tok_counts[t], "sites": sorted(tok_sites[t]),
                       "types": sorted(tok_types[t])}
                  for t in tok_counts if len(tok_sites[t]) >= 3}

    print(f"        Unique tokens: {len(tok_counts)}")
    print(f"        Multi-site (≥3): {len(multi_site)}")

    # ── Outputs ──
    report = {
        "corpus_size": len(CORPUS),
        "distributional_summary": {
            "corpus_tokens": dist_results.get("corpus_tokens", 0),
            "unique_roots": dist_results.get("unique_roots", 0),
            "semantic_clusters": len(dist_results.get("semantic_clusters", {})),
        },
        "reconstruction_summary": {
            "nes_entries": recon_results.get("total_nes_entries", 0),
            "matches": recon_results.get("total_matches", 0),
        },
        "bayesian_summary": stats,
        "new_readings_count": new_readings.get("proposal_count", 0),
        "token_census": {
            "unique_tokens": len(tok_counts),
            "multi_site_tokens": len(multi_site),
            "top_20": [
                {"token": t, "count": c, "sites": sorted(tok_sites[t])}
                for t, c in tok_counts.most_common(20)
            ],
        },
        "multi_site_evidence": multi_site,
        "decodings_sample": decoded[:5],
    }

    path = RESULTS / "bayesian_ingestion_report.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved: {path}")

    # CSV of all decoded tokens
    csv_path = RESULTS / "bayesian_decoded_corpus.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["inscription_id", "site", "type", "token", "best_meaning",
                     "posterior", "source"])
        for d in decoded:
            for tok_d in d["decodings"]:
                w.writerow([d["id"], d["site"], d["type"], tok_d["token"],
                            tok_d["best_meaning"], tok_d["best_posterior"],
                            tok_d.get("source", "")])
    print(f"  Decoded CSV: {csv_path}")

    return report


if __name__ == "__main__":
    print("=" * 72)
    print("  BAYESIAN CORPUS INGESTION — v5 decoder × 103 inscriptions")
    print("=" * 72)
    report = run_bayesian_ingestion()
    print("\n  " + "=" * 60)
    s = report["bayesian_summary"]
    print(f"  Corpus size          : {report['corpus_size']}")
    print(f"  Unique tokens        : {report['token_census']['unique_tokens']}")
    print(f"  Multi-site (≥3 sites): {report['token_census']['multi_site_tokens']}")
    print(f"  Avg posterior        : {s.get('average_posterior', 0):.3f}")
    print(f"  New readings         : {report['new_readings_count']}")
    print("  DONE\n")
