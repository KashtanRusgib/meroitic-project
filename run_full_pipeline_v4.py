#!/usr/bin/env python3
"""
Meroitic Full Pipeline v4.0 — Five-Strategy Integration Runner
===============================================================
Orchestrates ALL v3.0 modules PLUS the five new decipherment strategies:

  Inherited (v3.0):
    1. Cognate mining → Expanded Nilo-Saharan lexicon
    2. Morphosyntactic → Verbal chains, suffix mapping, clause parsing
    3. Template engine → Genre classification, lacuna restoration
    4. Corpus analysis → Confidence recalculation, predictive evaluation
    5. Full translation → 6-stage pipeline
    6. Tanyidamani stele → REM 1044 re-decode

  New (v4.0):
    7. NES Lexicon expansion → 130-entry comparative dictionary + cognate engine
    8. Bilingual/parallel text anchoring → Philae, Dakka, Nastasen bilinguals
    9. Statistical cryptanalysis → Zipf, PMI, Bayesian morphology, distributional
   10. Brute-force segmentation → Exhaustive solve of unknown tokens

  Final:
   11. Evidence fusion & confidence recalc
   12. Export v4 artefacts

Usage:
    python3 run_full_pipeline_v4.py
"""

import json
import sys
from pathlib import Path

# ── v3 imports ────────────────────────────────────────────────────────────────
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

# ── v4 imports ────────────────────────────────────────────────────────────────
from decipher.nes_lexicon import run_nes_analysis
from decipher.bilingual_analysis import run_bilingual_analysis
from decipher.cryptanalysis import run_cryptanalysis
from decipher.brute_force import run_brute_force

ROOT = Path(__file__).resolve().parent
DIVIDER = "=" * 72
THIN = "-" * 72


def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def run():
    print(DIVIDER)
    print("  MEROITIC DECIPHERMENT PIPELINE v4.0")
    print("  Five-strategy integration: NES · bilingual · crypto · brute-force")
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
    # STAGES 5-8: v4.0 FIVE NEW STRATEGIES
    # ══════════════════════════════════════════════════════════════════════

    # ── STAGE 5: NES LEXICON EXPANSION (Strategy 1) ──
    section("STAGE 5: NES LEXICON EXPANSION (Strategy 1)")
    nes_results = run_nes_analysis()
    nes_summary = nes_results["summary"]
    print(f"  NES dictionary entries    : {nes_results['nes_dictionary_size']}")
    print(f"  Sound laws                : {nes_results['sound_laws_count']}")
    print(f"  Unknown tokens scanned    : {nes_summary['low_confidence_roots_scanned']}")
    print(f"  High-confidence proposals : {nes_summary['high_confidence_proposals']}")
    print(f"  Medium-confidence proposals: {nes_summary['medium_confidence_proposals']}")
    print(f"  Existing verified         : {nes_summary['existing_cognates_verified']}")
    print(f"  Verification rate         : {nes_summary['verification_rate']:.0%}")

    # Display top NES cognate proposals
    for mer, match in list(nes_results.get("high_confidence_new", {}).items())[:8]:
        print(f"    {mer:15s} → '{match.get('nes_gloss', '?')}' "
              f"[{match.get('combined_score', 0):.3f}]")

    total_new_nes = (nes_summary["high_confidence_proposals"]
                     + nes_summary["medium_confidence_proposals"])
    results["nes_lexicon"] = {
        "dictionary_entries": nes_results["nes_dictionary_size"],
        "sound_laws": nes_results["sound_laws_count"],
        "new_cognates": total_new_nes,
        "verified": nes_summary["existing_cognates_verified"],
    }

    # ── STAGE 6: BILINGUAL / PARALLEL TEXT ANCHORING (Strategy 2+3) ──
    section("STAGE 6: BILINGUAL & LOANWORD ANALYSIS (Strategy 2+3)")
    bilingual_results = run_bilingual_analysis()
    bsummary = bilingual_results["summary"]
    print(f"  Unique bilingual anchors  : {bsummary['unique_anchors']}")
    print(f"  Source attestations        : {bsummary['source_attestations']}")
    print(f"  Vocabulary entries boosted : {bsummary['vocabulary_boosted']}")
    print(f"  New translation candidates: {bsummary['new_candidates']}")
    print(f"  Egyptian loans identified : {bsummary['egyptian_loans']}")
    print(f"  Native NES words          : {bsummary['native_nes']}")
    print(f"  Meroitic → ON exports     : {bsummary['meroitic_exports']}")

    # Show new translation candidates
    for cand in bilingual_results.get("new_translation_candidates", [])[:5]:
        print(f"    {cand['meroitic']:15s} → '{cand['proposed_meaning']}' "
              f"[bilingual={cand['bilingual_certainty']:.2f}, "
              f"current={cand['current_certainty']:.2f}]")

    results["bilingual_analysis"] = {
        "unique_anchors": bsummary["unique_anchors"],
        "vocabulary_boosted": bsummary["vocabulary_boosted"],
        "new_candidates": bsummary["new_candidates"],
        "egyptian_loans": bsummary["egyptian_loans"],
        "native_nes": bsummary["native_nes"],
        "meroitic_exports": bsummary["meroitic_exports"],
    }

    # ── STAGE 7: STATISTICAL CRYPTANALYSIS (Strategy 4) ──
    section("STAGE 7: STATISTICAL CRYPTANALYSIS (Strategy 4)")
    crypto_results = run_cryptanalysis()
    crypto_summary = crypto_results["summary"]
    print(f"  Zipf exponent (α)         : {crypto_summary['zipf_exponent']}")
    print(f"  Unique tokens in corpus   : {crypto_summary['unique_tokens_in_corpus']}")
    print(f"  High-PMI collocations     : {crypto_summary['high_pmi_collocations']}")
    print(f"  Morphological analyses    : {crypto_summary['morphological_analyses']}")
    print(f"  Distributional inferences : {crypto_summary['distributional_inferences']}")
    print(f"  Cross-lingual alignments  : {crypto_summary['cross_lingual_alignments']}")

    # Show top PMI collocations
    pmi_pairs = crypto_results.get("transitional_probabilities", {}).get(
        "high_pmi_collocations", []
    )
    for pair in pmi_pairs[:5]:
        w1, w2 = pair["pair"]
        print(f"    {w1} + {w2}: PMI={pair['pmi']:.2f} (count={pair['count']})")

    results["cryptanalysis"] = {
        "zipf_exponent": crypto_summary["zipf_exponent"],
        "unique_tokens": crypto_summary["unique_tokens_in_corpus"],
        "high_pmi": crypto_summary["high_pmi_collocations"],
        "morphological": crypto_summary["morphological_analyses"],
        "distributional": crypto_summary["distributional_inferences"],
        "cross_lingual": crypto_summary["cross_lingual_alignments"],
    }

    # ── STAGE 8: BRUTE-FORCE COMBINATION LOCK (Strategy 5) ──
    section("STAGE 8: BRUTE-FORCE COMBINATION LOCK (Strategy 5)")
    brute_results = run_brute_force()
    bf_summary = brute_results["summary"]
    print(f"  Total unknown tokens      : {bf_summary['total_unknown_tokens']}")
    print(f"  Solved (root known)       : {bf_summary['solved_count']}")
    print(f"  Partially solved          : {bf_summary['partially_solved_count']}")
    print(f"  Unsolved                  : {bf_summary['unsolved_count']}")

    # Show top solutions
    for sol in brute_results.get("solved", [])[:8]:
        best = sol["best_solution"]
        print(f"    {best['token']:15s} → [{best.get('prefix', '') or ''}]"
              f"{best['root']}[{'+'.join(best['suffixes']) or '-'}] "
              f"'{best.get('root_meaning', '?')}' "
              f"[score={best['score']:.3f}]")

    results["brute_force"] = {
        "total_unknowns": bf_summary["total_unknown_tokens"],
        "solved": bf_summary["solved_count"],
        "partially_solved": bf_summary["partially_solved_count"],
        "unsolved": bf_summary["unsolved_count"],
    }

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 9: FULL CORPUS TRANSLATION (with all v4 evidence)
    # ══════════════════════════════════════════════════════════════════════
    section("STAGE 9: FULL CORPUS TRANSLATION")

    builder = LexiconBuilder(VOCABULARY, MORPHEMES, comparative)
    lexicon = builder.build_full_lexicon(CORPUS)
    known = sum(1 for v in lexicon.values() if v.get("certainty", 0) >= 0.6)
    partial = sum(1 for v in lexicon.values() if 0.3 <= v.get("certainty", 0) < 0.6)
    unknown = sum(1 for v in lexicon.values() if v.get("certainty", 0) < 0.3)
    print(f"  Lexicon: {len(lexicon)} entries ({known} high, {partial} partial, {unknown} low)")

    comp_engine = create_comparative_engine(VOCABULARY, comparative, CORPUS)
    comp_results = comp_engine.run_full_analysis()
    likely_cognates = [c for c in comp_results["cognate_scores"] if c["is_likely_cognate"]]
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
    # STAGE 10: TANYIDAMANI v4.0
    # ══════════════════════════════════════════════════════════════════════
    section("STAGE 10: TANYIDAMANI STELE v4.0")

    from decipher.morphosyntax import VerbalChainAnalyzer, ClauseParser
    _vca = VerbalChainAnalyzer()
    _cp = ClauseParser()

    stele_results = []
    for sec in STELE_SECTIONS:
        tokens = [t.strip() for t in sec["text"].split(":") if t.strip()]
        chains = [_vca.parse_verbal_chain(t) for t in tokens
                  if _vca.parse_verbal_chain(t)["is_verbal"]]
        clause_parse = _cp.parse_inscription(sec["text"])
        clauses = clause_parse.get("clauses", [])

        token_annotations = []
        for tok in tokens:
            base = tok.split("-")[0].lower()
            ventry = VOCABULARY.get(base, {})
            token_annotations.append({
                "token": tok,
                "base": base,
                "translation": ventry.get("translation", "?"),
                "certainty": ventry.get("certainty", 0),
            })

        avg_cert = (sum(a["certainty"] for a in token_annotations) /
                    len(token_annotations)) if token_annotations else 0

        stele_results.append({
            "section_id": sec["section"],
            "title": sec["title"],
            "verbal_chains": len(chains),
            "clause_count": len(clauses),
            "token_count": len(tokens),
            "avg_certainty": round(avg_cert, 3),
        })

    avg_stele = sum(s["avg_certainty"] for s in stele_results) / len(stele_results)
    print(f"  Stele sections analyzed   : {len(stele_results)}")
    print(f"  Average section certainty : {avg_stele:.3f}")
    for sr in stele_results:
        print(f"    {sr['section_id']:4s} | {sr['title'][:40]:40s} | "
              f"cert={sr['avg_certainty']:.3f}")

    results["tanyidamani_v4"] = {
        "sections": len(stele_results),
        "avg_certainty": round(avg_stele, 3),
    }

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 11: EVIDENCE FUSION SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    section("STAGE 11: EVIDENCE FUSION SUMMARY")

    total_new_evidence = (
        results["nes_lexicon"]["new_cognates"]
        + results["bilingual_analysis"]["new_candidates"]
        + results["brute_force"]["solved"]
        + results["cryptanalysis"]["distributional"]
        + results["cryptanalysis"]["cross_lingual"]
    )
    print(f"  Total new evidence items  : {total_new_evidence}")
    print(f"  NES cognate proposals     : {results['nes_lexicon']['new_cognates']}")
    print(f"  Bilingual new candidates  : {results['bilingual_analysis']['new_candidates']}")
    print(f"  Brute-force solved tokens : {results['brute_force']['solved']}")
    print(f"  Distributional inferences : {results['cryptanalysis']['distributional']}")
    print(f"  Cross-lingual alignments  : {results['cryptanalysis']['cross_lingual']}")

    results["evidence_fusion"] = {
        "total_new_evidence": total_new_evidence,
    }

    # ══════════════════════════════════════════════════════════════════════
    # STAGE 12: EXPORT
    # ══════════════════════════════════════════════════════════════════════
    section("STAGE 12: EXPORT")

    output = {
        "pipeline_version": "4.0",
        "stages": results,
        "summary": {
            "corpus_size": len(CORPUS),
            "lexicon_entries": len(lexicon),
            "new_cognates_mined_v3": results["cognate_mining"]["new_cognates"],
            "nes_new_cognates_v4": results["nes_lexicon"]["new_cognates"],
            "bilingual_anchors": results["bilingual_analysis"]["unique_anchors"],
            "zipf_exponent": results["cryptanalysis"]["zipf_exponent"],
            "brute_force_solved": results["brute_force"]["solved"],
            "total_new_evidence": total_new_evidence,
            "verbal_chains_found": results["morphosyntax"]["verbal_chains"],
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

    out_path = ROOT / "decipher" / "pipeline_v4_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Results saved to {out_path}")

    # ══════════════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    section("PIPELINE v4.0 — FINAL SUMMARY")
    s = output["summary"]
    print(f"""
  Corpus inscriptions        : {s['corpus_size']}
  Lexicon entries            : {s['lexicon_entries']}
  v3 cognates mined          : {s['new_cognates_mined_v3']}
  v4 NES cognates proposed   : {s['nes_new_cognates_v4']}
  Bilingual anchors          : {s['bilingual_anchors']}
  Zipf exponent (α)          : {s['zipf_exponent']}
  Brute-force solved         : {s['brute_force_solved']}
  Total new evidence items   : {s['total_new_evidence']}
  Verbal chains found        : {s['verbal_chains_found']}
  Avg translation confidence : {s['avg_translation_confidence']:.3f}
  Tanyidamani avg certainty  : {s['stele_avg_certainty']:.3f}
""")

    return output


if __name__ == "__main__":
    run()
