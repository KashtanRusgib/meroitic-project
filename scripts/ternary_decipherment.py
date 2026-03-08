#!/usr/bin/env python3
"""
Ternary Decipherment Engine for Meroitic Script
=================================================

Replaces the binary probabilistic framework (v1-v7) with a three-valued
logical system grounded in the epistemology of Korzybski, Brusentsov,
and Peirce.

Instead of assigning each vocabulary entry a probability ∈ [0,1]
(which creates the illusion that 0.40 is "weak evidence" when it's
really "we don't know"), this engine classifies each piece of evidence
into ternary states:

  +1  ATTESTED       Confirmed — bilingual, Greek, or universal agreement
   0  INDETERMINATE  Genuinely unknown — honest uncertainty
  -1  EXCLUDED       Ruled out by contradictory evidence

Multiple evidence channels are combined using Łukasiewicz 3-valued
logic operators, producing a classification that is HONEST about
what we know, what we might know, and what we don't know.

Output:
  - Ternary assessment of all 64 vocabulary entries
  - Ternary assessment of all 25 Tanyidamani stele sections
  - Comparative analysis: binary vs. ternary results
  - Honest decipherment statistics
"""

import json
import sys
import time
from pathlib import Path
from collections import Counter

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decipher import (
    VOCABULARY, CORPUS, MORPHEMES, EVIDENCE_TIERS,
    get_evidence_tier, KNOWN_ROYAL_NAMES,
)
from decipher.tanyidamani_stele import STELE_SECTIONS, STELE_VOCABULARY
from decipher.ternary_logic import (
    T, tand, tor, tconsensus, tmajority, tweighted,
    TernaryAssessment, EvidenceChannel, SteleSectionAssessment,
    classify_evidence_channels, CHANNEL_WEIGHTS,
    print_truth_tables,
)


DIV = "=" * 76
THIN = "─" * 76


def assess_vocabulary() -> dict:
    """
    Apply ternary evidence classification to every vocabulary entry.
    Returns dict of word → TernaryAssessment.
    """
    assessments = {}
    for word, entry in VOCABULARY.items():
        tier = get_evidence_tier(word)
        assessment = classify_evidence_channels(word, entry, tier)
        assessments[word] = assessment
    return assessments


def assess_stele(vocab_assessments: dict) -> list:
    """
    Apply ternary logic to each Tanyidamani stele section.
    Each token is looked up in vocabulary assessments or stele vocabulary.
    """
    section_assessments = []

    for section in STELE_SECTIONS:
        text = section["text"]
        tokens = [t.strip() for t in text.split(":") if t.strip()]
        token_assessments = []

        for token in tokens:
            # Strip morphological suffixes to find root
            root = token.split("-")[0] if "-" in token else token

            # Check stele vocabulary first, then main vocabulary
            if root in STELE_VOCABULARY:
                entry = STELE_VOCABULARY[root]
                tier = get_evidence_tier(root)
                if tier == "UNCLASSIFIED":
                    # Check if it's a stele-specific entry
                    cert = entry.get("certainty", 0)
                    source = entry.get("source", "")
                    if cert >= 0.75 and ("rilly" in source.lower() or "griffith" in source.lower()):
                        tier = "PROBABLE"
                    else:
                        tier = "SPECULATIVE"
                ta = classify_evidence_channels(root, entry, tier)
                token_assessments.append(ta)
            elif root in vocab_assessments:
                token_assessments.append(vocab_assessments[root])
            elif root in VOCABULARY:
                tier = get_evidence_tier(root)
                ta = classify_evidence_channels(root, VOCABULARY[root], tier)
                token_assessments.append(ta)
            elif root in KNOWN_ROYAL_NAMES:
                # Royal names are ATTESTED
                ta = TernaryAssessment(
                    word=root,
                    proposed_meaning=KNOWN_ROYAL_NAMES[root].get("full_name", root),
                    channels=[EvidenceChannel(
                        name="bilingual", value=T.ATTESTED,
                        weight=CHANNEL_WEIGHTS["bilingual"],
                        description=f"Known historical ruler: {root}",
                        source="Archaeological record")])
                token_assessments.append(ta)
            elif root == "Tanyidamani":
                ta = TernaryAssessment(
                    word="Tanyidamani",
                    proposed_meaning="Tanyidamani (king, 2nd c. BCE)",
                    channels=[EvidenceChannel(
                        name="bilingual", value=T.ATTESTED,
                        weight=CHANNEL_WEIGHTS["bilingual"],
                        description="Known historical ruler: Tanyidamani",
                        source="Hintze 1960; REM 1044")])
                token_assessments.append(ta)
            elif root == "Amnirense":
                ta = TernaryAssessment(
                    word="Amnirense",
                    proposed_meaning="Amanirenas (queen, Candace)",
                    channels=[EvidenceChannel(
                        name="bilingual", value=T.ATTESTED,
                        weight=CHANNEL_WEIGHTS["bilingual"],
                        description="Known historical ruler: Amanirenas",
                        source="REM 1044; Rilly p.142")])
                token_assessments.append(ta)
            elif root == "Amanikhabale":
                ta = TernaryAssessment(
                    word="Amanikhabale",
                    proposed_meaning="Amanikhabale (ruler)",
                    channels=[EvidenceChannel(
                        name="bilingual", value=T.ATTESTED,
                        weight=CHANNEL_WEIGHTS["bilingual"],
                        description="Known historical ruler",
                        source="REM 1026; Rilly p.146")])
                token_assessments.append(ta)
            elif root == "Mnpte":
                ta = TernaryAssessment(
                    word="Mnpte",
                    proposed_meaning="Napata (place name)",
                    channels=[EvidenceChannel(
                        name="egyptian", value=T.ATTESTED,
                        weight=CHANNEL_WEIGHTS["egyptian"],
                        description="Napata — well-identified place name",
                        source="Rilly & de Voogt 2012:156")])
                token_assessments.append(ta)
            else:
                # Unknown token — honestly INDETERMINATE
                ta = TernaryAssessment(
                    word=root,
                    proposed_meaning="[unknown]",
                    channels=[EvidenceChannel(
                        name="contextual", value=T.INDETERMINATE,
                        weight=CHANNEL_WEIGHTS["contextual"],
                        description="No evidence available",
                        source="")])
                token_assessments.append(ta)

        section_assessments.append(SteleSectionAssessment(
            section_id=section["section"],
            title=section["title"],
            status=section["status"],
            tokens=tokens,
            token_assessments=token_assessments))

    return section_assessments


def print_vocabulary_report(assessments: dict):
    """Print ternary assessment of all vocabulary."""
    print(f"\n{DIV}")
    print("  TERNARY VOCABULARY ASSESSMENT")
    print(f"  Korzybski–Brusentsov–Peirce Framework")
    print(DIV)

    # Group by ternary value
    attested = []
    indeterminate = []
    excluded = []

    for word, a in sorted(assessments.items()):
        val = a.weighted
        if val == T.ATTESTED:
            attested.append((word, a))
        elif val == T.EXCLUDED:
            excluded.append((word, a))
        else:
            indeterminate.append((word, a))

    # ATTESTED words
    print(f"\n  ┌{'─' * 72}┐")
    print(f"  │{'ATTESTED (+1) — Confirmed Knowledge':^72s}│")
    print(f"  │{'These words we KNOW':^72s}│")
    print(f"  └{'─' * 72}┘")
    for word, a in attested:
        tier = get_evidence_tier(word)
        channels_str = ", ".join(f"{ch.name}={ch.value}" for ch in a.channels)
        print(f"    {word:15s} → \"{a.proposed_meaning:35s}\" [{tier}] ({channels_str})")

    # INDETERMINATE words
    print(f"\n  ┌{'─' * 72}┐")
    print(f"  │{'INDETERMINATE (0) — Honest Uncertainty':^72s}│")
    print(f"  │{'Evidence exists but insufficient — this is NOT weak positive':^72s}│")
    peirce_note = "It is Peirce's boundary value: neither true nor false"
    print(f"  │{peirce_note:^72s}│")
    print(f"  └{'─' * 72}┘")
    for word, a in indeterminate:
        tier = get_evidence_tier(word)
        channels_str = ", ".join(f"{ch.name}={ch.value}" for ch in a.channels)
        print(f"    {word:15s} → \"{a.proposed_meaning:35s}\" [{tier}] ({channels_str})")

    # EXCLUDED words
    if excluded:
        print(f"\n  ┌{'─' * 72}┐")
        print(f"  │{'EXCLUDED (-1) — Ruled Out':^72s}│")
        print(f"  └{'─' * 72}┘")
        for word, a in excluded:
            channels_str = ", ".join(f"{ch.name}={ch.value}" for ch in a.channels)
            print(f"    {word:15s} → \"{a.proposed_meaning:35s}\" ({channels_str})")

    # Summary
    total = len(assessments)
    print(f"\n{THIN}")
    print(f"  VOCABULARY SUMMARY")
    print(f"    Total entries:    {total}")
    print(f"    ATTESTED (+1):    {len(attested):3d} ({len(attested)/total*100:.1f}%)"
          f"  — These we KNOW")
    print(f"    INDETERMINATE (0):{len(indeterminate):3d} ({len(indeterminate)/total*100:.1f}%)"
          f"  — Honestly uncertain")
    print(f"    EXCLUDED (-1):    {len(excluded):3d} ({len(excluded)/total*100:.1f}%)"
          f"  — Ruled out")
    print(THIN)

    return len(attested), len(indeterminate), len(excluded)


def print_stele_report(section_assessments: list):
    """Print ternary assessment of all stele sections."""
    print(f"\n{DIV}")
    print("  TERNARY TANYIDAMANI STELE ASSESSMENT (REM 1044)")
    print(f"  25 sections across 4 sides")
    print(DIV)

    all_attested = 0
    all_indeterminate = 0
    all_excluded = 0
    all_tokens = 0

    for sa in section_assessments:
        att = sum(1 for ta in sa.token_assessments if ta.weighted == T.ATTESTED)
        ind = sum(1 for ta in sa.token_assessments if ta.weighted == T.INDETERMINATE)
        exc = sum(1 for ta in sa.token_assessments if ta.weighted == T.EXCLUDED)
        n = len(sa.token_assessments)
        all_attested += att
        all_indeterminate += ind
        all_excluded += exc
        all_tokens += n

        status_marker = {
            "ATTESTED": "✓✓",
            "ATTESTED/RESTORED": "✓~",
            "RESTORED": "~~",
            "CONJECTURAL": "??",
        }.get(sa.status, "??")

        sec_val = sa.section_value
        print(f"\n  [{sa.section_id}] {sa.title} ({sa.status}) {status_marker}")
        print(f"    Section ternary value: {sec_val!r}")
        print(f"    Tokens: {n} total"
              f" | {att} ATTESTED"
              f" | {ind} INDETERMINATE"
              f" | {exc} EXCLUDED")

        # Show each token
        for ta in sa.token_assessments:
            val = ta.weighted
            marker = {T.ATTESTED: "✓", T.INDETERMINATE: "?", T.EXCLUDED: "✗"}[val]
            print(f"      {marker} {ta.word:20s} → {val!r:25s} "
                  f"(score={ta.confidence_score:.2f}) "
                  f"\"{ta.proposed_meaning[:30]}\"")

    # Summary
    print(f"\n{DIV}")
    print(f"  STELE SUMMARY")
    print(f"    Total tokens:       {all_tokens}")
    print(f"    ATTESTED (+1):      {all_attested:3d} ({all_attested/all_tokens*100:.1f}%)"
          f"  — Tokens we genuinely know")
    print(f"    INDETERMINATE (0):  {all_indeterminate:3d} ({all_indeterminate/all_tokens*100:.1f}%)"
          f"  — Honestly uncertain tokens")
    print(f"    EXCLUDED (-1):      {all_excluded:3d} ({all_excluded/all_tokens*100:.1f}%)"
          f"  — Tokens ruled out")
    print(f"\n    Genuine decoded coverage: {all_attested/all_tokens*100:.1f}%"
          f" (only ATTESTED tokens)")
    print(f"    Honest uncertainty zone:  {all_indeterminate/all_tokens*100:.1f}%"
          f" (INDETERMINATE tokens)")
    print(DIV)

    return all_attested, all_indeterminate, all_excluded, all_tokens


def print_comparative_analysis(v_att, v_ind, v_exc, s_att, s_ind, s_exc, s_total):
    """Compare ternary vs binary results."""
    print(f"\n{DIV}")
    print("  COMPARATIVE ANALYSIS: TERNARY vs. BINARY LOGIC")
    print(DIV)

    print(f"""
  Binary Logic (v7.0):
    Vocabulary: 64 entries, each with P ∈ [0, 1]
    Problem: P=0.40 for 'dmke=temple' APPEARS to be weak evidence FOR
    the hypothesis. But it's really a guess dressed as probability.
    The posterior floor hack then guaranteed P could never drop below
    the prior — making even bad guesses immune to disconfirmation.

  Ternary Logic (v8.0):
    Vocabulary: 64 entries, each with ternary state ∈ {{-1, 0, +1}}
    Advantage: 'dmke=temple' is INDETERMINATE (0) — we simply
    DON'T KNOW, and the system models this honestly. There's no
    number to inflate, no floor to hack.

  ┌────────────────────────────────────────────────────────────────────┐
  │  "The map is not the territory." — Korzybski                      │
  │  Binary logic maps the territory of knowledge onto a line [0,1].  │
  │  Ternary logic respects the territory's actual structure:          │
  │    knowledge (+1), ignorance (0), and counter-evidence (-1).      │
  └────────────────────────────────────────────────────────────────────┘
""")

    v_total = v_att + v_ind + v_exc
    print(f"  Vocabulary (64 entries):")
    print(f"    Binary view:  7 SECURE + 25 PROBABLE + 32 SPECULATIVE")
    print(f"    Ternary view: {v_att} ATTESTED + {v_ind} INDETERMINATE + {v_exc} EXCLUDED")
    print()
    print(f"  Tanyidamani Stele ({s_total} tokens):")
    print(f"    Binary v7.0:  197/197 = 100.0% decoded (DISHONEST — inflated)")
    print(f"    Binary v8.0:  ~197/198 = 99.5% decoded (lowest P=0.497)")
    print(f"    Ternary v8.0: {s_att}/{s_total} = {s_att/s_total*100:.1f}% ATTESTED"
          f" + {s_ind}/{s_total} = {s_ind/s_total*100:.1f}% INDETERMINATE")
    print()
    print(f"  ┌────────────────────────────────────────────────────────────────────┐")
    print(f"  │  KEY INSIGHT                                                       │")
    print(f"  │                                                                    │")
    print(f"  │  Binary logic says: {s_att+s_ind}/{s_total} tokens have SOME translation"
          f" ({(s_att+s_ind)/s_total*100:.0f}%){'':>4s}│")
    print(f"  │  Ternary logic says: {s_att}/{s_total} tokens are GENUINELY KNOWN"
          f" ({s_att/s_total*100:.0f}%){'':>8s}│")
    print(f"  │                      {s_ind}/{s_total} tokens are HONESTLY UNCERTAIN"
          f" ({s_ind/s_total*100:.0f}%){'':>5s}│")
    print(f"  │                                                                    │")
    print(f"  │  The difference between those percentages is the HONESTY GAP       │")
    print(f"  │  that binary logic was hiding.                                     │")
    print(f"  └────────────────────────────────────────────────────────────────────┘")
    print(DIV)


def main():
    start = time.time()

    print(DIV)
    print("  MEROITIC TERNARY DECIPHERMENT ENGINE v8.0")
    print("  Three-Valued Logic: Korzybski–Brusentsov–Peirce Framework")
    print("  \"The map is not the territory.\" — Alfred Korzybski, 1933")
    print(DIV)

    # ── Phase 1: Łukasiewicz Truth Tables ──
    print(f"\n{DIV}")
    print("  PHASE 1: ŁUKASIEWICZ 3-VALUED LOGIC FOUNDATION")
    print(DIV)
    print_truth_tables()

    # ── Phase 2: Vocabulary Assessment ──
    print(f"\n{DIV}")
    print("  PHASE 2: VOCABULARY TERNARY CLASSIFICATION")
    print(DIV)
    vocab_assessments = assess_vocabulary()
    v_att, v_ind, v_exc = print_vocabulary_report(vocab_assessments)

    # ── Phase 3: Stele Assessment ──
    print(f"\n{DIV}")
    print("  PHASE 3: TANYIDAMANI STELE TERNARY CLASSIFICATION")
    print(DIV)
    section_assessments = assess_stele(vocab_assessments)
    s_att, s_ind, s_exc, s_total = print_stele_report(section_assessments)

    # ── Phase 4: Comparative Analysis ──
    print_comparative_analysis(v_att, v_ind, v_exc, s_att, s_ind, s_exc, s_total)

    # ── Phase 5: Save Results ──
    elapsed = time.time() - start

    results = {
        "engine": "v8.0_ternary",
        "framework": "Korzybski-Brusentsov-Peirce",
        "logic": "Łukasiewicz 3-valued",
        "elapsed_seconds": round(elapsed, 2),
        "vocabulary": {
            "total": len(vocab_assessments),
            "attested": v_att,
            "indeterminate": v_ind,
            "excluded": v_exc,
            "attested_pct": round(v_att / len(vocab_assessments) * 100, 1),
        },
        "stele": {
            "total_tokens": s_total,
            "attested": s_att,
            "indeterminate": s_ind,
            "excluded": s_exc,
            "genuine_coverage_pct": round(s_att / s_total * 100, 1),
        },
        "vocabulary_detail": {},
        "stele_sections": [],
    }

    for word, a in vocab_assessments.items():
        results["vocabulary_detail"][word] = {
            "meaning": a.proposed_meaning,
            "ternary_value": a.weighted.name,
            "confidence_score": a.confidence_score,
            "tier": get_evidence_tier(word),
            "channels": [{
                "name": ch.name,
                "value": ch.value.name,
                "weight": ch.weight,
                "description": ch.description,
            } for ch in a.channels],
        }

    for sa in section_assessments:
        results["stele_sections"].append({
            "section": sa.section_id,
            "title": sa.title,
            "status": sa.status,
            "ternary_value": sa.section_value.name,
            "attested_fraction": round(sa.attested_fraction, 3),
            "tokens": [{
                "word": ta.word,
                "meaning": ta.proposed_meaning,
                "ternary": ta.weighted.name,
                "score": ta.confidence_score,
            } for ta in sa.token_assessments],
        })

    results_file = ROOT / "decipher" / "ternary_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved to {results_file}")
    print(f"  Elapsed: {elapsed:.1f}s")

    # Final banner
    genuine_pct = s_att / s_total * 100
    print(f"\n{'#' * 76}")
    print(f"#{'':74s}#")
    if genuine_pct >= 90:
        print(f"#{'TERNARY ASSESSMENT: STRONG GENUINE COVERAGE':^74s}#")
    elif genuine_pct >= 60:
        print(f"#{'TERNARY ASSESSMENT: PARTIAL GENUINE COVERAGE':^74s}#")
    else:
        print(f"#{'TERNARY ASSESSMENT: SIGNIFICANT UNCERTAINTY REMAINS':^74s}#")
    print(f"#{'':74s}#")
    print(f"#  Genuinely ATTESTED:      {s_att:3d}/{s_total} tokens ({genuine_pct:.1f}%)"
          f"{'':>25s}#")
    print(f"#  Honestly INDETERMINATE:  {s_ind:3d}/{s_total} tokens ({s_ind/s_total*100:.1f}%)"
          f"{'':>25s}#")
    print(f"#  EXCLUDED:                {s_exc:3d}/{s_total} tokens ({s_exc/s_total*100:.1f}%)"
          f"{'':>25s}#")
    print(f"#{'':74s}#")
    print(f"#  \"True/False is a lie. The truth has three values.\"{'':>25s}#")
    print(f"#{'':74s}#")
    print(f"{'#' * 76}")


if __name__ == "__main__":
    main()
