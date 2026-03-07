#!/usr/bin/env python3
"""
Meroitic Full Pipeline v3.0 — Integration Runner
==================================================
Orchestrates ALL analysis modules (original + new) in a single run:

  1. Cognate mining  → Expanded Nilo-Saharan lexicon
  2. Morphosyntactic → Verbal chains, suffix mapping, clause parsing
  3. Template engine  → Genre classification, lacuna restoration, n-gram models
  4. Corpus analysis  → Confidence recalculation, predictive evaluation
  5. Full translation → Existing 6-stage pipeline + new evidence integration
  6. Tanyidamani v3   → Re-decode REM 1044 with all new evidence
  7. Export            → Updated JSON / TSV artefacts

Usage:
    python3 run_full_pipeline_v3.py
"""

import json
import sys
from pathlib import Path

# ── Imports: Original pipeline ────────────────────────────────────────────────
from decipher import (
    VOCABULARY, MORPHEMES, SYNTACTIC_RULES, CORPUS,
    NUBIAN_COMPARATIVE, EASTERN_SUDANIC_COMPARATIVE,
    KNOWN_ROYAL_NAMES, SITES,
)
from decipher.lexicon import LexiconBuilder
from decipher.comparative import create_comparative_engine
from decipher.translator import create_translation_pipeline
from decipher.confidence import create_confidence_scorer

# ── Imports: New modules ──────────────────────────────────────────────────────
from decipher.cognate_mining import run_cognate_mining
from decipher.morphosyntax import run_morphosyntactic_analysis
from decipher.template_engine import run_template_analysis
from decipher.corpus_ingestion import run_corpus_analysis, ConfidenceUpdater

# ── Imports: Tanyidamani ──────────────────────────────────────────────────────
from decipher.tanyidamani_stele import STELE_SECTIONS

ROOT = Path(__file__).resolve().parent
DIVIDER = "=" * 72
THIN = "-" * 72


def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def run():
    print(DIVIDER)
    print("  MEROITIC DECIPHERMENT PIPELINE v3.0")
    print("  Full integration: cognate mining + morphosyntax + templates")
    print(DIVIDER)

    results = {}

    # Merge comparative data
    comparative = dict(NUBIAN_COMPARATIVE)
    comparative.update(EASTERN_SUDANIC_COMPARATIVE)

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 1: COGNATE MINING — Expand Nilo-Saharan Lexicon
    # ──────────────────────────────────────────────────────────────────────
    section("STAGE 1: COGNATE MINING")
    cognate_results = run_cognate_mining()

    new_cognates = cognate_results["new_cognate_proposals"]
    semantic_anchors = cognate_results["semantic_anchoring"]
    triangulations = cognate_results["triangulated_meanings"]
    csummary = cognate_results["summary"]

    print(f"  New cognate pairs mined   : {len(new_cognates)}")
    print(f"  Semantic anchors generated: {len(semantic_anchors)}")
    print(f"  Triangulated meanings     : {len(triangulations)}")
    print(f"  Extended Nubian entries   : {csummary['extended_nubian_entries']}")
    print(f"  Extended ES entries       : {csummary['extended_es_entries']}")

    for cog in new_cognates[:10]:
        print(f"    {cog.get('meroitic', '?'):15s} → {cog.get('proto_form', '?'):15s} "
              f"'{cog.get('meaning', '?')}' [score={cog.get('score', 0):.3f}]")

    results["cognate_mining"] = {
        "new_cognates": len(new_cognates),
        "semantic_anchors": len(semantic_anchors),
        "triangulations": len(triangulations),
        "extended_nubian": csummary["extended_nubian_entries"],
        "extended_es": csummary["extended_es_entries"],
        "top_cognates": new_cognates[:20],
    }

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 2: MORPHOSYNTACTIC ANALYSIS
    # ──────────────────────────────────────────────────────────────────────
    section("STAGE 2: MORPHOSYNTACTIC ANALYSIS")
    morpho_results = run_morphosyntactic_analysis()

    verbal_chain_analysis = morpho_results["verbal_chain_analysis"]
    suffix_mapping = morpho_results["suffix_mapping"]
    clause_samples = morpho_results["clause_parsing_samples"]
    msummary = morpho_results["summary"]

    print(f"  Total verbal chains found : {msummary['total_verbal_chains']}")
    print(f"  Unique verb roots         : {msummary['unique_verb_roots']}")
    print(f"  Suffix types attested     : {msummary['suffix_types_attested']}")
    print(f"  Clause parses completed   : {msummary['inscriptions_clause_parsed']}")

    # Show sample clause parses
    for sample in clause_samples[:5]:
        clauses = sample.get("clauses", [])
        types = [c["type"] for c in clauses]
        print(f"    [{sample.get('id', '?')}] → {types}")

    results["morphosyntax"] = {
        "verbal_chains": msummary["total_verbal_chains"],
        "unique_verb_roots": msummary["unique_verb_roots"],
        "suffix_types": msummary["suffix_types_attested"],
        "clause_parses": msummary["inscriptions_clause_parsed"],
    }

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 3: GENRE TEMPLATE ENGINE
    # ──────────────────────────────────────────────────────────────────────
    section("STAGE 3: GENRE TEMPLATE ENGINE")
    template_results = run_template_analysis()

    genre_dist = template_results["genre_distribution"]
    template_fits = template_results["template_fits"]
    restoration_demos = template_results["restoration_demos"]
    tsummary = template_results["summary"]

    print(f"  Inscriptions classified   : {tsummary['inscriptions_classified']}")
    print(f"  Genres identified         : {tsummary['genres_identified']}")
    print(f"  Dominant genre            : {tsummary['dominant_genre']}")
    print(f"  Genre distribution:")
    for g, n in sorted(genre_dist["distribution"].items(), key=lambda x: -x[1]):
        print(f"    {g:25s}: {n}")
    print(f"  Template fits computed    : {len(template_fits)}")
    print(f"  Restoration demos         : {len(restoration_demos)}")

    # Average match ratio from template fits
    if template_fits:
        avg_match = sum(f.get("match_ratio", 0) for f in template_fits) / len(template_fits)
        print(f"  Mean template match ratio : {avg_match:.3f}")
    else:
        avg_match = 0

    results["template_engine"] = {
        "classifications": genre_dist["distribution"],
        "template_fits": len(template_fits),
        "restorations": len(restoration_demos),
        "mean_match_ratio": round(avg_match, 3),
    }

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 4: CORPUS ANALYSIS & CONFIDENCE RECALCULATION
    # ──────────────────────────────────────────────────────────────────────
    section("STAGE 4: CORPUS ANALYSIS")
    corpus_analysis = run_corpus_analysis()

    conf_summary = corpus_analysis["confidence_updates"]["summary"]
    pred_summary = corpus_analysis["predictive_evaluation"]

    print(f"  Corpus size               : {corpus_analysis['summary']['corpus_size']}")
    print(f"  Confidence entries updated: {conf_summary['updated_entries']}")
    print(f"  Avg confidence delta      : {conf_summary['average_delta']:+.4f}")
    print(f"  Lexical coverage          : {pred_summary['average_coverage']:.3f}")
    print(f"  Known tokens              : {pred_summary['known_tokens']} / {pred_summary['total_tokens']} "
          f"({pred_summary['known_pct']}%)")
    print(f"  Unknown tokens            : {pred_summary['unknown_tokens']} "
          f"({pred_summary['unknown_pct']}%)")

    results["corpus_analysis"] = corpus_analysis["summary"]

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 5: FULL CORPUS TRANSLATION (original pipeline)
    # ──────────────────────────────────────────────────────────────────────
    section("STAGE 5: FULL CORPUS TRANSLATION")

    # Build lexicon
    builder = LexiconBuilder(VOCABULARY, MORPHEMES, comparative)
    lexicon = builder.build_full_lexicon(CORPUS)

    known = sum(1 for v in lexicon.values() if v.get("certainty", 0) >= 0.6)
    partial = sum(1 for v in lexicon.values() if 0.3 <= v.get("certainty", 0) < 0.6)
    unknown = sum(1 for v in lexicon.values() if v.get("certainty", 0) < 0.3)
    print(f"  Lexicon: {len(lexicon)} entries ({known} high, {partial} partial, {unknown} low)")

    # Run comparative engine
    comp_engine = create_comparative_engine(VOCABULARY, comparative, CORPUS)
    comp_results = comp_engine.run_full_analysis()
    likely_cognates = [c for c in comp_results["cognate_scores"] if c["is_likely_cognate"]]
    print(f"  Established cognates      : {len(likely_cognates)}")

    # Translate
    pipeline = create_translation_pipeline(
        VOCABULARY, MORPHEMES, comparative, CORPUS, SYNTACTIC_RULES
    )
    translations = pipeline.translate_corpus(CORPUS)

    # Score
    scorer = create_confidence_scorer(VOCABULARY, MORPHEMES, comparative, SYNTACTIC_RULES)
    corpus_scores = scorer.score_corpus(translations, CORPUS)

    print(f"  Translations completed    : {len(translations)}")
    print(f"  Average confidence        : {corpus_scores['average_score']:.3f}")
    print(f"  Grade distribution        : {corpus_scores['grade_distribution']}")

    results["translation"] = {
        "lexicon_size": len(lexicon),
        "established_cognates": len(likely_cognates),
        "translations": len(translations),
        "average_confidence": corpus_scores["average_score"],
        "grade_distribution": corpus_scores["grade_distribution"],
    }

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 6: TANYIDAMANI v3.0 — Re-decode with all new evidence
    # ──────────────────────────────────────────────────────────────────────
    section("STAGE 6: TANYIDAMANI STELE v3.0")

    from decipher.morphosyntax import VerbalChainAnalyzer, ClauseParser
    _vca = VerbalChainAnalyzer()
    _cp = ClauseParser()

    stele_results = []
    for sec in STELE_SECTIONS:
        tokens = [t.strip() for t in sec["text"].split(":") if t.strip()]

        # Genre for stele sections
        genre = "royal_stele"

        # Count verbal chains in this section's tokens
        chains = [_vca.parse_verbal_chain(t) for t in tokens
                  if _vca.parse_verbal_chain(t)["is_verbal"]]
        clause_parse = _cp.parse_inscription(sec["text"])
        clauses = clause_parse.get("clauses", [])

        # Build per-token annotations
        token_annotations = []
        for tok in tokens:
            base = tok.split("-")[0].lower()
            ventry = VOCABULARY.get(base, {})
            annotation = {
                "token": tok,
                "base": base,
                "translation": ventry.get("translation", "?"),
                "certainty": ventry.get("certainty", 0),
                "pos": ventry.get("pos", "UNK"),
            }
            token_annotations.append(annotation)

        avg_cert = (sum(a["certainty"] for a in token_annotations) /
                    len(token_annotations)) if token_annotations else 0

        stele_results.append({
            "section_id": sec["section"],
            "title": sec["title"],
            "genre": genre,
            "verbal_chains": len(chains),
            "clause_count": len(clauses),
            "token_count": len(tokens),
            "avg_certainty": round(avg_cert, 3),
            "annotations": token_annotations,
        })

    avg_stele = sum(s["avg_certainty"] for s in stele_results) / len(stele_results)
    print(f"  Stele sections analyzed   : {len(stele_results)}")
    print(f"  Average section certainty : {avg_stele:.3f}")
    for sr in stele_results:
        print(f"    {sr['section_id']:4s} | {sr['title'][:40]:40s} | "
              f"cert={sr['avg_certainty']:.3f} | chains={sr['verbal_chains']} "
              f"| clauses={sr['clause_count']}")

    results["tanyidamani_v3"] = {
        "sections": len(stele_results),
        "avg_certainty": round(avg_stele, 3),
        "section_summaries": [
            {"id": s["section_id"], "title": s["title"],
             "certainty": s["avg_certainty"], "genre": s["genre"]}
            for s in stele_results
        ],
    }

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 7: EXPORT
    # ──────────────────────────────────────────────────────────────────────
    section("STAGE 7: EXPORT")

    output = {
        "pipeline_version": "3.0",
        "stages": results,
        "summary": {
            "corpus_size": len(CORPUS),
            "lexicon_entries": len(lexicon),
            "new_cognates_mined": results["cognate_mining"]["new_cognates"],
            "verbal_chains_found": results["morphosyntax"]["verbal_chains"],
            "genre_classifications": results["template_engine"]["classifications"],
            "confidence_entries_updated": conf_summary["updated_entries"],
            "avg_translation_confidence": corpus_scores["average_score"],
            "stele_avg_certainty": round(avg_stele, 3),
        },
        "translations": [
            {
                "id": t.get("inscription_id", ""),
                "type": t.get("inscription_type", ""),
                "source": t.get("source", ""),
                "translation": t.get("free_translation", ""),
                "confidence": t.get("confidence", {}),
            }
            for t in translations
        ],
    }

    out_path = ROOT / "decipher" / "pipeline_v3_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Results saved to {out_path}")

    # Summary
    section("PIPELINE v3.0 SUMMARY")
    s = output["summary"]
    print(f"""
  Corpus inscriptions      : {s['corpus_size']}
  Lexicon entries           : {s['lexicon_entries']}
  New cognates mined        : {s['new_cognates_mined']}
  Verbal chains found       : {s['verbal_chains_found']}
  Confidence entries updated: {s['confidence_entries_updated']}
  Avg translation confidence: {s['avg_translation_confidence']:.3f}
  Tanyidamani avg certainty : {s['stele_avg_certainty']:.3f}
  Genre distribution        : {s['genre_classifications']}
""")

    return output


if __name__ == "__main__":
    run()
