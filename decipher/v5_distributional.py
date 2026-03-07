"""
V5 Distributional Semantics Engine for Meroitic
================================================

Applies the distributional hypothesis: words occurring in similar
contexts have similar meanings. Builds co-occurrence matrices from
the full corpus, computes PMI and cosine similarity, and infers
meanings for unknown tokens by semantic transfer from known neighbors.

Methodology follows Schütze (1998) and Turney & Pantel (2010),
adapted for small-corpus ancient languages per Luo et al. (2015).
"""

import math
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Set

from decipher import VOCABULARY, CORPUS, MORPHEMES


class DistributionalEngine:
    """Full distributional analysis of the Meroitic corpus."""

    def __init__(self, corpus: list = None, vocabulary: dict = None):
        self.corpus = corpus or CORPUS
        self.vocab = vocabulary or VOCABULARY
        self.morphemes = MORPHEMES

        # Extracted data
        self.token_sequences: List[List[str]] = []
        self.token_freq: Counter = Counter()
        self.cooccurrence: Dict[str, Counter] = defaultdict(Counter)
        self.pmi_cache: Dict[Tuple[str, str], float] = {}
        self.roots: Dict[str, str] = {}  # token -> root
        self.semantic_vectors: Dict[str, Dict[str, float]] = {}

        self._extract_corpus()
        self._build_cooccurrence(window=3)
        self._compute_all_pmi()
        self._build_semantic_vectors()

    def _strip_morphology(self, token: str) -> str:
        """Strip known suffixes/prefixes to get root form."""
        root = token.lower()
        # Strip known prefixes
        for prefix in ['p-', 't-', 'm-', 'e-']:
            if root.startswith(prefix) and len(root) > len(prefix) + 1:
                root = root[len(prefix):]
                break
        # Strip known suffixes (longest first)
        suffix_list = sorted(self.morphemes.keys(), key=len, reverse=True)
        for suffix in suffix_list:
            clean = suffix.lstrip('-')
            if root.endswith(clean) and len(root) > len(clean) + 1:
                root = root[:-len(clean)]
                break
        return root

    def _extract_corpus(self):
        """Extract token sequences from all inscriptions."""
        for insc in self.corpus:
            text = insc.get('text', '')
            tokens = [t.strip() for t in text.split(':') if t.strip()]
            roots = []
            for t in tokens:
                root = self._strip_morphology(t)
                self.roots[t] = root
                roots.append(root)
                self.token_freq[root] += 1
            self.token_sequences.append(roots)

    def _build_cooccurrence(self, window: int = 3):
        """Build symmetric co-occurrence matrix with given window size."""
        for seq in self.token_sequences:
            for i, w1 in enumerate(seq):
                for j in range(max(0, i - window), min(len(seq), i + window + 1)):
                    if i != j:
                        w2 = seq[j]
                        self.cooccurrence[w1][w2] += 1

    def _compute_all_pmi(self):
        """Compute PMI for all co-occurring pairs."""
        total = sum(self.token_freq.values())
        for w1, neighbors in self.cooccurrence.items():
            for w2, count in neighbors.items():
                if count < 2:
                    continue
                p_w1 = self.token_freq[w1] / total
                p_w2 = self.token_freq[w2] / total
                # Estimate joint probability from co-occurrence
                pair_total = sum(sum(c.values()) for c in self.cooccurrence.values()) / 2
                p_joint = count / pair_total if pair_total > 0 else 0
                if p_joint > 0 and p_w1 > 0 and p_w2 > 0:
                    pmi = math.log2(p_joint / (p_w1 * p_w2))
                    # Use PPMI (positive PMI)
                    self.pmi_cache[(w1, w2)] = max(0, pmi)

    def _build_semantic_vectors(self):
        """Build PPMI-weighted semantic vectors for each token."""
        # Context dimensions = all tokens with freq >= 2
        dimensions = {t for t, c in self.token_freq.items() if c >= 2}
        for token in self.token_freq:
            vec = {}
            for dim in dimensions:
                key = (token, dim)
                if key in self.pmi_cache:
                    vec[dim] = self.pmi_cache[key]
            if vec:
                self.semantic_vectors[token] = vec

    def cosine_similarity(self, w1: str, w2: str) -> float:
        """Compute cosine similarity between two token vectors."""
        v1 = self.semantic_vectors.get(w1, {})
        v2 = self.semantic_vectors.get(w2, {})
        if not v1 or not v2:
            return 0.0
        shared = set(v1.keys()) & set(v2.keys())
        if not shared:
            return 0.0
        dot = sum(v1[k] * v2[k] for k in shared)
        mag1 = math.sqrt(sum(x * x for x in v1.values()))
        mag2 = math.sqrt(sum(x * x for x in v2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    def most_similar(self, token: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Find the most distributionally similar tokens."""
        root = self._strip_morphology(token)
        sims = []
        for other in self.semantic_vectors:
            if other == root:
                continue
            sim = self.cosine_similarity(root, other)
            if sim > 0:
                sims.append((other, sim))
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:top_n]

    def get_known_tokens(self) -> Set[str]:
        """Return tokens with established meanings (certainty >= 0.5)."""
        known = set()
        for word, data in self.vocab.items():
            cert = data.get('certainty', 0)
            if cert >= 0.5:
                known.add(word.lower())
        return known

    def get_unknown_tokens(self) -> Set[str]:
        """Return tokens in corpus that lack confident meanings."""
        known = self.get_known_tokens()
        # Also exclude proper names
        royal_names = set()
        for insc in self.corpus:
            for t in insc.get('text', '').split(':'):
                t = t.strip()
                if t and t[0].isupper():
                    royal_names.add(t.lower())
                    royal_names.add(self._strip_morphology(t))

        unknown = set()
        for root, freq in self.token_freq.items():
            if freq >= 2 and root not in known and root not in royal_names:
                # Check if it's a morphological variant of a known word
                is_variant = False
                for k in known:
                    if root.startswith(k) or k.startswith(root):
                        is_variant = True
                        break
                if not is_variant:
                    unknown.add(root)
        return unknown

    def infer_meanings(self) -> List[Dict]:
        """
        Infer meanings for unknown tokens via distributional transfer.
        
        For each unknown token, find its known nearest neighbors,
        then propose meaning based on the semantic field of neighbors.
        """
        known = self.get_known_tokens()
        unknown = self.get_unknown_tokens()
        proposals = []

        for unk in sorted(unknown):
            neighbors = self.most_similar(unk, top_n=8)
            known_neighbors = [(w, s) for w, s in neighbors if w in known]
            if not known_neighbors:
                continue

            # Determine semantic field from neighbors
            neighbor_meanings = []
            for w, sim in known_neighbors:
                if w in self.vocab:
                    meaning = self.vocab[w].get('translation', '')
                    category = self.vocab[w].get('category', '')
                    neighbor_meanings.append({
                        'word': w,
                        'meaning': meaning,
                        'category': category,
                        'similarity': round(sim, 3)
                    })

            if neighbor_meanings:
                # Identify dominant semantic field
                categories = Counter(n['category'] for n in neighbor_meanings)
                dominant_field = categories.most_common(1)[0][0] if categories else 'unknown'

                # Best similarity score
                best_sim = neighbor_meanings[0]['similarity']
                confidence = min(0.55, best_sim * 0.6)  # Conservative

                proposals.append({
                    'token': unk,
                    'frequency': self.token_freq[unk],
                    'proposed_field': dominant_field,
                    'confidence': round(confidence, 3),
                    'evidence': neighbor_meanings[:5],
                    'method': 'distributional_transfer',
                    'note': f"Distributes like {neighbor_meanings[0]['word']} "
                            f"({neighbor_meanings[0]['meaning']}); "
                            f"cosine={best_sim:.3f}"
                })

        proposals.sort(key=lambda x: x['confidence'], reverse=True)
        return proposals

    def semantic_field_clusters(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        Cluster all tokens into semantic fields using distributional evidence.
        
        Returns clusters keyed by field name with member tokens and scores.
        """
        # Seed clusters from known vocabulary
        field_seeds = defaultdict(list)
        for word, data in self.vocab.items():
            cat = data.get('category', 'unknown')
            cert = data.get('certainty', 0)
            if cert >= 0.5:
                root = word.lower()
                if root in self.semantic_vectors:
                    field_seeds[cat].append(root)

        clusters = {}
        for field, seeds in field_seeds.items():
            members = set(seeds)
            scored_members = [(s, 1.0) for s in seeds]

            # Find tokens distributionally similar to seed members
            for token in self.token_freq:
                if token in members:
                    continue
                avg_sim = 0
                count = 0
                for seed in seeds:
                    sim = self.cosine_similarity(token, seed)
                    if sim > 0:
                        avg_sim += sim
                        count += 1
                if count > 0:
                    avg_sim /= count
                    if avg_sim > 0.15:
                        scored_members.append((token, round(avg_sim, 3)))

            scored_members.sort(key=lambda x: x[1], reverse=True)
            clusters[field] = scored_members

        return clusters

    def collocations(self, min_pmi: float = 1.0) -> List[Dict]:
        """Extract statistically significant collocations."""
        results = []
        seen = set()
        for (w1, w2), pmi in sorted(self.pmi_cache.items(), key=lambda x: x[1], reverse=True):
            if pmi < min_pmi:
                break
            pair = tuple(sorted([w1, w2]))
            if pair in seen:
                continue
            seen.add(pair)
            results.append({
                'word1': w1,
                'word2': w2,
                'pmi': round(pmi, 3),
                'cooccurrence': self.cooccurrence[w1][w2],
                'freq1': self.token_freq[w1],
                'freq2': self.token_freq[w2]
            })
        return results[:50]

    def positional_analysis(self) -> Dict[str, Dict]:
        """
        Analyze typical positions of tokens within inscriptions.
        
        Position awareness helps distinguish sentence-initial elements
        (deities, invocations) from sentence-final (verbs, offerings).
        This is critical for an SOV language.
        """
        positions = defaultdict(list)
        for seq in self.token_sequences:
            n = len(seq)
            if n == 0:
                continue
            for i, token in enumerate(seq):
                rel_pos = i / max(n - 1, 1)  # 0.0 = start, 1.0 = end
                positions[token].append(rel_pos)

        analysis = {}
        for token, pos_list in positions.items():
            if len(pos_list) < 2:
                continue
            mean_pos = sum(pos_list) / len(pos_list)
            variance = sum((p - mean_pos) ** 2 for p in pos_list) / len(pos_list)
            analysis[token] = {
                'mean_position': round(mean_pos, 3),
                'variance': round(variance, 4),
                'occurrences': len(pos_list),
                'position_class': (
                    'initial' if mean_pos < 0.25 else
                    'medial' if mean_pos < 0.75 else
                    'final'
                )
            }
        return analysis

    def run_full_analysis(self) -> Dict:
        """Execute complete distributional analysis."""
        proposals = self.infer_meanings()
        clusters = self.semantic_field_clusters()
        collocs = self.collocations()
        positions = self.positional_analysis()

        return {
            'vocabulary_size': len(self.token_freq),
            'corpus_tokens': sum(self.token_freq.values()),
            'unique_roots': len(self.token_freq),
            'known_tokens': len(self.get_known_tokens()),
            'unknown_tokens': len(self.get_unknown_tokens()),
            'meaning_proposals': proposals,
            'proposal_count': len(proposals),
            'semantic_clusters': {k: len(v) for k, v in clusters.items()},
            'collocations': collocs,
            'positional_classes': {
                'initial': sum(1 for v in positions.values() if v['position_class'] == 'initial'),
                'medial': sum(1 for v in positions.values() if v['position_class'] == 'medial'),
                'final': sum(1 for v in positions.values() if v['position_class'] == 'final'),
            },
            'top_collocations': collocs[:10],
            'clusters_detail': {k: v[:10] for k, v in clusters.items()},
        }


if __name__ == '__main__':
    engine = DistributionalEngine()
    results = engine.run_full_analysis()

    print("=" * 70)
    print("  V5 DISTRIBUTIONAL SEMANTICS ANALYSIS")
    print("=" * 70)
    print(f"\n  Corpus: {results['corpus_tokens']} tokens, "
          f"{results['unique_roots']} unique roots")
    print(f"  Known: {results['known_tokens']} | "
          f"Unknown: {results['unknown_tokens']}")

    print(f"\n  Meaning proposals generated: {results['proposal_count']}")
    for p in results['meaning_proposals'][:10]:
        print(f"    {p['token']:20s}  field={p['proposed_field']:15s}  "
              f"conf={p['confidence']:.3f}  "
              f"({p['note'][:60]})")

    print(f"\n  Semantic clusters: {len(results['semantic_clusters'])}")
    for field, count in sorted(results['semantic_clusters'].items()):
        print(f"    {field:20s}: {count} members")

    print(f"\n  Top collocations (PMI):")
    for c in results['top_collocations'][:10]:
        print(f"    {c['word1']:12s} + {c['word2']:12s}  "
              f"PMI={c['pmi']:.2f}  co={c['cooccurrence']}")

    print(f"\n  Positional classes: {results['positional_classes']}")
    print("\n  DONE")
