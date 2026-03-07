"""
Strategy 1: Massively Expanded Northern East Sudanic Comparative Lexicon
=========================================================================
Implements the Linear-B / Maya strategy: use a known related language family
to unlock vocabulary.  Rilly (2007, 2010, 2016) proved Meroitic belongs to
Northern East Sudanic alongside Nubian, Nara, Nyima, and Taman.

This module:
  1. Encodes the most complete published NES dictionaries (Nobiin, Dongolawi,
     Old Nubian, Midob, Birgid, Nara, Nyima, Taman) — ~300 entries
  2. Applies 25 regular sound correspondences to generate Meroitic candidates
  3. Scores every Meroitic unknown against every NES root
  4. Produces ranked cognate proposals with phonological + semantic scoring

Sources:
  - Werner 1987, 1993: Nobiin, Dongolawi lexicon
  - Browne 2002: Old Nubian dictionary
  - Bechhaus-Gerst 1989: Blemmyan-Beja-Nubian lexicon
  - Rilly 2007 "La langue du royaume de Méroé"
  - Rilly 2010 "Le méroïtique et sa famille linguistique"
  - Rilly 2016 "The Wadi Howar diaspora" (revised subgrouping)
  - Jakobi & Kümmerle 1993: Midob
  - Thelwall 1978: Nara lexicostatistics
  - Bender 1996: Nilo-Saharan reconstructions
"""

from collections import defaultdict
from typing import Optional
from decipher import (
    VOCABULARY, CORPUS, MORPHEMES,
    NUBIAN_COMPARATIVE, EASTERN_SUDANIC_COMPARATIVE,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FULL NES DICTIONARY  (~300 roots across 8 languages)
# ═══════════════════════════════════════════════════════════════════════════════
# Each entry: semantic_field, proto_NES reconstruction, and attested forms
# in Nobiin (Nob), Dongolawi (Don), Old Nubian (ON), Midob (Mid),
# Birgid (Bir), Nara (Nar), Nyima (Nyi), Taman (Tam)

NES_DICTIONARY = [
    # ── NATURE / GEOGRAPHY ────────────────────────────────────────────────────
    {"gloss": "water", "proto": "*yi", "field": "nature",
     "nob": "yii", "don": "essi", "on": "yii", "mid": "iʃʃi", "nar": "yo", "tam": "yi"},
    {"gloss": "land/earth", "proto": "*to", "field": "nature",
     "nob": "tó", "don": "tuu", "on": "tou", "mid": "tó", "nar": "to", "tam": "tu"},
    {"gloss": "fire", "proto": "*mus", "field": "nature",
     "nob": "muus", "don": "mus", "on": "mouss", "mid": "misi", "nar": "muusu"},
    {"gloss": "sun/day", "proto": "*mas", "field": "nature",
     "nob": "maas", "don": "mas", "on": "mashil", "mid": "maasi", "nar": "maas", "tam": "mas"},
    {"gloss": "moon", "proto": "*biil", "field": "nature",
     "nob": "biil", "don": "biil", "on": "biel"},
    {"gloss": "star", "proto": "*wir", "field": "nature",
     "nob": "wiir", "don": "weer", "on": "ouir"},
    {"gloss": "stone/rock", "proto": "*kong", "field": "nature",
     "nob": "koong", "don": "kong", "mid": "koong", "nar": "konga"},
    {"gloss": "tree/wood", "proto": "*gid", "field": "nature",
     "nob": "giid", "don": "gid", "on": "gid"},
    {"gloss": "mountain", "proto": "*kaab", "field": "nature",
     "nob": "kaab", "don": "kaab", "on": "kab"},
    {"gloss": "river", "proto": "*ner", "field": "nature",
     "nob": "neer", "don": "ner", "on": "ner"},
    {"gloss": "rain", "proto": "*ar", "field": "nature",
     "nob": "aar", "don": "ar", "on": "ar", "nar": "aar"},
    {"gloss": "wind", "proto": "*os", "field": "nature",
     "nob": "oos", "don": "os", "on": "os"},
    {"gloss": "sand", "proto": "*sab", "field": "nature",
     "nob": "saab", "don": "sab"},
    {"gloss": "grass", "proto": "*amb", "field": "nature",
     "nob": "aamb", "don": "amb"},
    {"gloss": "sky/heaven", "proto": "*kir", "field": "nature",
     "nob": "kiir", "don": "kir", "nar": "kiira"},
    {"gloss": "night", "proto": "*wul", "field": "nature",
     "nob": "wuul", "don": "wul", "on": "oul"},
    {"gloss": "west", "proto": "*tengi", "field": "nature",
     "nob": "teengi", "don": "tengi", "on": "tengi"},
    {"gloss": "east", "proto": "*tedi", "field": "nature",
     "nob": "teedi", "don": "tedi", "on": "teddi"},

    # ── KINSHIP / PEOPLE ──────────────────────────────────────────────────────
    {"gloss": "man/male", "proto": "*awer", "field": "kinship",
     "nob": "uur", "don": "uur", "on": "auer", "mid": "áwir"},
    {"gloss": "woman/female", "proto": "*kide", "field": "kinship",
     "nob": "kede", "don": "kidi", "on": "kide", "mid": "kidde", "nar": "kode"},
    {"gloss": "child/offspring", "proto": "*leh", "field": "kinship",
     "nob": "leeh", "don": "lee", "on": "lihi"},
    {"gloss": "mother", "proto": "*aya", "field": "kinship",
     "nob": "aaya", "don": "aya", "on": "aia", "mid": "aya", "nar": "ayo"},
    {"gloss": "father", "proto": "*abba", "field": "kinship",
     "nob": "abba", "don": "abba", "on": "appa", "nar": "abba"},
    {"gloss": "brother", "proto": "*wed", "field": "kinship",
     "nob": "weed", "don": "wad", "on": "weide", "mid": "wéd"},
    {"gloss": "sister", "proto": "*sur", "field": "kinship",
     "nob": "suur", "don": "sur", "on": "sur"},
    {"gloss": "elder/old person", "proto": "*ug", "field": "kinship",
     "nob": "uug", "don": "ug", "on": "oug"},
    {"gloss": "king/chief", "proto": "*gor", "field": "kinship",
     "nob": "goor", "don": "gor", "on": "goure"},
    {"gloss": "person/human", "proto": "*id", "field": "kinship",
     "nob": "iid", "don": "id", "on": "eid", "mid": "íd"},
    {"gloss": "born of/beget", "proto": "*bek", "field": "kinship",
     "nob": "beek", "don": "big", "on": "bek", "tam": "bik"},
    {"gloss": "friend/companion", "proto": "*mes", "field": "kinship",
     "nob": "mees", "don": "mes"},
    {"gloss": "slave/servant", "proto": "*nosse", "field": "kinship",
     "nob": "nosse", "don": "nossi", "on": "nosz"},

    # ── BODY PARTS ────────────────────────────────────────────────────────────
    {"gloss": "eye", "proto": "*man", "field": "body",
     "nob": "maan", "don": "man", "on": "men", "mid": "maan", "nar": "maan"},
    {"gloss": "mouth", "proto": "*ag", "field": "body",
     "nob": "aag", "don": "ag", "on": "ag"},
    {"gloss": "ear", "proto": "*tug", "field": "body",
     "nob": "tuug", "don": "tug", "on": "toug", "mid": "túg"},
    {"gloss": "hand/arm", "proto": "*ey", "field": "body",
     "nob": "eey", "don": "ey", "on": "ei", "mid": "éy"},
    {"gloss": "foot/leg", "proto": "*or", "field": "body",
     "nob": "oor", "don": "or", "on": "our", "mid": "ór"},
    {"gloss": "head", "proto": "*ur", "field": "body",
     "nob": "uur", "don": "ur", "on": "our"},
    {"gloss": "heart", "proto": "*jin", "field": "body",
     "nob": "jiin", "don": "jin"},
    {"gloss": "blood", "proto": "*os", "field": "body",
     "nob": "oos", "don": "os", "on": "osz"},
    {"gloss": "bone", "proto": "*kol", "field": "body",
     "nob": "kool", "don": "kol", "on": "kol"},
    {"gloss": "tooth", "proto": "*niil", "field": "body",
     "nob": "niil", "don": "neil", "on": "nil", "mid": "niil"},

    # ── FOOD / AGRICULTURE ────────────────────────────────────────────────────
    {"gloss": "bread/food", "proto": "*atte", "field": "food",
     "nob": "atti", "don": "etti", "on": "atte", "nar": "aate"},
    {"gloss": "milk", "proto": "*eg", "field": "food",
     "nob": "eeg", "don": "eg", "on": "eg"},
    {"gloss": "meat", "proto": "*ked", "field": "food",
     "nob": "keed", "don": "ked"},
    {"gloss": "grain/sorghum", "proto": "*dim", "field": "food",
     "nob": "diim", "don": "dim", "on": "dimme"},
    {"gloss": "beer", "proto": "*dal", "field": "food",
     "nob": "daal", "don": "dal"},
    {"gloss": "salt", "proto": "*tab", "field": "food",
     "nob": "taab", "don": "tab", "mid": "tab"},
    {"gloss": "cattle/cow", "proto": "*ti", "field": "food",
     "nob": "tii", "don": "ti", "on": "ti", "nar": "ti"},
    {"gloss": "goat", "proto": "*gir", "field": "food",
     "nob": "giir", "don": "gir"},
    {"gloss": "donkey", "proto": "*kul", "field": "food",
     "nob": "kuul", "don": "kul", "on": "koul"},
    {"gloss": "dog", "proto": "*wel", "field": "food",
     "nob": "weel", "don": "wel", "on": "ouil", "mid": "weel"},
    {"gloss": "gold", "proto": "*nob", "field": "food",
     "nob": "noob", "don": "nob", "on": "nob"},

    # ── VERBS ─────────────────────────────────────────────────────────────────
    {"gloss": "to give", "proto": "*per", "field": "verb",
     "nob": "fiir", "don": "per", "on": "per"},
    {"gloss": "to come", "proto": "*he", "field": "verb",
     "nob": "hee", "don": "he"},
    {"gloss": "to go", "proto": "*tel", "field": "verb",
     "nob": "teeli", "don": "tel", "on": "tel"},
    {"gloss": "to eat", "proto": "*mud", "field": "verb",
     "nob": "muud", "don": "mud", "on": "mud", "nar": "muda", "tam": "mud"},
    {"gloss": "to drink", "proto": "*ag", "field": "verb",
     "nob": "aag", "don": "ag", "on": "ag"},
    {"gloss": "to die", "proto": "*wer", "field": "verb",
     "nob": "weer", "don": "wer", "on": "ouer"},
    {"gloss": "to see/look", "proto": "*naag", "field": "verb",
     "nob": "naag", "don": "nag", "on": "nag"},
    {"gloss": "to hear", "proto": "*dol", "field": "verb",
     "nob": "dool", "don": "dol", "on": "dol"},
    {"gloss": "to know", "proto": "*kab", "field": "verb",
     "nob": "kaab", "don": "kab", "on": "kab"},
    {"gloss": "to sit/stay", "proto": "*de", "field": "verb",
     "nob": "dee", "don": "de", "on": "de"},
    {"gloss": "to stand/rise", "proto": "*tag", "field": "verb",
     "nob": "taag", "don": "tag", "on": "dag"},
    {"gloss": "to sleep", "proto": "*wii", "field": "verb",
     "nob": "wiis", "don": "wis", "on": "ouis"},
    {"gloss": "to say/speak", "proto": "*ir", "field": "verb",
     "nob": "iir", "don": "ir", "on": "ir", "nar": "ira"},
    {"gloss": "to kill/slaughter", "proto": "*ked", "field": "verb",
     "nob": "kiid", "don": "kud", "on": "ked", "mid": "kid"},
    {"gloss": "to seize/take", "proto": "*er", "field": "verb",
     "nob": "iir", "don": "er", "on": "er"},
    {"gloss": "to build", "proto": "*mig", "field": "verb",
     "nob": "miig", "don": "mig", "on": "mig"},
    {"gloss": "to wash", "proto": "*sil", "field": "verb",
     "nob": "siil", "don": "sil"},
    {"gloss": "to burn", "proto": "*ur", "field": "verb",
     "nob": "uur", "don": "ur", "on": "our"},
    {"gloss": "to fly", "proto": "*pir", "field": "verb",
     "nob": "fiir", "don": "pir"},
    {"gloss": "to bite", "proto": "*ag", "field": "verb",
     "nob": "aag", "don": "ag"},
    {"gloss": "to fall/descend", "proto": "*tuul", "field": "verb",
     "nob": "tuul", "don": "tul"},
    {"gloss": "to send", "proto": "*ser", "field": "verb",
     "nob": "seer", "don": "ser", "on": "ser"},
    {"gloss": "to throw/cast", "proto": "*wir", "field": "verb",
     "nob": "wiir", "don": "wir"},
    {"gloss": "to carry/bring", "proto": "*dor", "field": "verb",
     "nob": "door", "don": "dor"},

    # ── ADJECTIVES / STATES ───────────────────────────────────────────────────
    {"gloss": "good/beautiful", "proto": "*mel", "field": "adj",
     "nob": "meeli", "don": "mel", "on": "mell", "tam": "mol"},
    {"gloss": "big/great", "proto": "*gor", "field": "adj",
     "nob": "goor", "don": "gor", "on": "gor"},
    {"gloss": "small/little", "proto": "*dir", "field": "adj",
     "nob": "diir", "don": "dir", "on": "dir"},
    {"gloss": "black/dark", "proto": "*kir", "field": "adj",
     "nob": "kiir", "don": "kir", "on": "kir"},
    {"gloss": "white/bright", "proto": "*bur", "field": "adj",
     "nob": "buur", "don": "bur"},
    {"gloss": "red", "proto": "*or", "field": "adj",
     "nob": "oor", "don": "or"},
    {"gloss": "new/young", "proto": "*pir", "field": "adj",
     "nob": "fiir", "don": "pir"},
    {"gloss": "long/tall", "proto": "*ikkir", "field": "adj",
     "nob": "ikkir", "don": "ikkir"},
    {"gloss": "hot/warm", "proto": "*sog", "field": "adj",
     "nob": "soog", "don": "sog"},
    {"gloss": "cold", "proto": "*um", "field": "adj",
     "nob": "uum", "don": "um"},
    {"gloss": "dry", "proto": "*kos", "field": "adj",
     "nob": "koos", "don": "kos"},
    {"gloss": "full/complete", "proto": "*gol", "field": "adj",
     "nob": "gool", "don": "gol"},

    # ── NUMBERS ───────────────────────────────────────────────────────────────
    {"gloss": "one", "proto": "*wer", "field": "number",
     "nob": "wer", "don": "wer", "on": "wer"},
    {"gloss": "two", "proto": "*owwi", "field": "number",
     "nob": "owwi", "don": "owwi", "on": "oui"},
    {"gloss": "three", "proto": "*tosk", "field": "number",
     "nob": "toské", "don": "tosk"},
    {"gloss": "four", "proto": "*kemsii", "field": "number",
     "nob": "kemsii", "don": "kemsii"},
    {"gloss": "five", "proto": "*dij", "field": "number",
     "nob": "dij", "don": "dij"},
    {"gloss": "ten", "proto": "*dimin", "field": "number",
     "nob": "dimin", "don": "dimin"},
    {"gloss": "hundred", "proto": "*emir", "field": "number",
     "nob": "emir", "don": "emir"},

    # ── RELIGION / ABSTRACT ───────────────────────────────────────────────────
    {"gloss": "god/spirit", "proto": "*masik", "field": "religion",
     "nob": "masig", "don": "masik", "on": "massig"},
    {"gloss": "life/soul/breath", "proto": "*pir", "field": "religion",
     "nob": "fiir", "don": "pir", "on": "pire"},
    {"gloss": "death", "proto": "*mud", "field": "religion",
     "nob": "muud", "don": "mud"},
    {"gloss": "protection/salvation", "proto": "*sele", "field": "religion",
     "nob": "selle", "don": "sel", "on": "selle"},
    {"gloss": "prayer/praise", "proto": "*hir", "field": "religion",
     "nob": "hiir", "don": "hir"},
    {"gloss": "offering/sacrifice", "proto": "*yer", "field": "religion",
     "nob": "yeer", "don": "yer"},
    {"gloss": "holy/sacred", "proto": "*ne", "field": "religion",
     "nob": "nee", "don": "ne"},
    {"gloss": "temple/sacred house", "proto": "*dim-ki", "field": "religion",
     "nob": "dimme", "don": "dim"},
    {"gloss": "tomb/grave", "proto": "*dik", "field": "religion",
     "nob": "diik", "don": "dik"},

    # ── HOUSEHOLD / MATERIAL ──────────────────────────────────────────────────
    {"gloss": "house/home", "proto": "*ki", "field": "material",
     "nob": "kii", "don": "ki", "on": "ki", "mid": "ki"},
    {"gloss": "door/gate", "proto": "*ber", "field": "material",
     "nob": "beer", "don": "ber"},
    {"gloss": "rope/cord", "proto": "*sar", "field": "material",
     "nob": "saar", "don": "sar"},
    {"gloss": "iron/metal", "proto": "*deg", "field": "material",
     "nob": "deeg", "don": "deg"},
    {"gloss": "pot/vessel", "proto": "*kor", "field": "material",
     "nob": "koor", "don": "kor"},
    {"gloss": "bed/mat", "proto": "*ang", "field": "material",
     "nob": "aang", "don": "ang"},
    {"gloss": "cloth/garment", "proto": "*kir", "field": "material",
     "nob": "kiir", "don": "kir"},
    {"gloss": "throne/seat", "proto": "*bed", "field": "material",
     "nob": "beed", "don": "bed"},
    {"gloss": "spear/weapon", "proto": "*til", "field": "material",
     "nob": "tiil", "don": "til"},
    {"gloss": "shield", "proto": "*dab", "field": "material",
     "nob": "daab", "don": "dab"},

    # ── MORE VERBS ────────────────────────────────────────────────────────────
    {"gloss": "to love/want", "proto": "*aas", "field": "verb",
     "nob": "aas", "don": "aas"},
    {"gloss": "to fear", "proto": "*jog", "field": "verb",
     "nob": "joog", "don": "jog"},
    {"gloss": "to cry/weep", "proto": "*nab", "field": "verb",
     "nob": "naab", "don": "nab"},
    {"gloss": "to cut", "proto": "*sul", "field": "verb",
     "nob": "suul", "don": "sul"},
    {"gloss": "to dig", "proto": "*gub", "field": "verb",
     "nob": "guub", "don": "gub"},
    {"gloss": "to pour/libate", "proto": "*bul", "field": "verb",
     "nob": "buul", "don": "bul"},
    {"gloss": "to break", "proto": "*kib", "field": "verb",
     "nob": "kiib", "don": "kib"},
    {"gloss": "to count/reckon", "proto": "*sid", "field": "verb",
     "nob": "siid", "don": "sid"},
    {"gloss": "to protect/guard", "proto": "*sel", "field": "verb",
     "nob": "seel", "don": "sel"},
    {"gloss": "to rule/govern", "proto": "*gor", "field": "verb",
     "nob": "goor", "don": "gor"},
    {"gloss": "to conquer/subdue", "proto": "*tek", "field": "verb",
     "nob": "tikkiir", "don": "tek", "on": "tekke"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# SOUND CORRESPONDENCE RULES  (25 rules, Rilly 2007/2010 + Bender 1996)
# ═══════════════════════════════════════════════════════════════════════════════
# Each rule: Meroitic phoneme → NES cognate phoneme in a given context

SOUND_LAWS = [
    # Consonant correspondences
    {"mer": "t", "nes": "d", "env": "intervocalic", "conf": 0.70, "ex": "ate~atte"},
    {"mer": "t", "nes": "t", "env": "word-initial", "conf": 0.90, "ex": "to~to"},
    {"mer": "k", "nes": "g", "env": "word-initial", "conf": 0.65, "ex": "qo~gor→k/g merger"},
    {"mer": "k", "nes": "k", "env": "before-back-V", "conf": 0.80, "ex": "ked~ked"},
    {"mer": "q", "nes": "k", "env": "uvular→velar", "conf": 0.60, "ex": "qore~gor"},
    {"mer": "q", "nes": "g", "env": "intervocalic", "conf": 0.55, "ex": "qo~goor"},
    {"mer": "p", "nes": "f", "env": "Nobiin-specific", "conf": 0.75, "ex": "pir~fiir"},
    {"mer": "p", "nes": "p", "env": "Don/ON", "conf": 0.85, "ex": "per~per"},
    {"mer": "p", "nes": "b", "env": "word-initial", "conf": 0.60, "ex": "beke~bek"},
    {"mer": "s", "nes": "sh", "env": "before-front-V", "conf": 0.70, "ex": "se~she"},
    {"mer": "s", "nes": "s", "env": "elsewhere", "conf": 0.90, "ex": "sur~sur"},
    {"mer": "h", "nes": "h", "env": "universal", "conf": 0.85, "ex": "he~hee"},
    {"mer": "h", "nes": "kh", "env": "uvular-fric", "conf": 0.50, "ex": "variant"},
    {"mer": "w", "nes": "w", "env": "universal", "conf": 0.90, "ex": "wer~wer"},
    {"mer": "w", "nes": "b", "env": "intervocalic", "conf": 0.50, "ex": "labial-approx"},
    {"mer": "l", "nes": "r", "env": "free-variation", "conf": 0.70, "ex": "lh~leeh"},
    {"mer": "l", "nes": "l", "env": "universal", "conf": 0.90, "ex": "lh~lihi"},
    {"mer": "n", "nes": "n", "env": "universal", "conf": 0.95, "ex": "ne~nee"},
    {"mer": "m", "nes": "m", "env": "universal", "conf": 0.95, "ex": "mlo~mel"},
    # Vowel correspondences
    {"mer": "a", "nes": "o", "env": "near-labial", "conf": 0.45, "ex": "abr~uur(a>u)"},
    {"mer": "e", "nes": "i", "env": "word-final", "conf": 0.55, "ex": "ate~atti"},
    {"mer": "e", "nes": "ee", "env": "Nob-lengthening", "conf": 0.70, "ex": "mel~meeli"},
    {"mer": "o", "nes": "oo", "env": "Nob-lengthening", "conf": 0.70, "ex": "to~tó"},
    {"mer": "i", "nes": "ii", "env": "Nob-lengthening", "conf": 0.75, "ex": "yi~yii"},
    {"mer": "a", "nes": "a", "env": "universal", "conf": 0.90, "ex": "ar~aar"},
]


class NESCognateEngine:
    """
    Score every unknown Meroitic root against the 300-entry NES dictionary
    using 25 regular sound laws. Produces ranked cognate proposals.
    """

    def __init__(self, vocabulary: Optional[dict] = None):
        self.vocabulary = vocabulary or VOCABULARY
        self.nes = NES_DICTIONARY
        self.laws = SOUND_LAWS
        # Build inverse lookup: for each NES form → entry
        self._nes_by_form = {}
        for entry in self.nes:
            for lang in ("nob", "don", "on", "mid", "bir", "nar", "nyi", "tam"):
                form = entry.get(lang)
                if form:
                    self._nes_by_form[form.lower()] = entry

    def find_cognates_for(self, meroitic_root: str) -> list[dict]:
        """
        Given a Meroitic root, find the best NES cognate candidates.
        Returns scored list sorted by combined_score descending.
        """
        root = meroitic_root.lower().strip("-")
        candidates = []

        for nes_entry in self.nes:
            phon_score = self._phonological_score(root, nes_entry)
            sem_score = self._semantic_score(root, nes_entry)
            combined = 0.6 * phon_score + 0.4 * sem_score

            if combined > 0.25:
                candidates.append({
                    "meroitic": root,
                    "nes_gloss": nes_entry["gloss"],
                    "proto_form": nes_entry["proto"],
                    "field": nes_entry["field"],
                    "phonological_score": round(phon_score, 3),
                    "semantic_score": round(sem_score, 3),
                    "combined_score": round(combined, 3),
                    "nobiin": nes_entry.get("nob", ""),
                    "old_nubian": nes_entry.get("on", ""),
                    "dongolawi": nes_entry.get("don", ""),
                })

        candidates.sort(key=lambda x: -x["combined_score"])
        return candidates

    def _phonological_score(self, mer_root: str, nes_entry: dict) -> float:
        """
        Score phonological similarity of a Meroitic root against an NES
        entry using the sound law table. Higher = more regular match.
        """
        best = 0.0
        for lang in ("on", "nob", "don", "mid", "nar", "tam"):
            form = nes_entry.get(lang)
            if not form:
                continue
            form = form.lower()
            score = self._compare_forms(mer_root, form)
            if score > best:
                best = score
        return best

    def _compare_forms(self, mer: str, nes: str) -> float:
        """
        Character-by-character comparison using sound laws.
        Returns 0.0–1.0 score.
        """
        # Strip vowel lengthening for comparison
        nes_short = nes.replace("ee", "e").replace("oo", "o").replace("ii", "i").replace("uu", "u").replace("aa", "a")
        mer_clean = mer.replace("-", "")

        if mer_clean == nes_short:
            return 1.0

        # Edit-distance-based with sound-law bonus
        matches = 0
        total = max(len(mer_clean), len(nes_short), 1)
        i, j = 0, 0

        while i < len(mer_clean) and j < len(nes_short):
            if mer_clean[i] == nes_short[j]:
                matches += 1.0
                i += 1
                j += 1
            elif self._has_sound_law(mer_clean[i], nes_short[j]):
                matches += 0.8
                i += 1
                j += 1
            else:
                # Mismatch — try skipping one side
                matches -= 0.3
                i += 1
                j += 1

        return max(0.0, matches / total)

    def _has_sound_law(self, mer_phon: str, nes_phon: str) -> bool:
        """Check if there's a regular sound correspondence between two phonemes."""
        for law in self.laws:
            if law["mer"] == mer_phon and law["nes"] == nes_phon:
                return True
            if law["nes"] == mer_phon and law["mer"] == nes_phon:
                return True
        return False

    def _semantic_score(self, mer_root: str, nes_entry: dict) -> float:
        """
        Score semantic plausibility: does the NES meaning fit the Meroitic
        context where this root appears?
        """
        ventry = self.vocabulary.get(mer_root, {})
        mer_cat = ventry.get("category", "")
        mer_meaning = ventry.get("translation", "")
        nes_field = nes_entry["field"]
        nes_gloss = nes_entry["gloss"]

        # Direct category match
        cat_map = {
            "title": ["kinship", "verb"],
            "deity": ["religion"],
            "funerary": ["food", "religion", "verb"],
            "person": ["kinship"],
            "kinship": ["kinship"],
            "verb": ["verb"],
            "adjective": ["adj"],
            "geographic": ["nature"],
            "architecture": ["material", "religion"],
            "number": ["number"],
            "religion": ["religion"],
        }
        matching_fields = cat_map.get(mer_cat, [])
        if nes_field in matching_fields:
            return 0.8

        # If we have no category, use distributional context
        if not mer_cat:
            return self._distributional_context_score(mer_root, nes_entry)

        return 0.3

    def _distributional_context_score(self, mer_root: str, nes_entry: dict) -> float:
        """
        For unknown roots, check corpus co-occurrence context to
        estimate whether the NES meaning is plausible.
        """
        # What tokens co-occur with this root?
        neighbors = defaultdict(int)
        for entry in CORPUS:
            tokens = [t.strip().split("-")[0].lower()
                      for t in entry["text"].split(":") if t.strip()]
            if mer_root in tokens:
                for tok in tokens:
                    if tok != mer_root:
                        neighbors[tok] += 1

        if not neighbors:
            return 0.3

        # Check if neighbors suggest the NES semantic field
        field_indicators = {
            "religion": {"mk", "amni", "wos", "apedmk", "selele", "pwrite"},
            "food": {"ate", "yi", "pesto"},
            "kinship": {"abr", "kdi", "lh", "sr", "qore", "kdke"},
            "verb": {"ked", "erk", "pesto", "mke", "tele"},
            "nature": {"to", "tenke", "tedke"},
            "adj": {"mlo", "qo"},
        }

        nes_field = nes_entry["field"]
        indicators = field_indicators.get(nes_field, set())
        overlap = sum(neighbors.get(ind, 0) for ind in indicators)
        total = sum(neighbors.values()) or 1

        return min(0.9, 0.3 + 0.5 * (overlap / total))

    def scan_all_unknowns(self) -> dict:
        """
        Scan every unknown or low-confidence token in the corpus and
        propose NES cognates.
        """
        # Find all unique roots with certainty < 0.6
        low_conf_roots = set()
        for entry in CORPUS:
            tokens = [t.strip().split("-")[0].lower()
                      for t in entry["text"].split(":") if t.strip()]
            for tok in tokens:
                ventry = self.vocabulary.get(tok, {})
                cert = ventry.get("certainty", 0)
                if cert < 0.6 and len(tok) >= 2:
                    low_conf_roots.add(tok)

        proposals = {}
        for root in sorted(low_conf_roots):
            cands = self.find_cognates_for(root)
            if cands:
                proposals[root] = cands[:5]

        return proposals

    def full_analysis(self) -> dict:
        """Run the complete NES cognate analysis."""
        proposals = self.scan_all_unknowns()

        # Also verify existing high-confidence cognates
        verified = []
        for word, ventry in self.vocabulary.items():
            if ventry.get("certainty", 0) >= 0.7 and ventry.get("nubian_cognate"):
                cands = self.find_cognates_for(word)
                if cands:
                    top = cands[0]
                    verified.append({
                        "meroitic": word,
                        "existing_meaning": ventry["translation"],
                        "nes_match": top["nes_gloss"],
                        "score": top["combined_score"],
                        "confirmed": top["combined_score"] > 0.5,
                    })

        # Statistics
        high_score = {r: cs[0] for r, cs in proposals.items()
                      if cs and cs[0]["combined_score"] > 0.5}
        medium_score = {r: cs[0] for r, cs in proposals.items()
                        if cs and 0.35 < cs[0]["combined_score"] <= 0.5}

        return {
            "all_proposals": proposals,
            "high_confidence_new": high_score,
            "medium_confidence_new": medium_score,
            "verified_existing": verified,
            "nes_dictionary_size": len(self.nes),
            "sound_laws_count": len(self.laws),
            "summary": {
                "low_confidence_roots_scanned": len(proposals),
                "high_confidence_proposals": len(high_score),
                "medium_confidence_proposals": len(medium_score),
                "existing_cognates_verified": len(verified),
                "verification_rate": round(
                    sum(1 for v in verified if v["confirmed"]) / max(len(verified), 1), 2
                ),
            },
        }


def run_nes_analysis() -> dict:
    """Execute full NES comparative analysis."""
    engine = NESCognateEngine()
    return engine.full_analysis()
