"""
Module 1: Expanded Nilo-Saharan Comparative Lexicon & Cognate Mining
=====================================================================
Systematically extends the comparative database by:
  1. Mining candidate cognates via regular sound correspondences (Rilly 2007, 2010)
  2. Semantic anchoring: triangulating unknown tokens from known "islands of certainty"
  3. Incorporating Midob, Birgid, Taman, Nara alongside Nubian core

References:
  - Rilly 2007 "La langue du royaume de Méroé"
  - Rilly 2010 "Le méroïtique et sa famille linguistique"
  - Bender 1996 "The Nilo-Saharan Languages"
  - Rilly & de Voogt 2012 "The Meroitic Language and Writing System"
"""

from collections import defaultdict
from typing import Optional

from decipher import (
    VOCABULARY, NUBIAN_COMPARATIVE, EASTERN_SUDANIC_COMPARATIVE,
    MORPHEMES, CORPUS,
)
from decipher.comparative import SoundLawEngine, SOUND_CORRESPONDENCES


# ═══════════════════════════════════════════════════════════════════════════════
# Extended sound correspondences (Rilly 2010: Ch.6; Bender 1996)
# ═══════════════════════════════════════════════════════════════════════════════

EXTENDED_SOUND_CORRESPONDENCES = SOUND_CORRESPONDENCES + [
    # Rilly 2010: labial/labiodental shifts
    {"meroitic": "b", "nubian": "w", "environment": "before round vowel", "confidence": 0.5},
    {"meroitic": "d", "nubian": "r", "environment": "intervocalic (Nobiin rhotacism)", "confidence": 0.6},
    # Rilly 2010: palatalization pathway
    {"meroitic": "s", "nubian": "t", "environment": "before i (palatal assimilation)", "confidence": 0.5},
    # Meroitic h ~ Nubian kh in divine/ritual context
    {"meroitic": "h", "nubian": "kh", "environment": "sacral vocabulary", "confidence": 0.4},
    # Vowel harmony: Meroitic o ~ Nubian u (common in NES branch)
    {"meroitic": "o", "nubian": "u", "environment": "back-vowel harmony", "confidence": 0.6},
    # Nilo-Saharan *d > Meroitic t / Nubian d  (fortition in Meroitic)
    {"meroitic": "t", "nubian": "t", "environment": "word-initial (identity)", "confidence": 0.9},
    # Final e/i raising
    {"meroitic": "e", "nubian": "a", "environment": "unstressed final", "confidence": 0.4},
]


# ═══════════════════════════════════════════════════════════════════════════════
# Extended Nubian comparative data (new entries)
# Adds ~20 new entries beyond the 16 in NUBIAN_COMPARATIVE
# ═══════════════════════════════════════════════════════════════════════════════

EXTENDED_NUBIAN_COMPARATIVE = {
    # ── Government & Social ──────────────────────────────────────────────────
    "qore": {
        "meroitic_meaning": "ruler, king",
        "certainty": 0.55,
        "old_nubian": "ourou/ouran", "old_nubian_meaning": "king/chief",
        "nobiin": "guur-ti", "nobiin_meaning": "great one / chief",
        "dongolawi": "goor", "dongolawi_meaning": "great",
        "midob": "", "midob_meaning": "",
        "proto_nubian": "*gur(?)",
        "notes": "Possible semantic extension from 'great' → 'ruler'. "
                 "Cf. Rilly 2010:411 links qore to NES *gur 'great'.",
    },
    "kdke": {
        "meroitic_meaning": "queen / Candace",
        "certainty": 0.45,
        "old_nubian": "kide-ke", "old_nubian_meaning": "woman-GEN (of women?)",
        "nobiin": "kede-ki", "nobiin_meaning": "girl's",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*kiDE-ke(?)",
        "notes": "Possibly compounds kdi 'woman' + -ke (morpheme). "
                 "Greek Kandake may preserve proto-form more faithfully.",
    },
    "ked": {
        "meroitic_meaning": "to slaughter",
        "certainty": 0.80,
        "old_nubian": "ked/kid", "old_nubian_meaning": "to cut/kill",
        "nobiin": "kiid", "nobiin_meaning": "to cut",
        "dongolawi": "kud", "dongolawi_meaning": "to cut",
        "midob": "kid", "midob_meaning": "to sever",
        "proto_nubian": "*ked",
        "notes": "Confirmed by Nastasen stele Egyptian parallel. "
                 "One of the most secure verbal cognates (Griffith 1917:167).",
    },
    "erk": {
        "meroitic_meaning": "to seize / take captive",
        "certainty": 0.75,
        "old_nubian": "er/ir", "old_nubian_meaning": "to take/seize",
        "nobiin": "iir", "nobiin_meaning": "to take",
        "dongolawi": "er", "dongolawi_meaning": "to take",
        "proto_nubian": "*er",
        "notes": "Confirmed by Nastasen parallel. Root *er with extension -k.",
    },
    "tele": {
        "meroitic_meaning": "to go / march",
        "certainty": 0.50,
        "old_nubian": "tal/tel", "old_nubian_meaning": "to go",
        "nobiin": "teel", "nobiin_meaning": "to go/walk",
        "dongolawi": "tol", "dongolawi_meaning": "to go",
        "proto_nubian": "*tel",
        "notes": "Tentative: Rilly 2010:420 links with NES *tel 'to go'.",
    },
    "dme": {
        "meroitic_meaning": "to establish / found",
        "certainty": 0.40,
        "old_nubian": "dime/dim", "old_nubian_meaning": "to set/place",
        "nobiin": "diim", "nobiin_meaning": "to put down",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*dim(?)",
        "notes": "Tentative. Temple-building context at Jebel Barkal.",
    },
    "he": {
        "meroitic_meaning": "to pour (libation)",
        "certainty": 0.45,
        "old_nubian": "hee/hi", "old_nubian_meaning": "to pour",
        "nobiin": "hii", "nobiin_meaning": "to pour water",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*he(?)",
        "notes": "Ritual context: libation offerings. Cf. Rilly 2007.",
    },
    "tedke": {
        "meroitic_meaning": "east / eastern",
        "certainty": 0.70,
        "old_nubian": "teddi", "old_nubian_meaning": "east / sunrise",
        "nobiin": "teedi", "nobiin_meaning": "east",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*tedi",
        "notes": "Directional pair with tenke 'west'. Regular -ke suffix.",
    },
    "mde": {
        "meroitic_meaning": "to die",
        "certainty": 0.50,
        "old_nubian": "mude", "old_nubian_meaning": "to die",
        "nobiin": "muud", "nobiin_meaning": "to die",
        "dongolawi": "mud", "dongolawi_meaning": "to die",
        "midob": "mod", "midob_meaning": "to die",
        "proto_nubian": "*mud",
        "notes": "Common Nilo-Saharan root. Meroitic m-d-e with vowel harmony.",
    },
    "tke": {
        "meroitic_meaning": "to give birth / offering",
        "certainty": 0.50,
        "old_nubian": "tik/tig", "old_nubian_meaning": "to produce / bring forth",
        "nobiin": "tiig", "nobiin_meaning": "to produce",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*tig(?)",
        "notes": "Dual usage: birth/offering in funerary context.",
    },
    "prite": {
        "meroitic_meaning": "life",
        "certainty": 0.75,
        "old_nubian": "biri/piri", "old_nubian_meaning": "life/soul",
        "nobiin": "fiir", "nobiin_meaning": "life/soul",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*pir",
        "notes": "Key funerary term. Sound shift p ~ f regular in Nobiin.",
    },
    "mete": {
        "meroitic_meaning": "born of / son of",
        "certainty": 0.55,
        "old_nubian": "met/mid", "old_nubian_meaning": "child of",
        "nobiin": "meed", "nobiin_meaning": "born of",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*met(?)",
        "notes": "Filiation marker in genealogical texts.",
    },
    "wide": {
        "meroitic_meaning": "brother",
        "certainty": 0.55,
        "old_nubian": "weide", "old_nubian_meaning": "brother",
        "nobiin": "weed", "nobiin_meaning": "brother",
        "dongolawi": "wad", "dongolawi_meaning": "brother",
        "proto_nubian": "*wed",
        "notes": "Kinship term. Regular correspondence.",
    },
    "hr": {
        "meroitic_meaning": "to praise / be favored",
        "certainty": 0.40,
        "old_nubian": "hir", "old_nubian_meaning": "to praise/bless",
        "nobiin": "", "nobiin_meaning": "",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*hir(?)",
        "notes": "Tentative. Funerary context: 'praised by the gods'.",
    },
    "dmke": {
        "meroitic_meaning": "temple / holy place",
        "certainty": 0.45,
        "old_nubian": "dimme", "old_nubian_meaning": "holy place/church",
        "nobiin": "", "nobiin_meaning": "",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*dim-ke(?)",
        "notes": "Tentative. ON dimme is a Christian-era borrowing; "
                 "possible shared Nilo-Saharan root *dim 'sacred place'.",
    },
    "ato": {
        "meroitic_meaning": "offering table / altar",
        "certainty": 0.50,
        "old_nubian": "atou", "old_nubian_meaning": "table/platform",
        "nobiin": "", "nobiin_meaning": "",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*atow(?)",
        "notes": "Archaeological context: offering tables at Karanog, Meroe.",
    },
    "tkke": {
        "meroitic_meaning": "to conquer / subdue",
        "certainty": 0.30,
        "old_nubian": "tekke", "old_nubian_meaning": "to strike/hit",
        "nobiin": "tikkiir", "nobiin_meaning": "to strike",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*tek(?)",
        "notes": "Tentative. Military context only. May be semantic extension "
                 "from 'to strike' → 'to conquer'.",
    },
    "mke": {
        "meroitic_meaning": "to build / construct",
        "certainty": 0.40,
        "old_nubian": "mike/mig", "old_nubian_meaning": "to make/build",
        "nobiin": "miig", "nobiin_meaning": "to make",
        "dongolawi": "", "dongolawi_meaning": "",
        "proto_nubian": "*mig(?)",
        "notes": "Temple-building context: B4 of REM 1044.",
    },
    "s": {
        "meroitic_meaning": "his/her (3SG possessive)",
        "certainty": 0.65,
        "old_nubian": "-su/-si", "old_nubian_meaning": "his/her",
        "nobiin": "-si", "nobiin_meaning": "his/her",
        "dongolawi": "-si", "dongolawi_meaning": "his/her",
        "proto_nubian": "*-si",
        "notes": "Pronominal possessive. Wide Nilo-Saharan distribution.",
    },
}

# Extended Eastern Sudanic (adds Taman, Nara, widening from 6 to 14 entries)
EXTENDED_EASTERN_SUDANIC = {
    "to": {"taman": "tu", "taman_meaning": "earth/land",
           "nara": "to", "nara_meaning": "ground"},
    "yi": {"taman": "yi", "taman_meaning": "water",
           "nara": "yo", "nara_meaning": "water"},
    "ate": {"taman": "", "taman_meaning": "",
            "nara": "aate", "nara_meaning": "food"},
    "kdi": {"taman": "", "taman_meaning": "",
            "nara": "kode", "nara_meaning": "woman"},
    "mlo": {"taman": "mol", "taman_meaning": "good",
            "nara": "", "nara_meaning": ""},
    "beke": {"taman": "bik", "taman_meaning": "to bear",
             "nara": "", "nara_meaning": ""},
    "mde": {"taman": "mud", "taman_meaning": "to die",
            "nara": "muda", "nara_meaning": "to die"},
    "ked": {"taman": "kid", "taman_meaning": "to cut",
            "nara": "ked", "nara_meaning": "to cut/sever"},
    "prite": {"taman": "pir", "taman_meaning": "soul",
              "nara": "", "nara_meaning": ""},
    "abr": {"taman": "awar", "taman_meaning": "person",
            "nara": "", "nara_meaning": ""},
    "sr": {"taman": "sur", "taman_meaning": "sister",
           "nara": "", "nara_meaning": ""},
    "tedke": {"taman": "ted", "taman_meaning": "sunrise/east",
              "nara": "", "nara_meaning": ""},
    "erk": {"taman": "", "taman_meaning": "",
            "nara": "er", "nara_meaning": "to take"},
    "wide": {"taman": "wad", "taman_meaning": "brother",
             "nara": "", "nara_meaning": ""},
}


class CognateMiner:
    """
    Systematically mine the Meroitic vocabulary for Nilo-Saharan cognates.

    Strategy:
      1. Apply extended sound laws to every unmatched root
      2. Score candidates against known Nubian lexicon
      3. Rank by phonological regularity + semantic plausibility
    """

    def __init__(self):
        self.sound_engine = SoundLawEngine(EXTENDED_SOUND_CORRESPONDENCES)
        # Merge all known Nubian forms into a lookup
        self.nubian_lexicon = self._build_nubian_lexicon()
        self.vocabulary = VOCABULARY
        self.existing_comparative = dict(NUBIAN_COMPARATIVE)
        self.extended_comparative = dict(EXTENDED_NUBIAN_COMPARATIVE)

    def _build_nubian_lexicon(self):
        """Build a comprehensive Nubian word → meaning lookup from all sources."""
        lex = {}
        for entry in NUBIAN_COMPARATIVE.values():
            for lang in ("old_nubian", "nobiin", "dongolawi", "midob", "birgid"):
                form = entry.get(lang, "")
                meaning = entry.get(f"{lang}_meaning", "")
                if form and meaning:
                    for f in form.split("/"):
                        lex[f.strip().lower()] = {
                            "meaning": meaning, "language": lang,
                        }
        for entry in EXTENDED_NUBIAN_COMPARATIVE.values():
            for lang in ("old_nubian", "nobiin", "dongolawi", "midob", "birgid"):
                form = entry.get(lang, "")
                meaning = entry.get(f"{lang}_meaning", "")
                if form and meaning:
                    for f in form.split("/"):
                        lex[f.strip().lower()] = {
                            "meaning": meaning, "language": lang,
                        }
        return lex

    def mine_new_cognates(self) -> list[dict]:
        """
        Apply sound laws to every VOCABULARY entry that lacks a comparative match.
        Return ranked list of proposed cognates.
        """
        proposals = []
        already_matched = (
            set(self.existing_comparative.keys()) |
            set(self.extended_comparative.keys())
        )

        for word, entry in self.vocabulary.items():
            if word in already_matched:
                continue
            candidates = self.sound_engine.apply_laws(word)
            for c in candidates[:8]:
                predicted = c["form"].lower()
                if predicted in self.nubian_lexicon:
                    nub = self.nubian_lexicon[predicted]
                    # Semantic plausibility: does the Nubian meaning fit?
                    sem_score = self._semantic_plausibility(
                        entry.get("category", ""), nub["meaning"]
                    )
                    proposals.append({
                        "meroitic_root": word,
                        "meroitic_meaning": entry.get("translation", ""),
                        "predicted_nubian_form": predicted,
                        "nubian_meaning": nub["meaning"],
                        "nubian_language": nub["language"],
                        "phonological_score": round(c["confidence"], 3),
                        "semantic_score": sem_score,
                        "combined_score": round(
                            c["confidence"] * 0.6 + sem_score * 0.4, 3
                        ),
                    })

        proposals.sort(key=lambda x: -x["combined_score"])
        return proposals

    def _semantic_plausibility(self, meroitic_category: str, nubian_meaning: str) -> float:
        """Score how plausible it is that a Nubian meaning maps to a Meroitic category."""
        cat = meroitic_category.lower()
        nm = nubian_meaning.lower()
        # Category-meaning affinity scores
        affinities = {
            "title": ["king", "chief", "ruler", "great", "lord"],
            "deity_name": ["god", "lord", "divine"],
            "offering": ["bread", "food", "water", "give", "pour"],
            "kinship": ["woman", "man", "sister", "brother", "child", "girl"],
            "adjective": ["good", "big", "great", "beautiful"],
            "verb": ["go", "cut", "take", "build", "die", "give", "pour",
                     "seize", "strike", "bear", "make"],
            "direction": ["east", "west", "sunrise", "sunset"],
            "noun": ["land", "earth", "gold", "temple", "table"],
            "pronoun": ["this", "that", "his", "her"],
            "number": ["one", "two"],
        }
        for category_key, keywords in affinities.items():
            if category_key in cat:
                if any(kw in nm for kw in keywords):
                    return 0.8
        # Fallback: partial match
        return 0.3

    def get_full_comparative_database(self) -> dict:
        """Return the complete merged comparative database (old + new)."""
        merged = dict(NUBIAN_COMPARATIVE)
        merged.update(EXTENDED_NUBIAN_COMPARATIVE)
        return merged

    def get_full_eastern_sudanic(self) -> dict:
        """Return the complete merged Eastern Sudanic database."""
        merged = dict(EASTERN_SUDANIC_COMPARATIVE)
        merged.update(EXTENDED_EASTERN_SUDANIC)
        return merged


class SemanticAnchor:
    """
    Use known "islands of certainty" to triangulate meanings of adjacent tokens.

    Method: For each unknown token in the corpus, examine its co-occurrence
    patterns with high-certainty tokens. If an unknown token consistently
    appears in the same slot as a known word of a particular semantic field,
    infer its probable category and meaning range.
    """

    def __init__(self):
        self.vocabulary = VOCABULARY
        self.certainty_threshold = 0.65  # "island" threshold

    def anchor_unknowns(self, corpus: list[dict]) -> list[dict]:
        """
        For every token with certainty < threshold, examine co-occurrence
        with high-certainty neighbors to propose semantic field membership.
        """
        # Build co-occurrence matrix: token → {neighbor_categories}
        cooccurrence = defaultdict(lambda: defaultdict(int))
        position_patterns = defaultdict(lambda: defaultdict(int))

        for entry in corpus:
            tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
            bases = [t.split("-")[0].lower() for t in tokens]

            for i, base in enumerate(bases):
                vocab_entry = self.vocabulary.get(base)
                if vocab_entry and vocab_entry.get("certainty", 0) >= self.certainty_threshold:
                    continue  # Skip known tokens — we want to anchor unknowns

                # Record categories of neighbors
                for offset in (-2, -1, 1, 2):
                    j = i + offset
                    if 0 <= j < len(bases):
                        neighbor = bases[j]
                        nv = self.vocabulary.get(neighbor)
                        if nv and nv.get("certainty", 0) >= self.certainty_threshold:
                            cooccurrence[base][nv["category"]] += 1

                # Record positional pattern
                rel_pos = i / len(tokens) if tokens else 0
                if rel_pos < 0.2:
                    position_patterns[base]["initial"] += 1
                elif rel_pos > 0.8:
                    position_patterns[base]["final"] += 1
                else:
                    position_patterns[base]["medial"] += 1

        # Propose semantic fields for unknowns
        proposals = []
        for token, cat_counts in cooccurrence.items():
            if not cat_counts:
                continue
            total = sum(cat_counts.values())
            top_cat = max(cat_counts, key=cat_counts.get)
            top_count = cat_counts[top_cat]
            confidence = top_count / total if total else 0

            # Position bias
            pos = position_patterns.get(token, {})
            dominant_position = max(pos, key=pos.get) if pos else "unknown"

            proposals.append({
                "token": token,
                "proposed_category": top_cat,
                "category_confidence": round(confidence, 3),
                "co_occurrence_count": total,
                "dominant_position": dominant_position,
                "neighbor_categories": dict(cat_counts),
                "current_vocabulary_entry": bool(self.vocabulary.get(token)),
            })

        proposals.sort(key=lambda x: (-x["category_confidence"], -x["co_occurrence_count"]))
        return proposals

    def triangulate_meanings(self, corpus: list[dict]) -> list[dict]:
        """
        For unknown tokens that appear between two known tokens, infer
        likely meaning from the semantic frame.
        """
        trigrams = defaultdict(lambda: defaultdict(int))

        for entry in corpus:
            tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
            bases = [t.split("-")[0].lower() for t in tokens]

            for i in range(1, len(bases) - 1):
                mid = bases[i]
                mid_v = self.vocabulary.get(mid)
                if mid_v and mid_v.get("certainty", 0) >= self.certainty_threshold:
                    continue  # Already known

                left = bases[i - 1]
                right = bases[i + 1]
                left_v = self.vocabulary.get(left)
                right_v = self.vocabulary.get(right)

                if not (left_v and right_v):
                    continue
                if left_v.get("certainty", 0) < self.certainty_threshold:
                    continue
                if right_v.get("certainty", 0) < self.certainty_threshold:
                    continue

                frame = (left_v["category"], right_v["category"])
                trigrams[mid][frame] += 1

        results = []
        for token, frames in trigrams.items():
            total = sum(frames.values())
            top_frame = max(frames, key=frames.get)
            results.append({
                "token": token,
                "left_category": top_frame[0],
                "right_category": top_frame[1],
                "frame_count": frames[top_frame],
                "total_occurrences": total,
                "inferred_role": self._infer_from_frame(top_frame),
            })

        results.sort(key=lambda x: -x["total_occurrences"])
        return results

    def _infer_from_frame(self, frame: tuple) -> str:
        """Infer the probable syntactic role from a (left_cat, right_cat) frame."""
        left, right = frame
        if "deity" in left.lower() and "title" in right.lower():
            return "epithet or divine attribute"
        if "title" in left.lower() and "name" in right.lower():
            return "honorific or filiation marker"
        if "offering" in left.lower() and "verb" in right.lower():
            return "offering item or quantity"
        if "adjective" in left.lower() or "adjective" in right.lower():
            return "noun modified by adjective"
        return "unknown (needs manual review)"


def run_cognate_mining() -> dict:
    """Execute the full cognate mining pipeline. Returns structured results."""
    miner = CognateMiner()
    anchor = SemanticAnchor()

    # 1. Mine new cognates
    new_cognates = miner.mine_new_cognates()

    # 2. Get full databases
    full_nubian = miner.get_full_comparative_database()
    full_es = miner.get_full_eastern_sudanic()

    # 3. Semantic anchoring
    anchored = anchor.anchor_unknowns(CORPUS)
    triangulated = anchor.triangulate_meanings(CORPUS)

    return {
        "new_cognate_proposals": new_cognates,
        "extended_nubian_database": full_nubian,
        "extended_eastern_sudanic": full_es,
        "semantic_anchoring": anchored[:30],
        "triangulated_meanings": triangulated[:20],
        "summary": {
            "original_nubian_entries": len(NUBIAN_COMPARATIVE),
            "extended_nubian_entries": len(full_nubian),
            "original_es_entries": len(EASTERN_SUDANIC_COMPARATIVE),
            "extended_es_entries": len(full_es),
            "new_cognate_proposals": len(new_cognates),
            "tokens_anchored": len(anchored),
            "tokens_triangulated": len(triangulated),
        },
    }
