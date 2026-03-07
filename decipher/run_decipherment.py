#!/usr/bin/env python3
"""
Meroitic Full Decipherment Runner
====================================
Runs the entire decipherment pipeline end-to-end:

  1. Loads the comprehensive knowledge base
  2. Builds the expanded lexicon
  3. Runs comparative linguistics analysis
  4. Translates the full corpus
  5. Scores all translations
  6. Prints a detailed report
"""

import json
import sys

from decipher import (
    VOCABULARY, MORPHEMES, SYNTACTIC_RULES, CORPUS,
    NUBIAN_COMPARATIVE, EASTERN_SUDANIC_COMPARATIVE,
    KNOWN_ROYAL_NAMES, SITES,
)
from decipher.grammar import (
    create_parser, create_phrase_analyzer,
    create_template_matcher, create_word_order_analyzer,
)
from decipher.lexicon import LexiconBuilder
from decipher.comparative import create_comparative_engine
from decipher.translator import create_translation_pipeline
from decipher.confidence import create_confidence_scorer


DIVIDER = "=" * 72
THIN = "-" * 72


def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def run():
    # Merge comparative data
    comparative = dict(NUBIAN_COMPARATIVE)
    comparative.update(EASTERN_SUDANIC_COMPARATIVE)

    # ----------------------------------------------------------------
    # Stage 1: Lexicon Construction
    # ----------------------------------------------------------------
    section("STAGE 1: LEXICON CONSTRUCTION")
    builder = LexiconBuilder(VOCABULARY, MORPHEMES, comparative)
    lexicon = builder.build_full_lexicon(CORPUS)

    known = sum(1 for v in lexicon.values() if v.get("certainty", 0) >= 0.6)
    partial = sum(1 for v in lexicon.values() if 0.3 <= v.get("certainty", 0) < 0.6)
    unknown = sum(1 for v in lexicon.values() if v.get("certainty", 0) < 0.3)

    print(f"  Total lexicon entries : {len(lexicon)}")
    print(f"  High confidence (≥0.6): {known}")
    print(f"  Partial (0.3–0.6)     : {partial}")
    print(f"  Low / unknown (<0.3)  : {unknown}")

    print(f"\n  Top 25 highest-confidence entries:")
    top = sorted(lexicon.items(), key=lambda x: -x[1].get("certainty", 0))[:25]
    for word, entry in top:
        print(f"    {word:20s} → {entry.get('translation', '?'):30s} "
              f"[{entry.get('certainty', 0):.2f}] ({entry.get('source', '')})")

    # ----------------------------------------------------------------
    # Stage 2: Comparative Linguistics
    # ----------------------------------------------------------------
    section("STAGE 2: COMPARATIVE LINGUISTICS")
    comp_engine = create_comparative_engine(VOCABULARY, comparative, CORPUS)
    comp_results = comp_engine.run_full_analysis()

    # Cognate scores
    cognates = comp_results["cognate_scores"]
    print(f"  Cognate pairs tested: {len(cognates)}")
    likely = [c for c in cognates if c["is_likely_cognate"]]
    print(f"  Likely cognates     : {len(likely)}")
    if cognates:
        avg = sum(c["cognate_score"] for c in cognates) / len(cognates)
        print(f"  Average score       : {avg:.3f}")

    print(f"\n  Top 10 cognate pairs:")
    for c in cognates[:10]:
        sym = "✓" if c["is_likely_cognate"] else "✗"
        print(f"    {sym} {c['meroitic']:12s} ↔ {c['nubian']:15s}  "
              f"score={c['cognate_score']:.3f}  ({c.get('meaning', '')})")

    # Proto-forms
    protos = comp_results["proto_forms"]
    print(f"\n  Reconstructed proto-forms: {len(protos)}")
    for pf in protos[:10]:
        print(f"    {pf.get('word', ''):12s} → {pf.get('proto', ''):15s}  "
              f"'{pf.get('meaning', '')}' (conf={pf.get('confidence', 0):.2f})")

    # Relationship summary
    rel = comp_results["relationship_summary"]
    print(f"\n  Language relationship: {rel.get('relationship_strength', '?')}")
    print(f"  {rel.get('conclusion', '')}")

    # ----------------------------------------------------------------
    # Stage 3: Grammar Analysis
    # ----------------------------------------------------------------
    section("STAGE 3: GRAMMAR ANALYSIS")
    parser = create_parser(VOCABULARY, MORPHEMES, KNOWN_ROYAL_NAMES)
    word_order = create_word_order_analyzer()

    # Feed corpus through parser
    all_parsed = []
    for insc in CORPUS:
        tokens = [t.strip() for t in insc["text"].split(":") if t.strip()]
        parsed = [parser.parse_token(tok) for tok in tokens]
        all_parsed.extend(parsed)

    pos_counts = {}
    for p in all_parsed:
        pos = p.get("pos", "UNK")
        pos_counts[pos] = pos_counts.get(pos, 0) + 1

    print(f"  Tokens parsed: {len(all_parsed)}")
    print(f"  POS distribution:")
    for pos, count in sorted(pos_counts.items(), key=lambda x: -x[1]):
        print(f"    {pos:20s}: {count}")

    wo = word_order.analyze_word_order(CORPUS, parser)
    avg_pos = wo.get("average_positions", {})
    # Infer SOV by checking if VERB appears later than NOUN
    verb_pos = avg_pos.get("VERB", {}).get("mean", 0.5)
    noun_pos = avg_pos.get("NOUN", {}).get("mean", 0.5)
    sov_conf = max(0, verb_pos - noun_pos) * 2  # higher if verb is sentence-final
    order = "SOV" if sov_conf > 0.1 else "uncertain"
    print(f"\n  Word order hypothesis: {order}")
    print(f"  SOV confidence       : {sov_conf:.2f}")
    print(f"  Average POS positions:")
    for pos, info in sorted(avg_pos.items(), key=lambda x: x[1]["mean"]):
        print(f"    {pos:20s}: mean={info['mean']:.3f}  (n={info['count']})")

    # ----------------------------------------------------------------
    # Stage 4: Full Translation
    # ----------------------------------------------------------------
    section("STAGE 4: FULL CORPUS TRANSLATION")
    pipeline = create_translation_pipeline(
        VOCABULARY, MORPHEMES, comparative, CORPUS, SYNTACTIC_RULES
    )
    translations = pipeline.translate_corpus(CORPUS)

    for t in translations:
        iid = t.get("inscription_id", "?")
        itype = t.get("inscription_type", "?")
        conf = t.get("confidence", {})
        grade = conf.get("grade", "?")
        overall = conf.get("overall", 0)

        print(f"\n  {THIN}")
        print(f"  [{iid}] ({itype}) — grade {grade} ({overall:.3f})")
        print(f"  Source: {t.get('source', '')[:80]}")
        print(f"  Translation: {t.get('free_translation', '(none)')}")

        # Brief interlinear
        interlinear = t.get("interlinear", [])
        if interlinear:
            glosses = " : ".join(
                f"{r['token']}={r['translation']}"
                for r in interlinear[:8]
            )
            if len(interlinear) > 8:
                glosses += " ..."
            print(f"  Gloss: {glosses}")

    # ----------------------------------------------------------------
    # Stage 5: Confidence Scoring
    # ----------------------------------------------------------------
    section("STAGE 5: CONFIDENCE ANALYSIS")
    scorer = create_confidence_scorer(VOCABULARY, MORPHEMES, comparative, SYNTACTIC_RULES)
    corpus_scores = scorer.score_corpus(translations, CORPUS)

    print(f"  Total inscriptions scored: {corpus_scores['total_inscriptions']}")
    print(f"  Average confidence score : {corpus_scores['average_score']:.3f}")
    print(f"  Grade distribution       : {corpus_scores['grade_distribution']}")
    print(f"  Weakest dimension        : {corpus_scores.get('weakest_overall_dimension', '?')}")
    print(f"  Strongest dimension      : {corpus_scores.get('strongest_overall_dimension', '?')}")

    print(f"\n  Dimension averages:")
    for dim, avg in sorted(corpus_scores.get("dimension_averages", {}).items(),
                           key=lambda x: -x[1]):
        bar_len = int(avg * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        print(f"    {dim:20s}: {avg:.3f} {bar}")

    # ----------------------------------------------------------------
    # Stage 6: Summary Report
    # ----------------------------------------------------------------
    section("DECIPHERMENT SUMMARY")
    print(f"""
  Corpus size          : {len(CORPUS)} inscriptions
  Sites represented    : {len(SITES)}
  Known royal names    : {len(KNOWN_ROYAL_NAMES)}
  Lexicon entries      : {len(lexicon)}
  High-confidence words: {known}
  Cognate pairs found  : {len(likely)} / {len(cognates)}
  Average translation  : grade {max(corpus_scores.get('grade_distribution', {}), key=corpus_scores.get('grade_distribution', {}).get, default='?')} (most common)
  Average confidence   : {corpus_scores['average_score']:.3f}

  LIMITATIONS:
  - Meroitic remains only partially deciphered. True continuous text
    reading is not yet possible for most inscriptions.
  - Phonetic values of signs are known thanks to Griffith (1911),
    but vocabulary meanings remain largely uncertain.
  - Translations here combine established knowledge (funerary formulas,
    royal titles, deity names) with computational inference. Grade A/B
    translations are reasonably reliable; C/D translations are speculative.
  - The comparative Nubian evidence is suggestive but not conclusive
    for a direct genetic relationship.
""")

    # Save results to JSON
    output = {
        "lexicon_size": len(lexicon),
        "high_confidence_entries": known,
        "comparative_cognates": len(likely),
        "corpus_size": len(CORPUS),
        "average_confidence": corpus_scores["average_score"],
        "grade_distribution": corpus_scores["grade_distribution"],
        "dimension_averages": corpus_scores.get("dimension_averages", {}),
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

    with open("decipher/results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Full results saved to decipher/results.json")


if __name__ == "__main__":
    run()
