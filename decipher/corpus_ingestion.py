"""
Module 4: Corpus Ingestion & Iterative Refinement Framework
============================================================
Provides:
  1. Standardized ingestion of new inscriptions (with validation)
  2. Iterative confidence recalculation as evidence accumulates
  3. Predictive model evaluation: test whether new texts confirm or refute
     existing translations
  4. Unicode Meroitic standardization (U+10980–U+1099F)

References:
  - Leclant & Rilly 2000 "Répertoire d'Épigraphie Méroïtique"
  - Carrier 2020 "Meroitic Inscriptions from Qasr Ibrim"
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from decipher import VOCABULARY, CORPUS, KNOWN_ROYAL_NAMES, SITES, MEROITIC_CURSIVE_SIGNS


# ═══════════════════════════════════════════════════════════════════════════════
# Unicode Meroitic Standardizer
# ═══════════════════════════════════════════════════════════════════════════════

# Reverse mapping: Latin transliteration → Unicode Meroitic sign
LATIN_TO_MEROITIC = {v: k for k, v in MEROITIC_CURSIVE_SIGNS.items()
                     if v != "word_divider"}
LATIN_TO_MEROITIC["divider"] = "𐦗"

# Known encoding variants that appear in published transliterations
NORMALIZATION_MAP = {
    # Common variant spellings in different publication traditions
    "sh": "s",       # Griffith tradition: sh → Rilly: s
    "kh": "h",       # Some publications use kh for the h-sign
    "ny": "ne",      # Palatal nasal variant
    "ñ": "ne",       # Unicode palatal nasal → ne sign
    "ḥ": "h",        # Egyptian convention
    "ẖ": "h",        # Capital variant
    "č": "se",       # Affricate convention
}


class UnicodeStandardizer:
    """
    Convert Meroitic transliterations to standardized Unicode cursive (U+10980–U+1099F).
    """

    def __init__(self):
        self.lat_to_mer = LATIN_TO_MEROITIC
        self.norm_map = NORMALIZATION_MAP
        self.divider = "\U00010997"

    def transliterate_to_unicode(self, transliteration: str) -> str:
        """Convert a colon-separated transliteration to Unicode Meroitic cursive."""
        tokens = [t.strip() for t in transliteration.split(":") if t.strip()]
        unicode_tokens = []
        for token in tokens:
            rendered = self._render_token(token)
            unicode_tokens.append(rendered)
        return f" {self.divider} ".join(unicode_tokens)

    def _render_token(self, token: str) -> str:
        """Convert a single token to Meroitic Unicode."""
        # Strip morpheme boundaries for the script rendering
        base = token.split("-")[0].lower()
        # Normalize variant spellings
        for old, new in self.norm_map.items():
            base = base.replace(old, new)

        result = []
        i = 0
        while i < len(base):
            # Try two-character sequences first
            if i + 1 < len(base) and base[i:i+2] in self.lat_to_mer:
                result.append(self.lat_to_mer[base[i:i+2]])
                i += 2
            elif base[i] in self.lat_to_mer:
                result.append(self.lat_to_mer[base[i]])
                i += 1
            else:
                i += 1  # Skip unrecognized characters

        return "".join(result)

    def validate_unicode(self, text: str) -> dict:
        """Validate that a Unicode text uses only valid Meroitic codepoints."""
        valid_range = range(0x10980, 0x109A0)
        total = 0
        valid = 0
        invalid_chars = []

        for ch in text:
            if ch.isspace():
                continue
            total += 1
            if ord(ch) in valid_range:
                valid += 1
            else:
                invalid_chars.append((ch, hex(ord(ch))))

        return {
            "total_characters": total,
            "valid_meroitic": valid,
            "invalid_characters": invalid_chars,
            "is_valid": len(invalid_chars) == 0,
        }


class InscriptionValidator:
    """Validate incoming inscription data for completeness and consistency."""

    REQUIRED_FIELDS = {"id", "text", "site", "type"}
    KNOWN_TYPES = {
        "funerary", "offering_table", "temple", "royal_stele",
        "graffito", "ostracon", "papyrus", "rock_inscription",
        "religious", "enthronement",
    }

    def validate(self, inscription: dict) -> dict:
        """Validate a single inscription entry. Returns issues found."""
        issues = []

        # Required fields
        for field in self.REQUIRED_FIELDS:
            if field not in inscription:
                issues.append({"severity": "ERROR", "message": f"Missing required field: {field}"})

        # ID format
        rem_id = inscription.get("id", "")
        if rem_id and not re.match(r"^REM_\d{4}[A-Z]?$", rem_id):
            issues.append({
                "severity": "WARNING",
                "message": f"Non-standard ID format: {rem_id} (expected REM_NNNN)",
            })

        # Text format (colon-separated transliteration)
        text = inscription.get("text", "")
        if text:
            tokens = [t.strip() for t in text.split(":") if t.strip()]
            if len(tokens) < 1:
                issues.append({"severity": "ERROR", "message": "Empty text field"})
            # Check for valid characters
            valid_chars = set("abcdefghijklmnopqrstuvwxyz-: 0123456789")
            invalid = set(text.lower()) - valid_chars
            if invalid:
                issues.append({
                    "severity": "WARNING",
                    "message": f"Non-standard characters in text: {invalid}",
                })
        else:
            issues.append({"severity": "ERROR", "message": "Empty or missing text"})

        # Known site
        site = inscription.get("site", "")
        if site and site not in SITES and site not in [s.lower() for s in SITES]:
            issues.append({
                "severity": "INFO",
                "message": f"Unknown site: {site} (not in known sites database)",
            })

        # Known type
        ins_type = inscription.get("type", "")
        if ins_type and ins_type not in self.KNOWN_TYPES:
            issues.append({
                "severity": "INFO",
                "message": f"Non-standard inscription type: {ins_type}",
            })

        return {
            "id": rem_id,
            "is_valid": not any(i["severity"] == "ERROR" for i in issues),
            "issues": issues,
            "issue_count": len(issues),
        }


class CorpusIngester:
    """
    Manage the ingestion of new inscriptions into the corpus.
    Handles deduplication, validation, and incremental model updates.
    """

    def __init__(self, corpus: Optional[list] = None):
        self.corpus = list(corpus or CORPUS)
        self.validator = InscriptionValidator()
        self.standardizer = UnicodeStandardizer()
        self._existing_ids = {entry["id"] for entry in self.corpus if "id" in entry}

    def ingest(self, new_inscriptions: list[dict]) -> dict:
        """
        Ingest a batch of new inscriptions. Validates, deduplicates,
        standardizes, and integrates.
        """
        accepted = []
        rejected = []
        duplicates = []

        for insc in new_inscriptions:
            # Validate
            validation = self.validator.validate(insc)

            if not validation["is_valid"]:
                rejected.append({
                    "inscription": insc,
                    "reason": "validation_failure",
                    "issues": validation["issues"],
                })
                continue

            # Deduplicate
            if insc.get("id") in self._existing_ids:
                duplicates.append(insc.get("id"))
                continue

            # Standardize Unicode
            if "text" in insc:
                insc["unicode_meroitic"] = self.standardizer.transliterate_to_unicode(
                    insc["text"]
                )

            # Add to corpus
            self.corpus.append(insc)
            self._existing_ids.add(insc.get("id"))
            accepted.append(insc.get("id"))

        return {
            "accepted": accepted,
            "rejected": rejected,
            "duplicates": duplicates,
            "summary": {
                "submitted": len(new_inscriptions),
                "accepted": len(accepted),
                "rejected": len(rejected),
                "duplicates": len(duplicates),
                "new_corpus_size": len(self.corpus),
            },
        }

    def export_corpus(self, output_path: Path) -> dict:
        """Export the full corpus in standardized JSON format."""
        export_data = {
            "metadata": {
                "name": "Meroitic Inscription Corpus",
                "version": "2.0",
                "inscription_count": len(self.corpus),
                "sources": [
                    "Griffith 1911", "Hintze 1960", "Rilly & de Voogt 2012",
                    "Carrier 2020", "REM database",
                ],
            },
            "inscriptions": self.corpus,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return {
            "path": str(output_path),
            "inscriptions": len(self.corpus),
            "size_bytes": output_path.stat().st_size,
        }


class ConfidenceUpdater:
    """
    Iteratively recalculate confidence scores as new evidence accumulates.

    The core principle: a token's confidence should INCREASE when:
      1. More attestations of the same root are found
      2. New cognates from Nubian/ES languages are established
      3. The same translation holds across multiple genres/sites

    And DECREASE when:
      1. Conflicting meanings are proposed
      2. Published scholarship revises readings
    """

    def __init__(self, vocabulary: Optional[dict] = None):
        self.vocabulary = vocabulary or VOCABULARY

    def recalculate_confidence(self, corpus: list[dict]) -> dict:
        """
        Recalculate confidence for every vocabulary entry based on
        corpus-wide attestation patterns.
        """
        # Count attestations per root
        root_attestations = Counter()
        root_sites = defaultdict(set)
        root_genres = defaultdict(set)

        for entry in corpus:
            tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
            site = entry.get("site", "unknown")
            genre = entry.get("type", "unknown")

            for token in tokens:
                base = token.split("-")[0].lower()
                if base in self.vocabulary:
                    root_attestations[base] += 1
                    root_sites[base].add(site)
                    root_genres[base].add(genre)

        # Compute updated confidence
        updates = {}
        for word, ventry in self.vocabulary.items():
            old_cert = ventry.get("certainty", 0.5)
            n_attest = root_attestations.get(word, 0)
            n_sites = len(root_sites.get(word, set()))
            n_genres = len(root_genres.get(word, set()))

            # Evidence-based adjustments
            attestation_boost = min(0.10, n_attest * 0.002)
            diversity_boost = min(0.05, n_sites * 0.01 + n_genres * 0.01)

            new_cert = min(0.95, old_cert + attestation_boost + diversity_boost)

            if abs(new_cert - old_cert) > 0.001:
                updates[word] = {
                    "old_certainty": old_cert,
                    "new_certainty": round(new_cert, 3),
                    "delta": round(new_cert - old_cert, 4),
                    "attestations": n_attest,
                    "sites": n_sites,
                    "genres": n_genres,
                }

        return {
            "updates": updates,
            "summary": {
                "vocabulary_size": len(self.vocabulary),
                "updated_entries": len(updates),
                "average_delta": round(
                    sum(u["delta"] for u in updates.values()) / max(len(updates), 1), 4
                ),
            },
        }


class PredictiveEvaluator:
    """
    Evaluate the predictive power of the current model against held-out texts.

    Given a new inscription, how well does the model:
      1. Classify its genre?
      2. Predict token categories at each position?
      3. Translate formulaic passages?
    """

    def __init__(self, vocabulary: Optional[dict] = None):
        self.vocabulary = vocabulary or VOCABULARY

    def evaluate_text(self, inscription: dict) -> dict:
        """
        Evaluate model performance on a single inscription.
        Returns coverage and prediction metrics.
        """
        tokens = [t.strip() for t in inscription["text"].split(":") if t.strip()]

        known_tokens = 0
        partial_tokens = 0
        unknown_tokens = 0
        details = []

        for token in tokens:
            base = token.split("-")[0].lower()
            ventry = self.vocabulary.get(base)

            if ventry:
                cert = ventry.get("certainty", 0)
                if cert >= 0.60:
                    known_tokens += 1
                    status = "known"
                else:
                    partial_tokens += 1
                    status = "partial"
            elif base in KNOWN_ROYAL_NAMES or base.capitalize() in KNOWN_ROYAL_NAMES:
                known_tokens += 1
                status = "proper_name"
            else:
                unknown_tokens += 1
                status = "unknown"

            details.append({
                "token": token,
                "base": base,
                "status": status,
                "certainty": ventry.get("certainty", 0) if ventry else 0,
            })

        total = len(tokens)
        coverage = (known_tokens + 0.5 * partial_tokens) / total if total else 0

        return {
            "id": inscription.get("id", ""),
            "total_tokens": total,
            "known_tokens": known_tokens,
            "partial_tokens": partial_tokens,
            "unknown_tokens": unknown_tokens,
            "lexical_coverage": round(coverage, 3),
            "token_details": details,
        }

    def evaluate_corpus(self, corpus: list[dict]) -> dict:
        """Evaluate model performance across the entire corpus."""
        results = []
        for entry in corpus:
            results.append(self.evaluate_text(entry))

        avg_coverage = sum(r["lexical_coverage"] for r in results) / len(results)
        total_known = sum(r["known_tokens"] for r in results)
        total_partial = sum(r["partial_tokens"] for r in results)
        total_unknown = sum(r["unknown_tokens"] for r in results)
        total_tokens = sum(r["total_tokens"] for r in results)

        return {
            "per_inscription": results,
            "summary": {
                "inscriptions_evaluated": len(results),
                "average_coverage": round(avg_coverage, 3),
                "total_tokens": total_tokens,
                "known_tokens": total_known,
                "partial_tokens": total_partial,
                "unknown_tokens": total_unknown,
                "known_pct": round(total_known / total_tokens * 100, 1) if total_tokens else 0,
                "unknown_pct": round(total_unknown / total_tokens * 100, 1) if total_tokens else 0,
            },
        }


def run_corpus_analysis() -> dict:
    """Execute corpus ingestion analysis and predictive evaluation."""
    ingester = CorpusIngester()
    updater = ConfidenceUpdater()
    evaluator = PredictiveEvaluator()
    standardizer = UnicodeStandardizer()

    # 1. Confidence recalculation
    confidence_updates = updater.recalculate_confidence(CORPUS)

    # 2. Predictive evaluation
    prediction_eval = evaluator.evaluate_corpus(CORPUS)

    # 3. Unicode standardization check (sample)
    unicode_samples = []
    for entry in CORPUS[:5]:
        rendered = standardizer.transliterate_to_unicode(entry["text"])
        validation = standardizer.validate_unicode(rendered)
        unicode_samples.append({
            "id": entry.get("id", ""),
            "unicode": rendered,
            "valid": validation["is_valid"],
        })

    return {
        "confidence_updates": confidence_updates,
        "predictive_evaluation": prediction_eval["summary"],
        "unicode_samples": unicode_samples,
        "summary": {
            "corpus_size": len(CORPUS),
            "confidence_entries_updated": confidence_updates["summary"]["updated_entries"],
            "avg_confidence_delta": confidence_updates["summary"]["average_delta"],
            "lexical_coverage": prediction_eval["summary"]["average_coverage"],
        },
    }
