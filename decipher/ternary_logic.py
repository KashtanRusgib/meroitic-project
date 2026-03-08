"""
Ternary Logic Engine for Meroitic Decipherment
================================================

Epistemological framework based on the confluence of:
  - Korzybski's General Semantics: binary logic is a "semantic blockage"
    that collapses multi-dimensional reality into two-dimensional categories
  - Brusentsov's Balanced Ternary: {-1, 0, +1} is more natural and efficient
    than {0, 1} for representing knowledge states
  - Peirce's Triadic Semiotics: Sign, Object, Interpretant — the process
    of interpretation itself requires a third value beyond True/False

Applied to Meroitic: the binary approach (known/unknown, with probabilities
∈ [0,1]) led to the v7.0 inflation problem — SPECULATIVE entries were
assigned probabilities that LOOKED like evidence but were really guesses
dressed in the clothing of certainty. Ternary logic replaces this with
THREE QUALITATIVELY DISTINCT epistemic states:

  +1  ATTESTED    Confirmed by bilingual/parallel texts, Greek transcriptions,
                   or universal scholarly agreement. This is KNOWLEDGE.
   0  INDETERMINATE  Evidence exists but is insufficient for determination.
                   This is honest UNCERTAINTY — not low probability, but a
                   qualitatively different state. As Peirce's "boundary" value.
  -1  EXCLUDED    Positively ruled out by contradictory evidence. This is
                   NEGATIVE knowledge — knowing what something is NOT.

Key insight: In binary logic, P=0.45 for "dmke = temple" looks like weak
evidence FOR the hypothesis. In ternary logic, dmke = INDETERMINATE (0) —
we simply don't know, and the system models this honestly rather than
pretending a guess is weak evidence.

Łukasiewicz 3-valued logic operators (with values {+1, 0, -1}):
  ¬(+1) = -1,  ¬(0) = 0,  ¬(-1) = +1
  a ∧ b = min(a, b)
  a ∨ b = max(a, b)
  a → b = min(1, 1 - a + b)   [Łukasiewicz implication]

Balanced ternary arithmetic:
  Radix economy of e ≈ 2.718 (base 3 is most efficient: Brusentsov)
  Negation is trivial: flip signs
  No unsigned/signed distinction needed

References:
  - Łukasiewicz, J. 1920. "O logice trójwartościowej"
  - Korzybski, A. 1933. "Science and Sanity"
  - Brusentsov, N. 1962. "The Setun Ternary Computer"
  - Peirce, C.S. 1909. Logic Notebook (MS 339)
  - Rilly, C. 2007. "La langue du royaume de Méroé"
"""

from enum import IntEnum
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════════
# TERNARY VALUE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class T(IntEnum):
    """Balanced ternary truth values."""
    EXCLUDED = -1       # Positively ruled out
    INDETERMINATE = 0   # Genuinely unknown — Peirce's "boundary"
    ATTESTED = 1        # Confirmed knowledge

    def __repr__(self):
        return {-1: "EXCLUDED(-1)", 0: "INDETERMINATE(0)", 1: "ATTESTED(+1)"}[self.value]

    def __str__(self):
        return {-1: "✗", 0: "?", 1: "✓"}[self.value]


# ═══════════════════════════════════════════════════════════════════════════════
# ŁUKASIEWICZ 3-VALUED OPERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def tnot(a: T) -> T:
    """Ternary negation: ¬(+1)=-1, ¬(0)=0, ¬(-1)=+1"""
    return T(-a.value)

def tand(a: T, b: T) -> T:
    """Ternary conjunction (strong): min(a, b)"""
    return T(min(a.value, b.value))

def tor(a: T, b: T) -> T:
    """Ternary disjunction (strong): max(a, b)"""
    return T(max(a.value, b.value))

def timplies(a: T, b: T) -> T:
    """Łukasiewicz implication: min(1, 1 - a + b)"""
    return T(min(1, 1 - a.value + b.value))

def tconsensus(*values: T) -> T:
    """
    Consensus operator for combining multiple evidence channels.

    Given n evidence values, returns:
      +1 if ALL are +1 (unanimous attestation)
      -1 if ANY is -1 (one exclusion vetoes)
       0 otherwise (mixed or insufficient evidence)

    This implements a conservative epistemic policy: it takes positive
    evidence from ALL channels to confirm, but only ONE channel to exclude.
    The intermediate state is the honest default.
    """
    vals = [v.value for v in values]
    if not vals:
        return T.INDETERMINATE
    if any(v == -1 for v in vals):
        return T.EXCLUDED
    if all(v == 1 for v in vals):
        return T.ATTESTED
    return T.INDETERMINATE

def tmajority(*values: T) -> T:
    """
    Majority vote operator.

    Returns the value held by the strict majority of channels.
    If no strict majority, returns INDETERMINATE.
    """
    vals = [v.value for v in values]
    if not vals:
        return T.INDETERMINATE
    counts = {-1: 0, 0: 0, 1: 0}
    for v in vals:
        counts[v] += 1
    threshold = len(vals) / 2
    if counts[1] > threshold:
        return T.ATTESTED
    if counts[-1] > threshold:
        return T.EXCLUDED
    return T.INDETERMINATE

def tweighted(channels: List[Tuple[T, float]]) -> T:
    """
    Weighted ternary combination.

    Each channel provides a ternary value and a weight (0-1).
    Computes weighted sum: Σ(value × weight) / Σ(weight)
    Maps result to ternary: > +0.33 → ATTESTED, < -0.33 → EXCLUDED, else INDETERMINATE.

    The thresholds are deliberately wide — the INDETERMINATE zone is
    twice as broad as either ATTESTED or EXCLUDED, implementing
    Korzybski's principle that certainty should be the exception, not
    the default.
    """
    if not channels:
        return T.INDETERMINATE
    total_weight = sum(w for _, w in channels)
    if total_weight == 0:
        return T.INDETERMINATE
    weighted_sum = sum(v.value * w for v, w in channels)
    score = weighted_sum / total_weight
    if score > 0.33:
        return T.ATTESTED
    if score < -0.33:
        return T.EXCLUDED
    return T.INDETERMINATE


# ═══════════════════════════════════════════════════════════════════════════════
# EVIDENCE CHANNELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvidenceChannel:
    """A single channel of evidence for a word's meaning."""
    name: str           # e.g., "bilingual", "comparative", "contextual"
    value: T            # Ternary assessment
    weight: float       # Channel reliability (0-1)
    description: str    # Human-readable explanation
    source: str = ""    # Citation


@dataclass
class TernaryAssessment:
    """Complete ternary assessment of a vocabulary entry."""
    word: str
    proposed_meaning: str
    channels: List[EvidenceChannel] = field(default_factory=list)

    @property
    def consensus(self) -> T:
        """Conservative consensus across all channels."""
        return tconsensus(*[ch.value for ch in self.channels])

    @property
    def majority(self) -> T:
        """Majority vote across channels."""
        return tmajority(*[ch.value for ch in self.channels])

    @property
    def weighted(self) -> T:
        """Weighted combination (Korzybski's wide INDETERMINATE zone)."""
        return tweighted([(ch.value, ch.weight) for ch in self.channels])

    @property
    def confidence_score(self) -> float:
        """
        Backward-compatible confidence score ∈ [0, 1] for systems
        that need a numerical value. Derived FROM ternary, not the
        other way around.

        ATTESTED channels contribute positively, EXCLUDED negatively,
        INDETERMINATE contribute nothing (honest zero-information).
        """
        if not self.channels:
            return 0.0
        total_weight = sum(ch.weight for ch in self.channels)
        if total_weight == 0:
            return 0.0
        # Map: +1 → contributes weight, 0 → contributes 0, -1 → subtracts weight
        positive = sum(ch.weight for ch in self.channels if ch.value == T.ATTESTED)
        return round(positive / total_weight, 4)

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [f"  {self.word} → \"{self.proposed_meaning}\""]
        lines.append(f"    Consensus: {self.consensus!r}  "
                    f"Majority: {self.majority!r}  "
                    f"Weighted: {self.weighted!r}  "
                    f"Score: {self.confidence_score:.2f}")
        for ch in self.channels:
            lines.append(f"    [{ch.value}] {ch.name} (w={ch.weight:.2f}): {ch.description}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# EVIDENCE CHANNEL DEFINITIONS FOR MEROITIC
# ═══════════════════════════════════════════════════════════════════════════════

# Weight hierarchy reflects epistemic reliability:
#   Bilingual evidence is the gold standard
#   Greek/Egyptian parallels are very strong
#   NES comparative (Rilly) is strong but indirect
#   Structural/positional is moderate
#   Contextual guessing is weak
CHANNEL_WEIGHTS = {
    "bilingual":    1.00,   # Bilingual Meroitic-Egyptian text
    "greek":        0.95,   # Greek transcription/parallel
    "egyptian":     0.90,   # Egyptian parallel (divine names etc.)
    "nes_cognate":  0.75,   # Nilo-Saharan comparative (Rilly)
    "positional":   0.60,   # Recurring position in known formula
    "structural":   0.50,   # Structural parallel to known pattern
    "iconographic": 0.50,   # Temple relief / iconographic correlation
    "contextual":   0.30,   # Contextual guess (weakest evidence)
    "distributional": 0.25, # Statistical distribution only
}


def classify_evidence_channels(word: str, entry: dict, tier: str) -> TernaryAssessment:
    """
    Classify a vocabulary entry into ternary evidence channels.

    This is where the epistemological rubber meets the road:
    instead of a single certainty number, we decompose the evidence
    into independent channels, each with a ternary value.
    """
    meaning = entry.get("translation", "[unknown]")
    assessment = TernaryAssessment(word=word, proposed_meaning=meaning)

    source = entry.get("source", "").lower()
    certainty = entry.get("certainty", 0)

    # Channel 1: Bilingual evidence
    if "bilingual" in source:
        assessment.channels.append(EvidenceChannel(
            name="bilingual", value=T.ATTESTED,
            weight=CHANNEL_WEIGHTS["bilingual"],
            description="Confirmed in bilingual Meroitic-Egyptian text",
            source=entry.get("source", "")))
    elif tier == "SECURE":
        # SECURE tier implies some form of cross-linguistic confirmation
        assessment.channels.append(EvidenceChannel(
            name="bilingual", value=T.ATTESTED,
            weight=CHANNEL_WEIGHTS["bilingual"],
            description="Cross-linguistically confirmed (SECURE tier)",
            source=entry.get("source", "")))

    # Channel 2: Greek/Egyptian parallel
    if entry.get("egyptian_parallel"):
        assessment.channels.append(EvidenceChannel(
            name="egyptian", value=T.ATTESTED,
            weight=CHANNEL_WEIGHTS["egyptian"],
            description=f"Egyptian parallel: {entry['egyptian_parallel']}",
            source=entry.get("source", "")))
    elif "greek" in source or "greek" in entry.get("egyptian_parallel", "").lower():
        assessment.channels.append(EvidenceChannel(
            name="greek", value=T.ATTESTED,
            weight=CHANNEL_WEIGHTS["greek"],
            description="Greek transcription/parallel",
            source=entry.get("source", "")))

    # Channel 3: NES comparative (Nubian cognate)
    cognate = entry.get("nubian_cognate", "")
    if cognate:
        if tier in ("SECURE", "PROBABLE"):
            assessment.channels.append(EvidenceChannel(
                name="nes_cognate", value=T.ATTESTED,
                weight=CHANNEL_WEIGHTS["nes_cognate"],
                description=f"Nubian cognate: {cognate}",
                source="Rilly 2007/2010"))
        else:
            # Cognate exists but word is SPECULATIVE — cognate is suggestive, not confirmed
            assessment.channels.append(EvidenceChannel(
                name="nes_cognate", value=T.INDETERMINATE,
                weight=CHANNEL_WEIGHTS["nes_cognate"],
                description=f"Suggestive cognate (unconfirmed): {cognate}",
                source="Rilly 2007/2010"))

    # Channel 4: Positional evidence (offering formula position)
    if "offering" in source and certainty >= 0.80:
        assessment.channels.append(EvidenceChannel(
            name="positional", value=T.ATTESTED,
            weight=CHANNEL_WEIGHTS["positional"],
            description="Consistent position in offering formula",
            source=entry.get("source", "")))
    elif "offering" in source:
        assessment.channels.append(EvidenceChannel(
            name="positional", value=T.INDETERMINATE,
            weight=CHANNEL_WEIGHTS["positional"],
            description="Appears in offering contexts (position uncertain)",
            source=entry.get("source", "")))

    # Channel 5: Published scholarship (Rilly, Griffith, Hintze)
    published_scholars = ["rilly", "griffith", "hintze", "hofmann"]
    if any(s in source for s in published_scholars):
        if tier == "PROBABLE":
            assessment.channels.append(EvidenceChannel(
                name="structural", value=T.ATTESTED,
                weight=CHANNEL_WEIGHTS["structural"],
                description="Published scholarly identification",
                source=entry.get("source", "")))
        elif tier == "SPECULATIVE":
            # Cited but weakly — scholar mention doesn't mean confirmation
            assessment.channels.append(EvidenceChannel(
                name="structural", value=T.INDETERMINATE,
                weight=CHANNEL_WEIGHTS["structural"],
                description="Mentioned in scholarship but not confirmed",
                source=entry.get("source", "")))

    # Channel 6: Contextual/distributional (weakest evidence)
    contextual_markers = ["context", "pattern", "parallel", "epithet"]
    if any(m in source for m in contextual_markers) and tier == "SPECULATIVE":
        assessment.channels.append(EvidenceChannel(
            name="contextual", value=T.INDETERMINATE,
            weight=CHANNEL_WEIGHTS["contextual"],
            description="Contextual inference by this project",
            source=entry.get("source", "")))

    # Channel 7: Iconographic (for deity names)
    if "iconography" in source or "temple" in source and entry.get("category") == "deity_name":
        if tier in ("SECURE", "PROBABLE"):
            assessment.channels.append(EvidenceChannel(
                name="iconographic", value=T.ATTESTED,
                weight=CHANNEL_WEIGHTS["iconographic"],
                description="Iconographic identification",
                source=entry.get("source", "")))

    # Ensure at least one channel exists
    if not assessment.channels:
        assessment.channels.append(EvidenceChannel(
            name="contextual", value=T.INDETERMINATE,
            weight=CHANNEL_WEIGHTS["contextual"],
            description="No independent evidence — project inference only",
            source="project inference"))

    return assessment


# ═══════════════════════════════════════════════════════════════════════════════
# TERNARY STELE SECTION ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SteleSectionAssessment:
    """Ternary assessment of a stele section."""
    section_id: str
    title: str
    status: str  # ATTESTED, RESTORED, CONJECTURAL
    tokens: List[str]
    token_assessments: List[TernaryAssessment]

    @property
    def section_value(self) -> T:
        """
        Ternary value for the entire section.

        Uses consensus: ALL tokens must be ATTESTED for section to be ATTESTED.
        This is intentionally strict — a section with one INDETERMINATE token
        cannot honestly claim to be fully decoded.
        """
        if not self.token_assessments:
            return T.INDETERMINATE
        values = [ta.weighted for ta in self.token_assessments]
        return tconsensus(*values)

    @property
    def attested_fraction(self) -> float:
        """Fraction of tokens that are ATTESTED."""
        if not self.token_assessments:
            return 0.0
        attested = sum(1 for ta in self.token_assessments if ta.weighted == T.ATTESTED)
        return attested / len(self.token_assessments)

    @property
    def indeterminate_fraction(self) -> float:
        """Fraction of tokens that are INDETERMINATE."""
        if not self.token_assessments:
            return 1.0
        indeterminate = sum(1 for ta in self.token_assessments
                          if ta.weighted == T.INDETERMINATE)
        return indeterminate / len(self.token_assessments)

    def summary(self) -> str:
        sec_val = self.section_value
        att = self.attested_fraction
        ind = self.indeterminate_fraction
        lines = [
            f"  [{self.section_id}] {self.title} ({self.status})",
            f"    Section: {sec_val!r}  "
            f"Attested: {att:.0%}  Indeterminate: {ind:.0%}  "
            f"Excluded: {1-att-ind:.0%}",
        ]
        for ta in self.token_assessments:
            lines.append(f"      {ta.word:20s} → {ta.weighted!r}  "
                        f"(score={ta.confidence_score:.2f})")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# TERNARY TRUTH TABLES (for reference / display)
# ═══════════════════════════════════════════════════════════════════════════════

def print_truth_tables():
    """Print Łukasiewicz 3-valued logic truth tables."""
    values = [T.ATTESTED, T.INDETERMINATE, T.EXCLUDED]
    print("Łukasiewicz 3-Valued Logic Truth Tables")
    print("=" * 50)

    print("\nNegation (¬):")
    for a in values:
        print(f"  ¬({a!r:20s}) = {tnot(a)!r}")

    print("\nConjunction (∧ = min):")
    print(f"  {'':20s}", end="")
    for b in values:
        print(f"  {b!r:20s}", end="")
    print()
    for a in values:
        print(f"  {a!r:20s}", end="")
        for b in values:
            print(f"  {tand(a, b)!r:20s}", end="")
        print()

    print("\nDisjunction (∨ = max):")
    print(f"  {'':20s}", end="")
    for b in values:
        print(f"  {b!r:20s}", end="")
    print()
    for a in values:
        print(f"  {a!r:20s}", end="")
        for b in values:
            print(f"  {tor(a, b)!r:20s}", end="")
        print()

    print("\nImplication (→, Łukasiewicz):")
    print(f"  {'':20s}", end="")
    for b in values:
        print(f"  {b!r:20s}", end="")
    print()
    for a in values:
        print(f"  {a!r:20s}", end="")
        for b in values:
            print(f"  {timplies(a, b)!r:20s}", end="")
        print()
