"""
Meroitic Lexicon Reconstruction System
=========================================
Builds and refines a Meroitic lexicon through multiple methods:

  1. Direct attestation (words with known translations)
  2. Contextual inference (meaning from position/co-occurrence)
  3. Distributional semantics (words in similar contexts have similar meanings)
  4. Nubian cognate projection (meaning from comparative linguistics)
  5. Name analysis (theophoric names reveal deity/word structure)
  6. Formula decomposition (recurring formulas reveal word functions)
"""

from collections import defaultdict, Counter
import math
from typing import Optional


class LexiconBuilder:
    """Builds and continuously refines a Meroitic lexicon."""

    def __init__(self, vocabulary: dict, morphemes: dict, comparative_data: dict):
        self.vocabulary = dict(vocabulary)
        self.morphemes = dict(morphemes)
        self.comparative = comparative_data
        self.contextual_meanings: dict[str, list[dict]] = defaultdict(list)
        self.distributional_vectors: dict[str, Counter] = {}

    def build_full_lexicon(self, corpus: list[dict]) -> dict:
        """Run all lexicon construction methods and merge results."""
        # Step 1: Extract all unique words and morphemes from corpus
        all_tokens, all_morphemes = self._extract_corpus_forms(corpus)

        # Step 2: Build distributional vectors
        self._build_distributional_model(corpus)

        # Step 3: Contextual inference
        self._run_contextual_inference(corpus)

        # Step 4: Name analysis
        name_results = self._analyze_names(corpus)

        # Step 5: Formula decomposition
        formula_results = self._decompose_formulas(corpus)

        # Step 6: Cognate projection
        cognate_projections = self._project_from_cognates()

        # Step 7: Distributional similarity proposals
        dist_proposals = self._distributional_proposals()

        # Step 8: Merge everything into a unified lexicon
        lexicon = self._merge_lexicon(
            all_tokens, all_morphemes, name_results,
            formula_results, cognate_projections, dist_proposals
        )

        return lexicon

    def _extract_corpus_forms(self, corpus: list[dict]) -> tuple[Counter, Counter]:
        """Count all tokens and morphemes in the corpus."""
        token_counter = Counter()
        morph_counter = Counter()
        for insc in corpus:
            tokens = [t.strip() for t in insc["text"].split(":") if t.strip()]
            for tok in tokens:
                token_counter[tok] += 1
                for m in tok.split("-"):
                    if m:
                        morph_counter[m.lower()] += 1
        return token_counter, morph_counter

    def _build_distributional_model(self, corpus: list[dict], window: int = 3):
        """Build co-occurrence vectors for distributional semantics."""
        for insc in corpus:
            tokens = [t.strip().lower() for t in insc["text"].split(":") if t.strip()]
            for i, token in enumerate(tokens):
                if token not in self.distributional_vectors:
                    self.distributional_vectors[token] = Counter()
                for j in range(max(0, i - window), min(len(tokens), i + window + 1)):
                    if i != j:
                        self.distributional_vectors[token][tokens[j]] += 1

    def _run_contextual_inference(self, corpus: list[dict]):
        """Infer word meanings from positional and contextual patterns."""
        for insc in corpus:
            tokens = [t.strip() for t in insc["text"].split(":") if t.strip()]
            itype = insc.get("type", "")
            total = len(tokens)

            for i, tok in enumerate(tokens):
                base = tok.split("-")[0].lower()
                context = {
                    "inscription_type": itype,
                    "position": i,
                    "normalized_position": i / total if total else 0,
                    "left": tokens[i - 1] if i > 0 else None,
                    "right": tokens[i + 1] if i < total - 1 else None,
                    "is_first": i == 0,
                    "is_last": i == total - 1,
                }
                self.contextual_meanings[base].append(context)

    def _analyze_names(self, corpus: list[dict]) -> dict:
        """Analyze theophoric and other compound names to extract embedded vocabulary.

        Meroitic names often contain deity names and meaningful elements:
          - Amni-tenmomide → contains 'amni' (Amun)
          - Natakamani → contains deity element
          - Amanitore → 'amani' + 'tore'
        """
        name_components = defaultdict(list)
        all_names = set()

        for insc in corpus:
            tokens = [t.strip() for t in insc["text"].split(":") if t.strip()]
            for tok in tokens:
                parts = tok.split("-")
                base = parts[0]
                # Detect proper names (capitalized, not in vocab)
                if base and base[0].isupper() and base.lower() not in self.vocabulary:
                    all_names.add(base)

        # Try to decompose names into known elements
        known_elements = sorted(self.vocabulary.keys(), key=len, reverse=True)
        deity_elements = {k: v for k, v in self.vocabulary.items()
                         if v.get("category") in ("deity_name", "religion")}

        for name in all_names:
            name_lower = name.lower()
            found_elements = []
            remaining = name_lower

            for elem in known_elements:
                if elem in remaining and len(elem) >= 2:
                    found_elements.append({
                        "element": elem,
                        "meaning": self.vocabulary[elem].get("translation", ""),
                        "category": self.vocabulary[elem].get("category", ""),
                    })
                    remaining = remaining.replace(elem, "", 1)

            if found_elements:
                name_components[name] = {
                    "elements": found_elements,
                    "residue": remaining,
                    "is_theophoric": any(
                        e["category"] in ("deity_name", "religion")
                        for e in found_elements
                    ),
                }

        return name_components

    def _decompose_formulas(self, corpus: list[dict]) -> dict:
        """Identify and decompose recurring formulas.

        Recurring sequences reveal grammatical and semantic patterns.
        """
        # Extract token sequences by inscription type
        type_sequences: dict[str, list[list[str]]] = defaultdict(list)
        for insc in corpus:
            tokens = [t.strip() for t in insc["text"].split(":") if t.strip()]
            itype = insc.get("type", "unknown")
            type_sequences[itype].append(tokens)

        formulas = {}

        # Funerary formula analysis
        funerary_seqs = type_sequences.get("funerary", [])
        if funerary_seqs:
            # Find the common offering formula
            offering_patterns = []
            for seq in funerary_seqs:
                # Look for the ate...pesto pattern
                ate_pos = None
                pesto_pos = None
                for i, tok in enumerate(seq):
                    if tok.split("-")[0].lower() == "ate":
                        ate_pos = i
                    if tok.split("-")[0].lower() == "pesto":
                        pesto_pos = i
                if ate_pos is not None and pesto_pos is not None:
                    offering_patterns.append(seq[ate_pos:pesto_pos + 1])

            formulas["funerary_offering"] = {
                "description": "Standard funerary offering formula",
                "translation": "May bread and water be given",
                "structure": "ate-li : yi-s-li : pesto-b-ke",
                "decomposition": [
                    {"word": "ate-li", "gloss": "bread-PL", "meaning": "breads/food offerings"},
                    {"word": "yi-s-li", "gloss": "water-3SG-PL", "meaning": "water offerings (his/her)"},
                    {"word": "pesto-b-ke", "gloss": "give-3SG-NMLZ", "meaning": "may be given / the giving"},
                ],
                "occurrences": len(offering_patterns),
            }

        # Royal formula analysis
        royal_seqs = type_sequences.get("royal", [])
        if royal_seqs:
            formulas["royal_invocation"] = {
                "description": "Royal deity invocation formula",
                "translation": "[Deity], the god, King [Name], great and good",
                "structure": "amni : mk(-se) : qore-l(-o) : NAME : qo : mlo",
                "decomposition": [
                    {"word": "amni", "gloss": "Amun", "meaning": "Amun (deity)"},
                    {"word": "mk-se", "gloss": "god-VOC", "meaning": "O God!"},
                    {"word": "qore-l-o", "gloss": "ruler-PL-GEN", "meaning": "of the kingship"},
                    {"word": "qo : mlo", "gloss": "great : good", "meaning": "great and good"},
                ],
            }

            formulas["royal_domain"] = {
                "description": "Royal domain formula",
                "translation": "Protection of the western land and Akine territory",
                "structure": "tenke : to : (akine : to :) selele",
                "decomposition": [
                    {"word": "tenke", "gloss": "west", "meaning": "western"},
                    {"word": "to", "gloss": "land", "meaning": "land/territory"},
                    {"word": "akine", "gloss": "Akine", "meaning": "Lower Nubian province"},
                    {"word": "selele", "gloss": "protection", "meaning": "protection/sovereignty"},
                ],
            }

        return formulas

    def _project_from_cognates(self) -> dict:
        """Project meanings from Nubian cognates to unknown Meroitic words.

        Uses regular sound correspondences to propose new cognates.
        """
        projections = {}
        for meroitic, data in self.comparative.items():
            if meroitic not in self.vocabulary:
                # This is a comparative entry but not yet in our vocab
                projections[meroitic] = {
                    "proposed_meaning": data.get("meroitic_meaning", ""),
                    "source": "Nubian cognate projection",
                    "certainty": data.get("certainty", 0.3) * 0.8,
                }
        return projections

    def _distributional_proposals(self) -> list[dict]:
        """Propose meanings for unknown words based on distributional similarity
        to known words."""
        proposals = []
        known_words = {k: v for k, v in self.vocabulary.items() if v.get("certainty", 0) >= 0.60}

        for unknown, vector in self.distributional_vectors.items():
            # Skip if already known
            base = unknown.split("-")[0]
            if base in self.vocabulary:
                continue
            if not vector:
                continue

            # Find most similar known word
            best_sim = 0
            best_match = None
            for known in known_words:
                known_lower = known.lower()
                if known_lower in self.distributional_vectors:
                    sim = self._cosine_sim(vector, self.distributional_vectors[known_lower])
                    if sim > best_sim:
                        best_sim = sim
                        best_match = known

            if best_match and best_sim > 0.4:
                proposals.append({
                    "word": unknown,
                    "similar_to": best_match,
                    "similarity": best_sim,
                    "proposed_category": known_words[best_match].get("category", ""),
                    "notes": f"Distributionally similar to '{best_match}' ({known_words[best_match].get('translation', '')})",
                })

        return sorted(proposals, key=lambda x: -x["similarity"])

    def _cosine_sim(self, v1: Counter, v2: Counter) -> float:
        common = set(v1.keys()) & set(v2.keys())
        if not common:
            return 0.0
        dot = sum(v1[k] * v2[k] for k in common)
        n1 = math.sqrt(sum(val ** 2 for val in v1.values()))
        n2 = math.sqrt(sum(val ** 2 for val in v2.values()))
        if n1 == 0 or n2 == 0:
            return 0.0
        return dot / (n1 * n2)

    def _merge_lexicon(self, all_tokens, all_morphemes, name_results,
                       formula_results, cognate_projections, dist_proposals) -> dict:
        """Merge all sources into a unified lexicon."""
        lexicon = {}

        # Layer 1: Known vocabulary (highest priority)
        for word, entry in self.vocabulary.items():
            lexicon[word] = {
                "translation": entry.get("translation", ""),
                "category": entry.get("category", ""),
                "certainty": entry.get("certainty", 0.5),
                "source": "known_vocabulary",
                "attestations": entry.get("attestations", 0),
                "nubian_cognate": entry.get("nubian_cognate", ""),
            }

        # Layer 2: Known morphemes
        for morph, entry in self.morphemes.items():
            if morph not in lexicon:
                lexicon[morph] = {
                    "translation": entry.get("function", ""),
                    "category": entry.get("category", ""),
                    "certainty": entry.get("certainty", 0.5),
                    "source": "grammatical_morpheme",
                }

        # Layer 3: Cognate projections
        for word, proj in cognate_projections.items():
            if word not in lexicon:
                lexicon[word] = {
                    "translation": proj["proposed_meaning"],
                    "category": "projected",
                    "certainty": proj["certainty"],
                    "source": "nubian_cognate_projection",
                }

        # Layer 4: Distributional proposals
        for prop in dist_proposals[:30]:  # top 30
            word = prop["word"]
            if word not in lexicon:
                lexicon[word] = {
                    "translation": f"[similar to {prop['similar_to']}]",
                    "category": prop["proposed_category"],
                    "certainty": prop["similarity"] * 0.3,
                    "source": "distributional_inference",
                    "notes": prop["notes"],
                }

        # Add corpus frequency data
        for word in lexicon:
            clean = word.lstrip("-").rstrip("-").lower()
            lexicon[word]["corpus_frequency"] = all_morphemes.get(clean, 0)

        return lexicon
