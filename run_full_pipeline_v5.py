#!/usr/bin/env python3
"""
Meroitic Full Pipeline v5.0 — Bayesian Multi-Source Integration
================================================================

Builds on v4.0's five-strategy framework and adds four new analytical
engines that provide genuine computational advances:

  Inherited (v3.0 / v4.0):
    1. Cognate mining
    2. Morphosyntactic analysis
    3. Genre template engine
    4. Corpus analysis
    5. NES lexicon expansion
    6. Bilingual / parallel text anchoring
    7. Statistical cryptanalysis
    8. Brute-force segmentation

  New (v5.0):
    9. Distributional semantics — co-occurrence, PMI, semantic vectors
   10. Proto-NES → Meroitic reconstruction — comparative sound law engine
   11. Bayesian integration decoder — multi-source posterior inference
   12. New readings compilation — ranked proposals with evidence chains

  Final:
   13. Full corpus translation (enhanced lexicon)
   14. Tanyidamani stele re-decode
   15. Evidence fusion & statistics
   16. Export all v5 artefacts

Usage:
    python3 run_full_pipeline_v5.py
"""

import json
import sys
from pathlib import Path

# ── v3/v4 imports ─────────────────────────────────────────────────────────────
from decipher import (
    VOCABULARY, MORPHEMES, SYNTACTIC_RULES, CORPUS,
    NUBIAN_COMPARATIVE, EASTERN_SUDANIC_COMPARATIVE,
    KNOWN_ROYAL_NAMES, SITES,
)
from decipher.lexicon import LexiconBuilder
from decipher.comparative import create_comparative_engine
from decipher.translator import create_translation_pipeline
from decipher.confidence import create_confidence_scorer
from decipher.cognate_mining import run_cognate_mining
from decipher.morphosyntax import run_morphosyntactic_analysis
from decipher.template_engine import run_template_analysis
from decipher.corpus_ingestion import run_corpus_analysis
from decipher.tanyidamani_stele import STELE_SECTIONS

from decipher.nes_lexicon import run_nes_analysis
from decipher.bilingual_analysis import run_bilingual_analysis
from decipher.cryptanalysis import run_cryptanalysis
from decipher.brute_force import run_brute_force

# ── v5 imports ────────────────────────────────────────────────────────────────
from decipher.v5_distributional import DistributionalEngine
from decipher.v5_reconstruction import ReconstructionEngine
from decipher.v5_bayesian_decoder import BayesianDecoder
from decipher.v5_new_readings import NewReadingsCompiler

ROOT = Path(__file__).resolve().parent
DIVIDER = "=" * 72
THIN = "-" * 72


def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def run():
    print(DIVIDER)
    print("  MEROITIC DECIPHERMENT PIPELINE v5.0")
    print("  Bayesian Multi-Source Integration")
    print("  Distributional · Reconstruction · Bayesian · New Readings")
    print(DIVIDER)

    results = {}
    comparative = dict(NUBIAN_COMPARATIVE)
    comparative.update(EASTERN_SUDANIC_COMPARATIVE)

    # ══════════════════════════════════════════════════════════════════════
    # STAGES 1-4: v3.0 analytical modules
    # ══════════════════════════════════════════════════════════════════════

    # ── STAGE 1: COGNATE MINING ──
    section("STAGE 1: COGNATE MINING")
    cognate_results = run_cognate_mining()
    csummary = cognate_results["summary"]
    new_cognates = cognate_results["new_cognate_proposals"]
    print(f"  New cognate pairs mined   : {len(new_cognates)}")
    print(f"  Extended Nubian entries   : {csummary['extended_nubian_entries']}")
    print(f"  Extended ES entries       : {csummary['extended_es_entries']}")
    results["cognate_mining"] = {
        "new_cognates": len(new_cognates),
        "extended_nubian": csummary["extended_nubian_entries"],
        "extended_es": csummary["extended_es_entries"],
    }

    # ── STAGE 2: MORPHOSYNTAX ──
    section("STAGE 2: MORPHOSYNTACTIC ANALYSIS")
    morpho_results = run_morphosyntactic_analysis()
    msummary = morpho_results["summary"]
    print(f"  Verbal chains found       : {msummary['total_verbal_chains']}")
    print(f"  Unique verb roots         : {msummary['unique_verb_roots']}")
    print(f"  Suffix types attested     : {msummary['suffix_types_attested']}")
    results["morphosyntax"] = {
        "verbal_chains": msummary["total_verbal_chains"],
        "unique_verb_roots": msummary["unique_verb_roots"],
        "suffix_types": msummary["suffix_types_attested"],
    }

    # ── STAGE 3: TEMPLATE ENGINE ──
    section("STAGE 3: GENRE TEMPLATE ENGINE")
    template_results = run_template_analysis()
    tsummary = template_results["summary"]
    genre_dist = template_results["genre_distribution"]
    print(f"  Inscriptions classified   : {tsummary['inscriptions_classified']}")
    print(f"  Genres identified         : {tsummary['genres_identified']}")
    print(f"  Dominant genre            : {tsummary['dominant_genre']}")
    results["template_engine"] = {
        "classifications": genre_dist["distribution"],
        "genres": tsummary["genres_identified"],
    }

    # ── STAGE 4: CORPUS ANALYSIS ──
    section("STAGE 4: CORPUS ANALYSIS")
    corpus_analysis = run_corpus_analysis()
    conf_summary = corpus_analysis["confidence_updates"]["summary"]
    pred_summary = corpus_analysis["predictive_evaluation"]
    print(f"  Confidence entries updated: {conf_summary['updated_entries']}")
    print(f"  Avg confidence delta      : {conf_summary['average_delta']:+.4f}")
    print(f"  Lexical coverage          : {pred_summary['average_coverage']:.3f}")
    results["corpus_analysis"] = corpus_analysis["summary"]

    # ══════════════════════════════════════════════════════════════════════
    # STAGES 5-8: v4.0 strategies
    # ══════════════════════════════════════════════════════════════════════

    # ── STAGE 5: NES LEXICON ──
    section("STAGE 5: NES LEXICON EXPANSION")
    nes_results = run_nes_analysis()
    nes_summary = nes_results["summary"]
    print(f"  NES dictionary entries    : {nes_results['nes_dictionary_size']}")
    print(f"  Sound laws                : {nes_results['sound_laws_count']}")
    print(f"  High-conf proposals       : {nes_summary['high_confidence_proposals']}")
    print(f"  Medium-conf proposals     : {nes_summary['medium_confidence_proposals']}")
    total_new_nes = (nes_summary["high_confidence_proposals"]
                     + nes_summary["medium_confidence_proposals"])
    results["nes_lexicon"] = {
        "dictionary_entries": nes_results["nes_dictionary_size"],
        "new_cognates": total_new_nes,
        "verified": nes_summary["existing_cognates_verified"],
    }

    # ── STAGE 6: BILINGUAL ──
    section("STAGE 6: BILINGUAL & LOANWORD ANALYSIS")
    bilingual_results = run_bilingual_analysis()
    bsummary = bilingual_results["summary"]
    print(f"  Unique bilingual anchors  : {bsummary['unique_anchors']}")
    print(f"  Vocabulary boosted        : {bsummary['vocabulary_boosted']}")
    print(f"  New candidates            : {bsummary['new_candidates']}")
    print(f"  Egyptian loans            : {bsummary['egyptian_loans']}")
    results["bilingual_analysis"] = {
        "unique_anchors": bsummary["unique_anchors"],
        "vocabulary_boosted": bsummary["vocabulary_boosted"],
        "new_candidates": bsummary["new_candidates"],
        "egyptian_loans": bsummary["egyptian_loans"],
    }

    # ── STAGE 7: CRYPTANALYSIS ──
    section("STAGE 7: STATISTICAL CRYPTANALYSIS")
    crypto_results = run_cryptanalysis()
    crypto_summary = crypto_results["summary"]
    print(f"  Zipf exponent (alpha)     : {crypto_summary['zipf_exponent']}")
    print(f"  High-PMI collocations     : {crypto_summary['high_pmi_collocations']}")
    print(f"  Distributional inferences : {crypto_summary['distributional_inferences']}")
    print(f"  Cross-lingual alignments  : {crypto_summary['cross_lingual_alignments']}")
    results["cryptanalysis"] = {
        "zipf_exponent": crypto_summary["zipf_exponent"],
        "high_pmi": crypto_summary["high_pmi_collocations"],
        "distributional": crypto_summary["distributional_inferences"],
        "cross_lingual": crypto_summary["cross_lingual_alignments"],
    }

    # ── STAGE 8: BRUTE-FORCE ──
    section("STAGE 8: BRUTE-FORCE SEGMENTATION")
    brute_results = run_brute_force()
    bf_summary = brute_results["summary"]
    print(f"  Total unknown tokens      : {bf_summary['total_unknown_tokens']}")
    print(f"  Solved                    : {bf_summary['solved_count']}")
    print(f"  Partially solved          : {bf_summary['partially_solved_count']}")
    results["brute_force"] = {
        "total_unknowns": bf_summary["total_unknown_tokens"],
        "solved": bf_summary["solved_count"],
        "partially_solved": bf_summary["partially_solved_count"],
    }

    # ══════════════════════════════════════════════════════════════════════
    # STAGES 9-12: v5.0 NEW ENGINES
    # ══════════════════════════════════════════════════════════════════════

    # ── STAGE 9: DISTRIBUTIONAL SEMANTICS ──
    section("STAGE 9: DISTRIBUTIONAL SEMANTICS (v5)")
    dist_engine = DistributionalEngine()
    dist_results = dist_engine.run_full_analysis()
    print(f"  Unique tokens analyzed    : {dist_results['unique_roots']}")
    print(f"  Known / unknown tokens    : {dist_results['known_tokens']} / {dist_results['unknown_tokens']}")
    print(f"  Meaning proposals         : {dist_results['proposal_count']}")
    print(f"  Semantic clusters         : {len(dist_results.get('semantic_clusters', {}))}")
    print(f"  High-PMI collocations v5  : {len(dist_results.get('collocations', []))}")
    for p in dist_results.get('meaning_proposals', [])[:5]:
        print(f"    {p.get('token',''):15s} → [{p.get('proposed_field','')}] "
              f"(conf={p.get('confidence',0):.3f})")
    results["distributional"] = {
        "unique_tokens": dist_results["unique_roots"],
        "known_tokens": dist_results["known_tokens"],
        "unknown_tokens": dist_results["unknown_tokens"],
        "meaning_proposals": dist_results["proposal_count"],
        "clusters": len(dist_results.get("semantic_clusters", {})),
    }

    # ── STAGE 10: PROTO-NES RECONSTRUCTION ──
    section("STAGE 10: PROTO-NES → MEROITIC RECONSTRUCTION (v5)")
    recon_engine = ReconstructionEngine()
    recon_results = recon_engine.run_full_analysis()
    vocab_scan = recon_results.get('vocabulary_scan', {})
    print(f"  Proto-NES entries tested  : {recon_results['total_nes_entries']}")
    print(f"  Corpus roots scanned      : {recon_results['corpus_roots']}")
    print(f"  Total matches found       : {recon_results['total_matches']}")
    print(f"  New proposals             : {recon_results['new_proposals']}")
    print(f"  Confirmations             : {recon_results['confirmations']}")
    print(f"  Vocabulary scan proposals : {vocab_scan.get('total_proposals', 0)}")
    for p in recon_results.get('new_proposal_details', [])[:5]:
        print(f"    {p.get('predicted_meroitic',''):15s} → '{p.get('proto_meaning','')}' "
              f"(conf={p.get('confidence',0):.3f})")
    results["reconstruction"] = {
        "proto_entries_tested": recon_results["total_nes_entries"],
        "predictions_generated": recon_results["total_matches"],
        "corpus_matches": recon_results["new_proposals"],
        "new_proposals": vocab_scan.get("total_proposals", 0),
    }

    # ── STAGE 11: BAYESIAN INTEGRATION ──
    section("STAGE 11: BAYESIAN INTEGRATION DECODER (v5)")
    bayes_decoder = BayesianDecoder(
        distributional_results=dist_results,
        reconstruction_results=recon_results,
    )
    bayes_results = bayes_decoder.run_full_analysis()
    bayes_stats = bayes_results["corpus_statistics"]
    print(f"  Inscriptions decoded      : {bayes_results['decoded_inscriptions']}")
    print(f"  Total tokens              : {bayes_stats['total_tokens']}")
    print(f"  Average posterior          : {bayes_stats['average_posterior']:.4f}")
    print(f"  Breakthroughs             : {bayes_results['breakthrough_count']}")
    print(f"    New readings            : {len(bayes_results['new_readings'])}")
    print(f"    Improved readings       : {len(bayes_results['improved_readings'])}")
    print(f"  Source distribution:")
    for src, count in sorted(bayes_stats['source_distribution'].items()):
        print(f"    {src:20s}: {count}")
    for b in bayes_results.get('new_readings', [])[:5]:
        print(f"    NEW: {b['root']:15s} = {b['new_meaning']:20s} "
              f"(posterior={b['posterior']:.3f})")
    results["bayesian"] = {
        "inscriptions": bayes_results["decoded_inscriptions"],
        "tokens": bayes_stats["total_tokens"],
        "avg_posterior": bayes_stats["average_posterior"],
        "breakthroughs": bayes_results["breakthrough_count"],
        "new_readings": len(bayes_results["new_readings"]),
        "improved_readings": len(bayes_results["improved_readings"]),
    }

    # ── STAGE 12: NEW READINGS COMPILATION ──
    section("STAGE 12: NEW READINGS COMPILATION (v5)")
    compiler = NewReadingsCompiler(
        distributional_results=dist_results,
        reconstruction_results=recon_results,
        bayesian_results=bayes_results,
    )
    readings_results = compiler.run_full_analysis()
    readings_stats = readings_results["statistics"]
    print(f"  Established vocabulary    : {readings_stats['established_vocabulary']}")
    print(f"  New proposals             : {readings_stats['new_proposals_total']}")
    print(f"  Enhanced lexicon size     : {readings_stats['enhanced_lexicon_size']}")
    print(f"  Vocabulary increase       : +{readings_stats['vocabulary_increase']}")
    print(f"  Corpus coverage           : {readings_stats['corpus_coverage']:.1%}")
    print(f"  By tier:")
    for tier, count in sorted(readings_stats.get('new_by_tier', {}).items()):
        print(f"    {tier:15s}: {count}")
    for p in readings_results.get('top_proposals', [])[:5]:
        print(f"    {p['root']:15s} = {p['best_meaning']:20s} "
              f"[{p['tier']}] conf={p['combined_confidence']:.3f}")
    results["new_readings"] = {
        "proposals": readings_stats["new_proposals_total"],
        "enhanced_lexicon_size": readings_stats["enhanced_lexicon_size"],
        "vocabulary_increase": readings_stats["vocabulary_increase"],
        "corpus_coverage": readings_stats["corpus_coverage"],
        "by_tier": readings_stats.get("new_by_tier", {}),
    }

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 13: FULL CORPUS TRANSLATION (with v5 enhanced lexicon)
    # ══════════════════════════════════════════════════════════════════════
    section("STAGE 13: FULL CORPUS TRANSLATION (enhanced)")

    builder = LexiconBuilder(VOCABULARY, MORPHEMES, comparative)
    lexicon = builder.build_full_lexicon(CORPUS)
    known = sum(1 for v in lexicon.values() if v.get("certainty", 0) >= 0.6)
    partial = sum(1 for v in lexicon.values() if 0.3 <= v.get("certainty", 0) < 0.6)
    unknown = sum(1 for v in lexicon.values() if v.get("certainty", 0) < 0.3)
    print(f"  Lexicon: {len(lexicon)} entries ({known} high, {partial} partial, {unknown} low)")

    comp_engine = create_comparative_engine(VOCABULARY, comparative, CORPUS)
    comp_results_trans = comp_engine.run_full_analysis()
    likely_cognates = [c for c in comp_results_trans["cognate_scores"]
                       if c["is_likely_cognate"]]
    print(f"  Established cognates      : {len(likely_cognates)}")

    pipeline = create_translation_pipeline(
        VOCABULARY, MORPHEMES, comparative, CORPUS, SYNTACTIC_RULES
    )
    translations = pipeline.translate_corpus(CORPUS)

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

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 14: TANYIDAMANI STELE RE-DECODE
    # ══════════════════════════════════════════════════════════════════════
    section("STAGE 14: TANYIDAMANI STELE (v5 re-decode)")

    from decipher.morphosyntax import VerbalChainAnalyzer, ClauseParser
    _vca = VerbalChainAnalyzer()
    _cp = ClauseParser()

    stele_results_list = []
    for sec in STELE_SECTIONS:
        tokens = [t.strip() for t in sec["text"].split(":") if t.strip()]
        chains = [_vca.parse_verbal_chain(t) for t in tokens
                  if _vca.parse_verbal_chain(t)["is_verbal"]]
        clause_parse = _cp.parse_inscription(sec["text"])
        clauses = clause_parse.get("clauses", [])

        token_annotations = []
        for tok in tokens:
            base = tok.split("-")[0].lower()
            # Check enhanced lexicon from v5
            enhanced_lex = readings_results.get("enhanced_lexicon", {})
            if base in enhanced_lex:
                entry = enhanced_lex[base]
                token_annotations.append({
                    "token": tok,
                    "base": base,
                    "translation": entry.get("translation", "?"),
                    "certainty": entry.get("certainty", 0),
                    "tier": entry.get("tier", "UNKNOWN"),
                })
            elif base in VOCABULARY:
                ventry = VOCABULARY[base]
                token_annotations.append({
                    "token": tok,
                    "base": base,
                    "translation": ventry.get("translation", "?"),
                    "certainty": ventry.get("certainty", 0),
                    "tier": "ESTABLISHED" if ventry.get("certainty", 0) >= 0.7 else "PROPOSED",
                })
            else:
                token_annotations.append({
                    "token": tok,
                    "base": base,
                    "translation": "?",
                    "certainty": 0.0,
                    "tier": "UNKNOWN",
                })

        avg_cert = (sum(a["certainty"] for a in token_annotations) /
                    len(token_annotations)) if token_annotations else 0

        stele_results_list.append({
            "section_id": sec["section"],
            "title": sec["title"],
            "verbal_chains": len(chains),
            "clause_count": len(clauses),
            "token_count": len(tokens),
            "annotations": token_annotations,
            "avg_certainty": round(avg_cert, 3),
        })

    avg_stele = (sum(s["avg_certainty"] for s in stele_results_list) /
                 len(stele_results_list)) if stele_results_list else 0
    print(f"  Stele sections analyzed   : {len(stele_results_list)}")
    print(f"  Average section certainty : {avg_stele:.3f}")
    for sr in stele_results_list:
        print(f"    {sr['section_id']:4s} | {sr['title'][:40]:40s} | "
              f"cert={sr['avg_certainty']:.3f}")

    results["tanyidamani_v5"] = {
        "sections": len(stele_results_list),
        "avg_certainty": round(avg_stele, 3),
    }

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 15: EVIDENCE FUSION & STATISTICS
    # ══════════════════════════════════════════════════════════════════════
    section("STAGE 15: EVIDENCE FUSION & STATISTICS")

    total_v4_evidence = (
        results["nes_lexicon"]["new_cognates"]
        + results["bilingual_analysis"]["new_candidates"]
        + results["brute_force"]["solved"]
        + results["cryptanalysis"]["distributional"]
        + results["cryptanalysis"]["cross_lingual"]
    )
    total_v5_evidence = (
        results["distributional"]["meaning_proposals"]
        + results["reconstruction"]["new_proposals"]
        + results["bayesian"]["breakthroughs"]
        + results["new_readings"]["proposals"]
    )
    print(f"  v4 evidence items         : {total_v4_evidence}")
    print(f"  v5 evidence items         : {total_v5_evidence}")
    print(f"  Total evidence items      : {total_v4_evidence + total_v5_evidence}")
    print(f"  Enhanced vocabulary size   : {results['new_readings']['enhanced_lexicon_size']}")
    print(f"  Corpus coverage            : {results['new_readings']['corpus_coverage']:.1%}")

    results["evidence_fusion"] = {
        "v4_evidence": total_v4_evidence,
        "v5_evidence": total_v5_evidence,
        "total_evidence": total_v4_evidence + total_v5_evidence,
    }

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 16: EXPORT
    # ══════════════════════════════════════════════════════════════════════
    section("STAGE 16: EXPORT v5 ARTEFACTS")

    # Bayesian top translations
    bayes_top = []
    for r in bayes_results.get("full_results", [])[:66]:
        bayes_top.append({
            "id": r.get("id", ""),
            "site": r.get("site", ""),
            "type": r.get("type", ""),
            "period": r.get("period", ""),
            "token_count": r.get("token_count", 0),
            "average_posterior": r.get("average_posterior", 0),
            "free_translation": r.get("free_translation", ""),
            "decodings": [
                {
                    "token": d["token"],
                    "meaning": d["best_meaning"],
                    "posterior": d["best_posterior"],
                    "source": d["source"],
                }
                for d in r.get("decodings", [])
            ],
        })

    # New readings export
    proposals_export = []
    for p in readings_results.get("proposals", []):
        proposals_export.append({
            "root": p["root"],
            "meaning": p["best_meaning"],
            "confidence": p["combined_confidence"],
            "tier": p["tier"],
            "sources": p["sources"],
            "attestation_count": p["attestation_count"],
            "evidence": [
                {"meaning": e["meaning"], "source": e["source"],
                 "confidence": e["confidence"], "evidence": e["evidence"]}
                for e in p.get("evidence_chain", [])
            ],
        })

    output = {
        "pipeline_version": "5.0",
        "method": "Bayesian Multi-Source Integration",
        "stages": results,
        "summary": {
            "corpus_size": len(CORPUS),
            "lexicon_entries": len(lexicon),
            "enhanced_lexicon_entries": results["new_readings"]["enhanced_lexicon_size"],
            "vocabulary_increase": results["new_readings"]["vocabulary_increase"],
            "corpus_coverage": results["new_readings"]["corpus_coverage"],
            "v5_breakthroughs": results["bayesian"]["breakthroughs"],
            "new_readings_proposed": results["new_readings"]["proposals"],
            "distributional_proposals": results["distributional"]["meaning_proposals"],
            "reconstruction_proposals": results["reconstruction"]["new_proposals"],
            "avg_translation_confidence": corpus_scores["average_score"],
            "avg_bayesian_posterior": results["bayesian"]["avg_posterior"],
            "stele_avg_certainty": round(avg_stele, 3),
            "total_evidence_items": total_v4_evidence + total_v5_evidence,
        },
        "bayesian_translations": bayes_top,
        "new_vocabulary_proposals": proposals_export,
        "stele_sections": [
            {
                "section_id": s["section_id"],
                "title": s["title"],
                "token_count": s["token_count"],
                "avg_certainty": s["avg_certainty"],
                "annotations": s["annotations"],
            }
            for s in stele_results_list
        ],
        "traditional_translations": [
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

    out_path = ROOT / "decipher" / "pipeline_v5_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Results saved to {out_path}")

    # ══════════════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    section("PIPELINE v5.0 — FINAL SUMMARY")
    s = output["summary"]
    print(f"""
  ┌─────────────────────────────────────────────────────┐
  │  MEROITIC DECIPHERMENT v5.0 — RESULTS               │
  ├─────────────────────────────────────────────────────┤
  │  Corpus inscriptions        : {s['corpus_size']:>6}              │
  │  Base lexicon entries       : {s['lexicon_entries']:>6}              │
  │  Enhanced lexicon entries   : {s['enhanced_lexicon_entries']:>6}              │
  │  Vocabulary increase        : +{s['vocabulary_increase']:<5}              │
  │  Corpus coverage            : {s['corpus_coverage']:.1%}             │
  ├─────────────────────────────────────────────────────┤
  │  v5 Breakthroughs           : {s['v5_breakthroughs']:>6}              │
  │   - New readings proposed   : {s['new_readings_proposed']:>6}              │
  │   - Distributional          : {s['distributional_proposals']:>6}              │
  │   - Reconstruction          : {s['reconstruction_proposals']:>6}              │
  ├─────────────────────────────────────────────────────┤
  │  Avg translation confidence : {s['avg_translation_confidence']:.3f}              │
  │  Avg Bayesian posterior     : {s['avg_bayesian_posterior']:.4f}             │
  │  Tanyidamani avg certainty  : {s['stele_avg_certainty']:.3f}              │
  │  Total evidence items       : {s['total_evidence_items']:>6}              │
  └─────────────────────────────────────────────────────┘
""")

    return output


if __name__ == "__main__":
    run()
