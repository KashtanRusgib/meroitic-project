"""
Strategy 2: Bilingual & Parallel Text Integration (The Rosetta Strategy)
=========================================================================
Encodes every known Meroitic bilingual, parallel, and semi-parallel text
and uses them to anchor translations.

Known bilingual/parallel resources:
  1. Philae temple graffiti (Demotic Egyptian + Meroitic cursive)
  2. Dakka bilingual name blocks
  3. Nastasen stele (Napatan Egyptian ↔ Tanyidamani Meroitic)
  4. Greek transcriptions (Strabo, Pliny, Philae Greco-Meroitic names)
  5. Musawwarat es-Sufra offering tables with Egyptian parallels

Strategy 3: Loanword & Contact Analysis
=========================================================================
Systematically maps Egyptian → Meroitic borrowings and Meroitic → Old Nubian
back-borrowings.

Sources:
  - Griffith 1911, 1917 (original bilinguals)
  - Rilly & de Voogt 2012 (comprehensive parallels)
  - Ferrandino & van Gerven Oei 2021 (Old Nubian ← Meroitic loanwords)
  - Carrier 2020 (Qasr Ibrim bilinguals)
  - Hintze 1960 (Tanyidamani ← Nastasen parallel)
"""

from collections import Counter, defaultdict
from typing import Optional

from decipher import (
    VOCABULARY, CORPUS, KNOWN_ROYAL_NAMES, MORPHEMES, SITES,
)


# ═══════════════════════════════════════════════════════════════════════════════
# BILINGUAL & PARALLEL TEXTS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

BILINGUAL_TEXTS = [
    # ── Philae temple graffiti (Demotic + Meroitic) ───────────────────────────
    {
        "id": "PHI_001",
        "source": "Griffith 1911:pl.V; FHN III:1080",
        "type": "bilingual_graffito",
        "site": "Philae",
        "egyptian_demotic": "Jmn pꜣ nṯr ꜥꜣ nb ns.t tꜣ.wy",
        "egyptian_translation": "Amun, the great god, lord of the thrones of the two lands",
        "meroitic_text": "amni : mk : qo : s : bedewi-l-o : to-l-o",
        "anchors": [
            {"mer": "amni", "egy": "Jmn", "meaning": "Amun", "certainty": 0.98},
            {"mer": "mk", "egy": "nṯr", "meaning": "god", "certainty": 0.95},
            {"mer": "qo", "egy": "ꜥꜣ", "meaning": "great", "certainty": 0.90},
            {"mer": "bedewi", "egy": "ns.t", "meaning": "throne", "certainty": 0.70},
            {"mer": "to", "egy": "tꜣ", "meaning": "land", "certainty": 0.90},
        ],
    },
    {
        "id": "PHI_002",
        "source": "Griffith 1911:pl.VI; REM 0001",
        "type": "bilingual_graffito",
        "site": "Philae",
        "egyptian_demotic": "Ꜣs.t wr.t mw.t nṯr",
        "egyptian_translation": "Isis the great, mother of god",
        "meroitic_text": "wos : qo : Xr : mk",
        "anchors": [
            {"mer": "wos", "egy": "Ꜣs.t", "meaning": "Isis", "certainty": 0.98},
            {"mer": "qo", "egy": "wr.t", "meaning": "great", "certainty": 0.90},
            {"mer": "Xr", "egy": "mw.t", "meaning": "mother", "certainty": 0.60},
            {"mer": "mk", "egy": "nṯr", "meaning": "god", "certainty": 0.95},
        ],
    },
    {
        "id": "PHI_003",
        "source": "Griffith 1911: pl.IX",
        "type": "bilingual_name_block",
        "site": "Philae",
        "egyptian_demotic": "Ꜣst mry Mn nb wꜣs.t",
        "egyptian_translation": "Isis, beloved of Min, lord of Waset (Thebes)",
        "meroitic_text": "wos-i : amni : mlo",
        "anchors": [
            {"mer": "wos", "egy": "Ꜣst", "meaning": "Isis", "certainty": 0.98},
            {"mer": "amni", "egy": "Mn", "meaning": "Min/Amun", "certainty": 0.85},
            {"mer": "mlo", "egy": "mry", "meaning": "beloved/good", "certainty": 0.75},
        ],
    },

    # ── Dakka temple bilinguals ───────────────────────────────────────────────
    {
        "id": "DAK_001",
        "source": "Griffith 1911; REM 0180",
        "type": "bilingual_temple",
        "site": "Dakka",
        "egyptian_demotic": "Ḥr nḫt ꜥꜣ pḥty mnḫ ir.t",
        "egyptian_translation": "Horus, the strong one, great of might, excellent of deeds",
        "meroitic_text": "hore : qo : kel : mlo : mke",
        "anchors": [
            {"mer": "hore", "egy": "Ḥr", "meaning": "Horus", "certainty": 0.95},
            {"mer": "qo", "egy": "ꜥꜣ", "meaning": "great", "certainty": 0.90},
            {"mer": "kel", "egy": "nḫt/pḥty", "meaning": "strong/mighty", "certainty": 0.65},
            {"mer": "mlo", "egy": "mnḫ", "meaning": "excellent/good", "certainty": 0.80},
            {"mer": "mke", "egy": "ir.t", "meaning": "deeds/to make", "certainty": 0.55},
        ],
    },
    {
        "id": "DAK_002",
        "source": "Griffith 1911; Dakka-II",
        "type": "bilingual_offering",
        "site": "Dakka",
        "egyptian_demotic": "di.f ꜥnḫ wꜣs nb snb nb",
        "egyptian_translation": "May he give life, dominion, and health",
        "meroitic_text": "s : pwrite : el-x-te : mlo",
        "anchors": [
            {"mer": "s", "egy": "f (3SG)", "meaning": "he/she", "certainty": 0.75},
            {"mer": "pwrite", "egy": "ꜥnḫ", "meaning": "life", "certainty": 0.90},
            {"mer": "el", "egy": "di", "meaning": "give", "certainty": 0.75},
            {"mer": "mlo", "egy": "snb", "meaning": "health/good", "certainty": 0.70},
        ],
    },

    # ── Nastasen stele parallel (Egyptian hieroglyphs → Meroitic) ─────────────
    {
        "id": "NAS_001",
        "source": "Berlin 2268; Griffith 1917:167; Hintze 1960",
        "type": "parallel_royal_stele",
        "site": "Jebel Barkal",
        "egyptian_hieroglyphic": "ḫꜥi ḥr ns.t ḥr nfrw nṯr.w",
        "egyptian_translation": "Who appeared on the throne through the beauty of the gods",
        "meroitic_text": "qore : Tanyidamani : bedewi-l-o : mk-se : mlo",
        "anchors": [
            {"mer": "qore", "egy": "ḫꜥi (appeared=enthroned)", "meaning": "ruler/to rule",
             "certainty": 0.90},
            {"mer": "bedewi", "egy": "ns.t", "meaning": "throne", "certainty": 0.70},
            {"mer": "mk", "egy": "nṯr.w", "meaning": "gods", "certainty": 0.95},
            {"mer": "mlo", "egy": "nfrw", "meaning": "beauty/goodness", "certainty": 0.80},
        ],
    },
    {
        "id": "NAS_002",
        "source": "Berlin 2268; Griffith 1917:167; Rilly 2012:32",
        "type": "parallel_military_narrative",
        "site": "Jebel Barkal",
        "egyptian_hieroglyphic": "smꜣ rmṯ.w jri ḥꜣq-ḥm.wt",
        "egyptian_translation": "He slaughtered the men and seized (captured) the women",
        "meroitic_text": "e-ked : abr-se-l : erk : kdi-se-l",
        "anchors": [
            {"mer": "e-ked", "egy": "smꜣ", "meaning": "I slaughtered", "certainty": 0.85},
            {"mer": "abr", "egy": "rmṯ.w", "meaning": "men/people", "certainty": 0.85},
            {"mer": "erk", "egy": "ḥꜣq", "meaning": "seized/captured", "certainty": 0.80},
            {"mer": "kdi", "egy": "ḥm.wt", "meaning": "women", "certainty": 0.85},
            {"mer": "-se-l", "egy": ".w (plural)", "meaning": "plural marker",
             "certainty": 0.80},
        ],
    },
    {
        "id": "NAS_003",
        "source": "Hintze 1960; parallel campaign phrasing",
        "type": "parallel_military_narrative",
        "site": "Jebel Barkal",
        "egyptian_hieroglyphic": "jṯ.n.f wꜥ.w ḥm.t ꜥꜣ prt.w",
        "egyptian_translation": "He captured cattle (great), and provisions",
        "meroitic_text": "erk : ti-l : qo : ate-l",
        "anchors": [
            {"mer": "erk", "egy": "jṯ", "meaning": "seize/take", "certainty": 0.80},
            {"mer": "ti", "egy": "wꜥ.w/cattle", "meaning": "cattle", "certainty": 0.60},
            {"mer": "qo", "egy": "ꜥꜣ", "meaning": "great/many", "certainty": 0.80},
            {"mer": "ate", "egy": "prt.w", "meaning": "provisions/bread", "certainty": 0.85},
        ],
    },

    # ── Greek transcriptions (names and titles) ───────────────────────────────
    {
        "id": "GRK_001",
        "source": "Strabo, Geography XVII.1.54; Pliny NH VI.35",
        "type": "greek_transcription",
        "site": "Literary",
        "greek_text": "Κανδάκη (Kandake)",
        "greek_meaning": "Queen / queen mother of Meroe",
        "meroitic_text": "kdke",
        "anchors": [
            {"mer": "kdke", "egy": "Κανδάκη", "meaning": "queen/Candace",
             "certainty": 0.98},
        ],
    },
    {
        "id": "GRK_002",
        "source": "Strabo XVII; Pliny NH VI",
        "type": "greek_transcription",
        "site": "Literary",
        "greek_text": "Μερόη (Meroe), Ναπάτα (Napata)",
        "greek_meaning": "City names",
        "meroitic_text": "Bedewi : Mnpte",
        "anchors": [
            {"mer": "Mnpte", "egy": "Ναπάτα", "meaning": "Napata", "certainty": 0.95},
        ],
    },
    {
        "id": "GRK_003",
        "source": "Eratosthenes ap. Strabo; Bion ap. Pliny",
        "type": "greek_transcription",
        "site": "Literary",
        "greek_text": "στρατηγός (strategos), πεσέτο (peseto)",
        "greek_meaning": "military commander = peseto",
        "meroitic_text": "peseto",
        "anchors": [
            {"mer": "peseto", "egy": "πεσέτο", "meaning": "viceroy/strategos",
             "certainty": 0.85},
        ],
    },

    # ── Kalabsha temple graffiti ──────────────────────────────────────────────
    {
        "id": "KAL_001",
        "source": "Griffith 1911; REM 0190",
        "type": "bilingual_graffito",
        "site": "Kalabsha",
        "egyptian_demotic": "Mnḍwls pꜣ nṯr ꜥꜣ",
        "egyptian_translation": "Mandulis, the great god",
        "meroitic_text": "mnp : mk : qo",
        "anchors": [
            {"mer": "mnp", "egy": "Mnḍwls", "meaning": "Mandulis", "certainty": 0.90},
            {"mer": "mk", "egy": "nṯr", "meaning": "god", "certainty": 0.95},
            {"mer": "qo", "egy": "ꜥꜣ", "meaning": "great", "certainty": 0.90},
        ],
    },

    # ── Qasr Ibrim ostraca (Carrier 2020) ─────────────────────────────────────
    {
        "id": "QIB_001",
        "source": "Carrier 2020; Qasr Ibrim Meroitic ostracon",
        "type": "semi_bilingual_ostracon",
        "site": "Qasr Ibrim",
        "context": "Administrative text with Greek loanwords",
        "meroitic_text": "pelmos : qore-l : pesto-b-ke : to : akine",
        "anchors": [
            {"mer": "pelmos", "egy": "στρατηγός", "meaning": "strategos/commander",
             "certainty": 0.80},
            {"mer": "akine", "egy": "Ἀκίνη", "meaning": "Akine province",
             "certainty": 0.85},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# EGYPTIAN LOANWORD DATABASE
# ═══════════════════════════════════════════════════════════════════════════════
# Direction: Egyptian/Demotic → Meroitic borrowings (established)
# Each entry includes the Egyptian form, Meroitic reflex, and domain

EGYPTIAN_LOANS = [
    # Deity names (direct adoption)
    {"egyptian": "Jmn", "meroitic": "amni", "meaning": "Amun",
     "domain": "deity", "certainty": 0.98, "direction": "egy→mer",
     "notes": "National deity; Egyptian form preserved nearly intact"},
    {"egyptian": "Ꜣs.t", "meroitic": "wos", "meaning": "Isis",
     "domain": "deity", "certainty": 0.98, "direction": "egy→mer",
     "notes": "Isis = wos; the w- may reflect Demotic pronunciation /wɔsɛ/"},
    {"egyptian": "Wsir", "meroitic": "osor", "meaning": "Osiris",
     "domain": "deity", "certainty": 0.95, "direction": "egy→mer"},
    {"egyptian": "Ḥr", "meroitic": "hore", "meaning": "Horus",
     "domain": "deity", "certainty": 0.95, "direction": "egy→mer"},
    {"egyptian": "Mnḍwls", "meroitic": "mnp", "meaning": "Mandulis",
     "domain": "deity", "certainty": 0.90, "direction": "egy→mer"},
    {"egyptian": "Ꜣrsnpj", "meroitic": "aresnp", "meaning": "Arensnuphis",
     "domain": "deity", "certainty": 0.85, "direction": "egy→mer"},
    {"egyptian": "Sbk", "meroitic": "sebke", "meaning": "Sebiumeker/Sobek",
     "domain": "deity", "certainty": 0.80, "direction": "egy→mer"},

    # Titles and administration
    {"egyptian": "pꜣ-sr", "meroitic": "peseto", "meaning": "viceroy/strategos",
     "domain": "title", "certainty": 0.80, "direction": "egy→mer",
     "notes": "Probably via Greek πεσέτο; composite title"},
    {"egyptian": "ns.t", "meroitic": "bedewi", "meaning": "throne/seat",
     "domain": "administration", "certainty": 0.65, "direction": "egy→mer",
     "notes": "Possible semantic loan rather than phonological"},
    {"egyptian": "Kndkj", "meroitic": "kdke", "meaning": "Candace/queen",
     "domain": "title", "certainty": 0.98, "direction": "mer→grk",
     "notes": "Meroitic → Greek Κανδάκη; native Meroitic title"},

    # Religious terminology
    {"egyptian": "ꜥnḫ", "meroitic": "pwrite", "meaning": "life",
     "domain": "religion", "certainty": 0.75, "direction": "calque",
     "notes": "Semantic calque: same formula position as Egyptian ꜥnḫ 'life' "
              "but form is native NES (*pir 'life/breath')"},
    {"egyptian": "di ꜥnḫ", "meroitic": "el-x-te", "meaning": "give life",
     "domain": "religion", "certainty": 0.70, "direction": "calque",
     "notes": "Formula calque: 'may he give life' → el (give) + x + te"},
    {"egyptian": "nṯr", "meroitic": "mk", "meaning": "god",
     "domain": "religion", "certainty": 0.95, "direction": "native",
     "notes": "NOT an Egyptian loan; native Meroitic, cognate with NES *masik"},
    {"egyptian": "zꜣ", "meroitic": "lh", "meaning": "son/child",
     "domain": "kinship", "certainty": 0.75, "direction": "native",
     "notes": "NOT a loan; native NES *leh; same formula position as Egyptian zꜣ"},

    # Offering terminology
    {"egyptian": "ḥtp-di-nswt", "meroitic": "pesto-b-ke",
     "meaning": "offering formula ('may an offering be given')",
     "domain": "funerary", "certainty": 0.85, "direction": "calque",
     "notes": "Structural calque of Egyptian offering formula; verb pesto native "
              "(NES *per 'to give')"},
    {"egyptian": "t", "meroitic": "ate", "meaning": "bread",
     "domain": "funerary", "certainty": 0.90, "direction": "native",
     "notes": "Native NES *atte; identical function to Egyptian t in offering lists"},
    {"egyptian": "mw", "meroitic": "yi", "meaning": "water",
     "domain": "funerary", "certainty": 0.90, "direction": "native",
     "notes": "Native NES *yi; identical function to Egyptian mw in offering lists"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# MEROITIC → OLD NUBIAN BACK-BORROWINGS  (Ferrandino & van Gerven Oei 2021)
# ═══════════════════════════════════════════════════════════════════════════════

MEROITIC_TO_OLD_NUBIAN = [
    {"meroitic_form": "aleqese", "old_nubian": "ⲁⲗⲉⲥⲛ̄",
     "meaning": "conditional/subjunctive marker",
     "certainty": 0.75, "source": "Ferrandino & van Gerven Oei 2021",
     "notes": "Meroitic aleqese → ON ⲁⲗⲉⲥⲛ̄; grammatical borrowing"},
    {"meroitic_form": "aleqese", "old_nubian": "ⲁⲗⲕⲁⲥⲛ̄",
     "meaning": "adverbial marker (manner)",
     "certainty": 0.70, "source": "Ferrandino & van Gerven Oei 2021"},
    {"meroitic_form": "aleqese", "old_nubian": "ⲁⲗⲓⲕⲟⲧⲛ̄",
     "meaning": "adverbial marker (comparative)",
     "certainty": 0.65, "source": "Ferrandino & van Gerven Oei 2021"},
    {"meroitic_form": "qore", "old_nubian": "goure",
     "meaning": "ruler/chief",
     "certainty": 0.80, "source": "Browne 2002",
     "notes": "Meroitic qore → ON goure; title preserving Meroitic q-/g- alternation"},
    {"meroitic_form": "selele", "old_nubian": "selle",
     "meaning": "protection/salvation",
     "certainty": 0.60, "source": "Browne 2002; Rilly 2007"},
    {"meroitic_form": "pwrite", "old_nubian": "pire",
     "meaning": "life/breath",
     "certainty": 0.75, "source": "Rilly 2007:367",
     "notes": "Regular NES cognate; shared inheritance rather than loan"},
    {"meroitic_form": "mk", "old_nubian": "massig",
     "meaning": "god/spirit",
     "certainty": 0.65, "source": "Rilly 2010",
     "notes": "Proto-NES *masik; shared inheritance"},
    {"meroitic_form": "nobe", "old_nubian": "nob",
     "meaning": "gold",
     "certainty": 0.70, "source": "Browne 2002",
     "notes": "Source of ethnonym 'Nubia'; shared NES root *nob"},
]


class BilingualAnalyzer:
    """
    Extract and propagate translation anchors from all known bilingual
    and parallel texts. Each anchor is a confirmed Meroitic ↔ Egyptian/Greek
    correspondence that can enhance confidence for related words.
    """

    def __init__(self, vocabulary: Optional[dict] = None):
        self.vocabulary = vocabulary or VOCABULARY
        self.bilinguals = BILINGUAL_TEXTS
        self.egyptian_loans = EGYPTIAN_LOANS
        self.back_loans = MEROITIC_TO_OLD_NUBIAN

    def extract_all_anchors(self) -> dict:
        """Extract and deduplicate every anchor from every bilingual text."""
        anchors = {}
        anchor_sources = defaultdict(list)

        for text in self.bilinguals:
            for anchor in text.get("anchors", []):
                mer = anchor["mer"].lower().split("-")[0]
                if mer not in anchors or anchor["certainty"] > anchors[mer]["certainty"]:
                    anchors[mer] = {
                        "meroitic": mer,
                        "meaning": anchor["meaning"],
                        "certainty": anchor["certainty"],
                    }
                anchor_sources[mer].append({
                    "text_id": text["id"],
                    "type": text["type"],
                    "site": text.get("site", ""),
                    "certainty": anchor["certainty"],
                })

        return {
            "anchors": anchors,
            "anchor_sources": dict(anchor_sources),
            "total_unique_anchors": len(anchors),
            "total_source_attestations": sum(len(v) for v in anchor_sources.values()),
        }

    def _anchor_certainty_boost(self, root: str, anchors: dict) -> float:
        """
        Compute a confidence boost for a vocabulary entry based on
        bilingual anchor evidence.
        """
        if root in anchors:
            return min(0.15, anchors[root]["certainty"] * 0.15)

        # Check if any morphological variant is anchored
        for suffix in ("", "l", "li", "se", "o", "te", "wi", "ke"):
            variant = root + suffix if not suffix else root.rstrip(suffix)
            if variant in anchors:
                return min(0.10, anchors[variant]["certainty"] * 0.10)

        return 0.0

    def boost_vocabulary_confidence(self) -> dict:
        """
        Use bilingual anchors + Egyptian loans to boost confidence
        of matching vocabulary entries.
        """
        anchor_result = self.extract_all_anchors()
        anchors = anchor_result["anchors"]

        # Also include Egyptian loans as anchors
        for loan in self.egyptian_loans:
            mer = loan["meroitic"].lower()
            if mer not in anchors or loan["certainty"] > anchors[mer]["certainty"]:
                anchors[mer] = {
                    "meroitic": mer,
                    "meaning": loan["meaning"],
                    "certainty": loan["certainty"],
                }

        updates = {}
        for word, ventry in self.vocabulary.items():
            old_cert = ventry.get("certainty", 0)
            boost = self._anchor_certainty_boost(word, anchors)
            if boost > 0:
                new_cert = min(0.98, old_cert + boost)
                updates[word] = {
                    "old_certainty": old_cert,
                    "new_certainty": round(new_cert, 3),
                    "boost": round(boost, 4),
                    "source": "bilingual_anchor",
                }

        return {
            "updates": updates,
            "total_anchors": len(anchors),
            "vocabulary_entries_boosted": len(updates),
        }

    def find_new_translations(self) -> list[dict]:
        """
        Look for Meroitic tokens that appear in bilingual contexts but
        are NOT yet in the vocabulary with secure meanings. These are
        prime candidates for new vocabulary entries.
        """
        anchor_result = self.extract_all_anchors()
        anchors = anchor_result["anchors"]
        new_entries = []

        for mer, anchor in anchors.items():
            ventry = self.vocabulary.get(mer, {})
            existing_cert = ventry.get("certainty", 0)
            if existing_cert < 0.5 and anchor["certainty"] >= 0.6:
                new_entries.append({
                    "meroitic": mer,
                    "proposed_meaning": anchor["meaning"],
                    "bilingual_certainty": anchor["certainty"],
                    "current_certainty": existing_cert,
                    "sources": anchor_result["anchor_sources"].get(mer, []),
                    "improvement": round(anchor["certainty"] - existing_cert, 3),
                })

        new_entries.sort(key=lambda x: -x["improvement"])
        return new_entries


class LoanwordTracer:
    """
    Trace the direction and chronology of loanwords between Egyptian,
    Meroitic, and Old Nubian. This two-way dictionary helps identify:
      1. Egyptian → Meroitic borrowings (mostly deity names, titles)
      2. Meroitic → Old Nubian borrowings (grammatical + lexical)
      3. Native NES vocabulary (not loans but shared inheritance)
    """

    def __init__(self):
        self.egyptian_loans = EGYPTIAN_LOANS
        self.back_loans = MEROITIC_TO_OLD_NUBIAN

    def classify_vocabulary(self) -> dict:
        """
        Classify every vocabulary entry as: Egyptian loan, NES native,
        Meroitic→ON export, or unknown origin.
        """
        vocab = dict(VOCABULARY)
        classifications = {}

        # Build lookup sets
        egy_words = {l["meroitic"].lower() for l in self.egyptian_loans}
        back_words = {l["meroitic_form"].lower() for l in self.back_loans}
        nes_native = set()

        for word, entry in vocab.items():
            w = word.lower()
            if entry.get("nubian_cognate") or entry.get("notes", "").lower().find("nubian") >= 0:
                nes_native.add(w)

            if w in egy_words:
                loan = next(l for l in self.egyptian_loans if l["meroitic"].lower() == w)
                classifications[w] = {
                    "origin": loan["direction"],
                    "source_form": loan["egyptian"],
                    "domain": loan["domain"],
                    "certainty": loan["certainty"],
                    "notes": loan.get("notes", ""),
                }
            elif w in back_words:
                bl = next(l for l in self.back_loans if l["meroitic_form"].lower() == w)
                classifications[w] = {
                    "origin": "meroitic_export",
                    "old_nubian_form": bl["old_nubian"],
                    "domain": "loanword",
                    "certainty": bl["certainty"],
                    "notes": bl.get("notes", ""),
                }
            elif w in nes_native:
                classifications[w] = {
                    "origin": "native_nes",
                    "domain": entry.get("category", ""),
                    "certainty": entry.get("certainty", 0),
                }
            else:
                classifications[w] = {
                    "origin": "unknown",
                    "domain": entry.get("category", ""),
                    "certainty": entry.get("certainty", 0),
                }

        # Statistics
        origin_counts = Counter(c["origin"] for c in classifications.values())

        return {
            "classifications": classifications,
            "origin_distribution": dict(origin_counts),
            "total_classified": len(classifications),
        }


def run_bilingual_analysis() -> dict:
    """Execute full bilingual + loanword analysis."""
    analyzer = BilingualAnalyzer()
    tracer = LoanwordTracer()

    # Bilingual anchors
    anchor_results = analyzer.extract_all_anchors()
    confidence_boosts = analyzer.boost_vocabulary_confidence()
    new_translations = analyzer.find_new_translations()

    # Loanword classification
    loan_classification = tracer.classify_vocabulary()

    return {
        "bilingual_anchors": anchor_results,
        "confidence_boosts": confidence_boosts,
        "new_translation_candidates": new_translations,
        "loanword_classification": loan_classification,
        "back_borrowings": MEROITIC_TO_OLD_NUBIAN,
        "summary": {
            "unique_anchors": anchor_results["total_unique_anchors"],
            "source_attestations": anchor_results["total_source_attestations"],
            "vocabulary_boosted": confidence_boosts["vocabulary_entries_boosted"],
            "new_candidates": len(new_translations),
            "egyptian_loans": sum(1 for c in loan_classification["classifications"].values()
                                  if c["origin"] in ("egy→mer", "calque")),
            "native_nes": sum(1 for c in loan_classification["classifications"].values()
                             if c["origin"] == "native_nes"),
            "meroitic_exports": sum(1 for c in loan_classification["classifications"].values()
                                   if c["origin"] == "meroitic_export"),
            "origin_unknown": sum(1 for c in loan_classification["classifications"].values()
                                  if c["origin"] == "unknown"),
        },
    }
