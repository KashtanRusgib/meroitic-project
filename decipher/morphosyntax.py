"""
Module 2: Advanced Morphological & Syntactic Modeling
=====================================================
Extends the grammar engine with:
  1. Verbal Chain Analyzer — isolates prefixes (e-), suffixes (-b, -ke, -s),
     compares royal military narratives with Napatan Egyptian parallels
  2. Suffixal Function Mapper — statistical analysis of morpheme cooccurrence
     and positional distribution to refine suffix meanings
  3. Clause-level parser for complex sentences beyond NP-AP pairs

References:
  - Hintze 1979 "Beiträge zur meroitischen Grammatik"
  - Hofmann 1981 "Material für eine meroitische Grammatik"
  - Rilly 2007, 2010
  - Rilly & de Voogt 2012: Ch. 3-4 on morphology
"""

from collections import defaultdict, Counter
from typing import Optional

from decipher import VOCABULARY, MORPHEMES, CORPUS


# ═══════════════════════════════════════════════════════════════════════════════
# Extended verbal morphology (Rilly 2007; Hintze 1979)
# ═══════════════════════════════════════════════════════════════════════════════

VERBAL_PREFIXES = {
    "e-": {
        "function": "1SG subject",
        "gloss": "1SG",
        "certainty": 0.80,
        "source": "Nastasen stele parallel (Griffith 1917:167)",
        "examples": ["e-ked (I slaughtered)", "e-tele (I went?)"],
        "notes": "Most securely identified verbal prefix. Attested in Side C of REM 1044.",
    },
    "t-": {
        "function": "2SG/3SG subject (tentative)",
        "gloss": "3SG",
        "certainty": 0.35,
        "source": "Hintze 1979; Rilly 2007",
        "examples": ["t-ked (he/she slaughtered?)", "t-mke (he/she built?)"],
        "notes": "Tentative. Pattern seen in some royal narratives.",
    },
    "p-": {
        "function": "causative / passive (tentative)",
        "gloss": "CAUS",
        "certainty": 0.40,
        "source": "Rilly 2007",
        "examples": ["p-esto (to cause to give → to offer)"],
        "notes": "May derive from pesto 'to give/offer'. Causative analysis "
                 "supported by parallel in Nubian languages (Rilly 2010:Ch.7).",
    },
    "m-": {
        "function": "nominalizer / agent noun",
        "gloss": "NMLZ",
        "certainty": 0.45,
        "source": "Hintze 1979",
        "examples": ["m-ke (builder?)", "m-de (tomb/death-place?)"],
        "notes": "Tentative. Agent noun formation: m- + verb root.",
    },
}

VERBAL_SUFFIXES = {
    "-b": {
        "function": "copula / existential",
        "gloss": "COP",
        "certainty": 0.65,
        "source": "Rilly 2007; Hofmann 1981",
        "paradigm": {"assertive": "-b", "optative": "-b-ke"},
        "examples": ["pesto-b (is given)", "pesto-b-ke (may it be given)"],
    },
    "-ke": {
        "function": "nominalization / subjunctive",
        "gloss": "NMLZ",
        "certainty": 0.60,
        "source": "Hintze 1979",
        "paradigm": {"nmlz": "-ke", "subjunctive": "-b-ke"},
        "examples": ["pesto-b-ke (giving / may it be given)"],
    },
    "-s": {
        "function": "perfect / completive aspect",
        "gloss": "PFV",
        "certainty": 0.40,
        "source": "Hintze 1979; Rilly 2007",
        "examples": ["ked-s (slaughtered, completed)"],
    },
    "-ye": {
        "function": "participial / relative",
        "gloss": "PTCP",
        "certainty": 0.45,
        "source": "Rilly 2007",
        "examples": ["qore-yi (one who rules / ruling)"],
    },
    "-lo": {
        "function": "terminal / emphatic",
        "gloss": "TERM",
        "certainty": 0.50,
        "source": "Hofmann 1981",
        "examples": ["mlo-lo (truly good)", "se-mlo-lw (?,good,TERM)"],
    },
    "-i": {
        "function": "vocative / addressee marker",
        "gloss": "VOC",
        "certainty": 0.75,
        "source": "Griffith 1911; many invocation formulas",
        "examples": ["apedmk-i (O Apedemak!)", "wos-i (O Isis!)"],
    },
}

NOMINAL_SUFFIXES = {
    "-l": {
        "function": "determinant (definite article)",
        "gloss": "DET",
        "certainty": 0.85,
        "source": "Rilly 2012",
        "notes": "'May be translated by either a definite or indefinite article "
                 "depending on context' (Rilly & de Voogt 2012).",
    },
    "-li": {
        "function": "determinant + plural",
        "gloss": "DET.PL",
        "certainty": 0.80,
        "source": "Rilly 2007",
        "examples": ["ate-li (the breads)", "mlo-li (the good ones)"],
    },
    "-se": {
        "function": "determinant (variant, before plural)",
        "gloss": "DET",
        "certainty": 0.70,
        "source": "Rilly 2007",
        "examples": ["abr-se-l (the men)", "kdi-se-l (the women)"],
    },
    "-o": {
        "function": "genitive / focus",
        "gloss": "GEN",
        "certainty": 0.75,
        "source": "Rilly 2007",
        "examples": ["qore-l-o (of the ruler)"],
    },
    "-te": {
        "function": "locative / ablative",
        "gloss": "LOC",
        "certainty": 0.80,
        "source": "Rilly 2007; many instances",
        "examples": ["amni-te (at Amun's temple)", "Mnpte (at Napata)"],
    },
    "-wi": {
        "function": "dative / benefactive",
        "gloss": "DAT",
        "certainty": 0.55,
        "source": "Hintze 1979",
        "examples": ["selele-wi (for protection)"],
    },
    "-ne": {
        "function": "instrumental / comitative",
        "gloss": "INST",
        "certainty": 0.40,
        "source": "Hofmann 1981",
        "examples": ["(uncertain)"],
    },
    "-k": {
        "function": "possessive / associative",
        "gloss": "POSS",
        "certainty": 0.50,
        "source": "Rilly 2007",
        "examples": ["mk-k (of the god)"],
    },
}


class VerbalChainAnalyzer:
    """
    Parse and analyze Meroitic verbal chains by isolating prefix + root + suffixes.

    A "verbal chain" is a sequence: [prefix]-ROOT-[suffix1]-[suffix2]...[suffix_n]

    The analyzer:
      1. Strips known prefixes from the left
      2. Identifies the verbal root from vocabulary
      3. Parses the suffix chain right-to-left
      4. Assigns grammatical features to the complete chain
    """

    def __init__(self):
        self.prefixes = VERBAL_PREFIXES
        self.v_suffixes = VERBAL_SUFFIXES
        self.n_suffixes = NOMINAL_SUFFIXES
        self.all_suffixes = {**self.v_suffixes, **self.n_suffixes}
        self.vocabulary = VOCABULARY
        self._verbal_roots = {
            w for w, v in VOCABULARY.items()
            if v.get("category", "") == "verb"
        }
        # Also include well-known verbs not in VOCABULARY under "verb" category
        self._verbal_roots.update({"ked", "erk", "tele", "pesto", "beke",
                                    "dme", "he", "mke", "tkke", "mde", "tke"})

    def parse_verbal_chain(self, token: str) -> dict:
        """
        Decompose a token into prefix + root + suffix chain.
        Returns structured analysis with glosses and confidence.
        """
        original = token
        remaining = token.lower().strip()
        result = {
            "original": original,
            "prefix": None,
            "root": None,
            "root_meaning": None,
            "suffixes": [],
            "gloss_chain": [],
            "is_verbal": False,
            "confidence": 0.0,
        }

        # Step 1: Strip prefix
        for pf, pf_data in sorted(self.prefixes.items(), key=lambda x: -len(x[0])):
            pf_bare = pf.rstrip("-")
            if remaining.startswith(pf_bare) and len(remaining) > len(pf_bare):
                result["prefix"] = {
                    "form": pf, "gloss": pf_data["gloss"],
                    "certainty": pf_data["certainty"],
                }
                result["gloss_chain"].append(pf_data["gloss"])
                remaining = remaining[len(pf_bare):]
                break

        # Step 2: Find verbal root (longest match)
        root_found = None
        for root in sorted(self._verbal_roots, key=len, reverse=True):
            if remaining.startswith(root):
                root_found = root
                break

        if root_found:
            result["root"] = root_found
            ventry = self.vocabulary.get(root_found, {})
            result["root_meaning"] = ventry.get("translation", root_found)
            result["is_verbal"] = True
            result["gloss_chain"].append(result["root_meaning"])
            remaining = remaining[len(root_found):]
        else:
            # Try to find any vocabulary root
            for word in sorted(self.vocabulary.keys(), key=len, reverse=True):
                if remaining.startswith(word) and len(word) >= 2:
                    result["root"] = word
                    result["root_meaning"] = self.vocabulary[word].get("translation", word)
                    result["gloss_chain"].append(result["root_meaning"])
                    remaining = remaining[len(word):]
                    break
            if not result["root"]:
                result["root"] = remaining
                result["root_meaning"] = f"[{remaining}]"
                result["gloss_chain"].append(f"[{remaining}]")
                remaining = ""

        # Step 3: Parse suffix chain (left-to-right, greedy longest match)
        iteration_limit = 10
        while remaining and iteration_limit > 0:
            iteration_limit -= 1
            matched = False
            for sf_key, sf_data in sorted(
                self.all_suffixes.items(), key=lambda x: -len(x[0])
            ):
                sf_bare = sf_key.lstrip("-")
                if remaining.startswith(sf_bare):
                    result["suffixes"].append({
                        "form": sf_key,
                        "gloss": sf_data["gloss"],
                        "certainty": sf_data["certainty"],
                    })
                    result["gloss_chain"].append(sf_data["gloss"])
                    remaining = remaining[len(sf_bare):]
                    matched = True
                    break
            if not matched:
                # Unrecognized suffix material
                result["suffixes"].append({
                    "form": f"-{remaining}",
                    "gloss": f"[{remaining}]",
                    "certainty": 0.1,
                })
                result["gloss_chain"].append(f"[{remaining}]")
                break

        # Step 4: Compute confidence
        parts = ([result["prefix"]] if result["prefix"] else []) + result["suffixes"]
        if parts:
            certs = [p.get("certainty", 0.1) for p in parts]
            root_cert = self.vocabulary.get(
                result["root"], {}
            ).get("certainty", 0.3)
            result["confidence"] = round(
                (root_cert + sum(certs)) / (1 + len(certs)), 3
            )
        else:
            result["confidence"] = self.vocabulary.get(
                result["root"], {}
            ).get("certainty", 0.2)

        return result

    def analyze_corpus_verbs(self, corpus: list[dict]) -> dict:
        """
        Scan the entire corpus for verbal chains and analyze their distribution.
        """
        all_chains = []
        prefix_dist = Counter()
        suffix_dist = Counter()
        root_dist = Counter()

        for entry in corpus:
            tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
            for token in tokens:
                chain = self.parse_verbal_chain(token)
                if chain["is_verbal"]:
                    all_chains.append(chain)
                    if chain["prefix"]:
                        prefix_dist[chain["prefix"]["form"]] += 1
                    root_dist[chain["root"]] += 1
                    for sf in chain["suffixes"]:
                        suffix_dist[sf["form"]] += 1

        return {
            "total_verbal_chains": len(all_chains),
            "prefix_distribution": dict(prefix_dist.most_common()),
            "suffix_distribution": dict(suffix_dist.most_common()),
            "root_distribution": dict(root_dist.most_common(20)),
            "sample_chains": [
                {
                    "original": c["original"],
                    "gloss": "-".join(c["gloss_chain"]),
                    "confidence": c["confidence"],
                }
                for c in sorted(all_chains, key=lambda x: -x["confidence"])[:15]
            ],
        }


class SuffixalMapper:
    """
    Statistical analysis of Meroitic suffix distribution to refine suffix functions.

    Examines:
      - What categories of root each suffix attaches to
      - Positional distribution (does suffix appear clause-finally? after names?)
      - Co-occurrence restrictions (which suffixes never combine?)
    """

    def __init__(self):
        self.vocabulary = VOCABULARY
        self.all_suffixes = {**NOMINAL_SUFFIXES, **VERBAL_SUFFIXES}

    def map_suffix_hosts(self, corpus: list[dict]) -> dict:
        """Determine which root categories each suffix prefers to attach to."""
        suffix_hosts = defaultdict(lambda: defaultdict(int))
        suffix_positions = defaultdict(lambda: defaultdict(int))

        for entry in corpus:
            tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
            for idx, token in enumerate(tokens):
                parts = token.split("-")
                if len(parts) < 2:
                    continue
                root = parts[0].lower()
                root_entry = self.vocabulary.get(root, {})
                root_cat = root_entry.get("category", "unknown")

                for suffix_part in parts[1:]:
                    sf_key = f"-{suffix_part.lower()}"
                    if sf_key in self.all_suffixes:
                        suffix_hosts[sf_key][root_cat] += 1
                        # Positional analysis
                        rel_pos = idx / len(tokens) if tokens else 0
                        if rel_pos < 0.25:
                            suffix_positions[sf_key]["initial_quarter"] += 1
                        elif rel_pos < 0.50:
                            suffix_positions[sf_key]["second_quarter"] += 1
                        elif rel_pos < 0.75:
                            suffix_positions[sf_key]["third_quarter"] += 1
                        else:
                            suffix_positions[sf_key]["final_quarter"] += 1

        results = {}
        for sf_key in self.all_suffixes:
            hosts = suffix_hosts.get(sf_key, {})
            positions = suffix_positions.get(sf_key, {})
            total = sum(hosts.values())
            results[sf_key] = {
                "total_occurrences": total,
                "host_categories": dict(hosts),
                "preferred_host": max(hosts, key=hosts.get) if hosts else None,
                "positional_distribution": dict(positions),
                "preferred_position": max(positions, key=positions.get) if positions else None,
                "known_function": self.all_suffixes[sf_key]["function"],
                "known_certainty": self.all_suffixes[sf_key]["certainty"],
            }

        return results

    def find_suffix_cooccurrences(self, corpus: list[dict]) -> dict:
        """Find which suffix combinations co-occur and which are mutually exclusive."""
        pair_counts = defaultdict(int)
        single_counts = defaultdict(int)

        for entry in corpus:
            tokens = [t.strip() for t in entry["text"].split(":") if t.strip()]
            for token in tokens:
                parts = token.split("-")
                if len(parts) < 2:
                    continue
                suffixes_in_token = []
                for part in parts[1:]:
                    sf_key = f"-{part.lower()}"
                    if sf_key in self.all_suffixes:
                        suffixes_in_token.append(sf_key)
                        single_counts[sf_key] += 1

                # Record pairs
                for i in range(len(suffixes_in_token)):
                    for j in range(i + 1, len(suffixes_in_token)):
                        pair = tuple(sorted([suffixes_in_token[i], suffixes_in_token[j]]))
                        pair_counts[pair] += 1

        # Compute association scores
        associations = []
        for pair, count in pair_counts.items():
            s1, s2 = pair
            expected = (single_counts[s1] * single_counts[s2]) / max(
                sum(single_counts.values()), 1
            )
            pmi = count / max(expected, 0.001)  # Simplified PMI
            associations.append({
                "suffix_pair": list(pair),
                "co_occurrence_count": count,
                "expected": round(expected, 2),
                "association_strength": round(pmi, 3),
                "type": "syntagmatic" if pmi > 1.5 else "weak" if pmi > 0.5 else "exclusive",
            })

        associations.sort(key=lambda x: -x["association_strength"])
        return {
            "suffix_pair_associations": associations,
            "single_suffix_counts": dict(single_counts),
        }


class ClauseParser:
    """
    Parse complex Meroitic sentences into clause-level constituents.

    Goes beyond simple NP-AP pairings to handle:
      - Coordinated clauses (narrative chains in royal stelae)
      - Relative clauses (participial -ye forms)
      - Subordinate clauses (locative -te, dative -wi frames)
    """

    def __init__(self):
        self.vocabulary = VOCABULARY
        self.verbal_analyzer = VerbalChainAnalyzer()

    def parse_inscription(self, text: str) -> dict:
        """Parse an inscription into clause-level structure."""
        tokens = [t.strip() for t in text.split(":") if t.strip()]

        # Classify each token
        classified = []
        for token in tokens:
            base = token.split("-")[0].lower()
            ventry = self.vocabulary.get(base, {})
            cat = ventry.get("category", "unknown")

            verbal = self.verbal_analyzer.parse_verbal_chain(token)

            classified.append({
                "form": token,
                "base": base,
                "category": cat,
                "is_verbal": verbal["is_verbal"],
                "verbal_parse": verbal if verbal["is_verbal"] else None,
                "has_locative": "-te" in token.lower(),
                "has_genitive": "-o" in token.lower() or "-l-o" in token.lower(),
                "has_dative": "-wi" in token.lower(),
                "has_det": "-l" in token.lower() and "-lo" not in token.lower(),
            })

        # Segment into clauses at clause boundaries
        clauses = self._segment_clauses(classified)

        return {
            "tokens": classified,
            "clauses": clauses,
            "clause_count": len(clauses),
        }

    def _segment_clauses(self, tokens: list[dict]) -> list[dict]:
        """
        Segment token sequence into clauses.
        Clause boundaries are identified at:
          - Verbal tokens (SOV: verb marks clause end)
          - Vocative/invocation markers (start new clause)
          - Major category shifts (title → offering = likely boundary)
        """
        clauses = []
        current_clause = {"tokens": [], "type": "unknown"}

        for i, tok in enumerate(tokens):
            current_clause["tokens"].append(tok)

            is_boundary = False
            # Verb marks clause end in SOV language
            if tok["is_verbal"] and i < len(tokens) - 1:
                next_tok = tokens[i + 1]
                if next_tok["category"] in ("deity_name", "title", "offering"):
                    is_boundary = True

            # Category: invocation starts new clause
            if (i > 0 and tok["category"] == "deity_name" and
                    tokens[i - 1].get("category") not in ("deity_name", "adjective")):
                # Split: previous tokens are one clause, this starts new one
                if len(current_clause["tokens"]) > 1:
                    prev_tokens = current_clause["tokens"][:-1]
                    clauses.append(self._classify_clause(prev_tokens))
                    current_clause = {"tokens": [tok], "type": "unknown"}
                    continue

            if is_boundary:
                clauses.append(self._classify_clause(current_clause["tokens"]))
                current_clause = {"tokens": [], "type": "unknown"}

        if current_clause["tokens"]:
            clauses.append(self._classify_clause(current_clause["tokens"]))

        return clauses

    def _classify_clause(self, tokens: list[dict]) -> dict:
        """Classify a clause by its type based on constituent categories."""
        cats = [t["category"] for t in tokens]
        has_verb = any(t["is_verbal"] for t in tokens)
        has_deity = any(c in ("deity_name",) for c in cats)
        has_offering = any(c in ("offering", "verb") for c in cats)
        has_name = any("name" in c.lower() for c in cats)
        has_locative = any(t["has_locative"] for t in tokens)

        if has_deity and not has_verb:
            clause_type = "invocation"
        elif has_offering and has_verb:
            clause_type = "offering_formula"
        elif has_verb and has_locative:
            clause_type = "locative_predication"
        elif has_verb:
            clause_type = "main_clause"
        elif has_name:
            clause_type = "nominal_predicate"
        else:
            clause_type = "fragment"

        return {
            "type": clause_type,
            "tokens": [t["form"] for t in tokens],
            "categories": cats,
            "has_verb": has_verb,
            "length": len(tokens),
        }


def run_morphosyntactic_analysis() -> dict:
    """Execute the full morphological and syntactic analysis."""
    vca = VerbalChainAnalyzer()
    sfm = SuffixalMapper()
    cp = ClauseParser()

    # 1. Verbal chain analysis across corpus
    verb_analysis = vca.analyze_corpus_verbs(CORPUS)

    # 2. Suffix distribution mapping
    suffix_map = sfm.map_suffix_hosts(CORPUS)
    suffix_cooccurrence = sfm.find_suffix_cooccurrences(CORPUS)

    # 3. Clause parsing (sample of 10 inscriptions for demonstration)
    clause_samples = []
    for entry in CORPUS[:10]:
        parsed = cp.parse_inscription(entry["text"])
        clause_samples.append({
            "id": entry.get("id", ""),
            "clauses": parsed["clauses"],
            "clause_count": parsed["clause_count"],
        })

    return {
        "verbal_chain_analysis": verb_analysis,
        "suffix_mapping": suffix_map,
        "suffix_cooccurrence": suffix_cooccurrence,
        "clause_parsing_samples": clause_samples,
        "summary": {
            "total_verbal_chains": verb_analysis["total_verbal_chains"],
            "unique_verb_roots": len(verb_analysis["root_distribution"]),
            "suffix_types_attested": sum(
                1 for v in suffix_map.values() if v["total_occurrences"] > 0
            ),
            "inscriptions_clause_parsed": len(clause_samples),
        },
    }
