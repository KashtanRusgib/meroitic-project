"""
V5 New Readings Proposal Module
=================================

Compiles, deduplicates, and ranks ALL new vocabulary proposals from the
v5 analysis pipeline. Produces a scholarly-quality apparatus with:
  - Evidence chains for each proposal
  - Cross-method validation scores
  - Confidence tiers (ESTABLISHED / PROPOSED / SPECULATIVE / UNKNOWN)
  - Full attestation data
"""

from collections import defaultdict
from typing import Dict, List, Optional

from decipher import VOCABULARY, CORPUS, MORPHEMES


# Confidence tiers
TIER_ESTABLISHED = 'ESTABLISHED'    # ≥ 0.70  multiple independent sources
TIER_PROPOSED    = 'PROPOSED'       # 0.45-0.69  at least 2 sources
TIER_SPECULATIVE = 'SPECULATIVE'    # 0.20-0.44  single source
TIER_UNKNOWN     = 'UNKNOWN'        # < 0.20  no viable candidates


class NewReadingsCompiler:
    """
    Gathers proposals from distributional, comparative, and Bayesian
    modules and produces a unified ranked vocabulary list.
    """

    def __init__(self, distributional_results=None, reconstruction_results=None,
                 bayesian_results=None):
        self.vocab = VOCABULARY
        self.corpus = CORPUS
        self.dist = distributional_results or {}
        self.recon = reconstruction_results or {}
        self.bayes = bayesian_results or {}

        self.proposals: Dict[str, Dict] = {}
        self.attestations: Dict[str, List[str]] = defaultdict(list)

    def _build_attestation_index(self):
        """Map each token root to the inscriptions it appears in."""
        for insc in self.corpus:
            insc_id = insc.get('id', '')
            for tok in insc.get('text', '').split(':'):
                tok = tok.strip()
                if tok:
                    root = self._get_root(tok)
                    self.attestations[root].append(insc_id)

    def _get_root(self, token: str) -> str:
        root = token.lower()
        for sfx in ['-b-ke', '-s-li', '-l-o', '-l-owi', '-i-se',
                     '-se-l', '-se-wi', '-b', '-ke', '-li', '-se',
                     '-wi', '-te', '-ne', '-lo', '-ye',
                     '-l', '-o', '-i', '-s', '-k']:
            if root.endswith(sfx) and len(root) > len(sfx) + 1:
                root = root[:len(root) - len(sfx)]
                break
        for pfx in ['e-', 'p-', 't-', 'm-']:
            if root.startswith(pfx) and len(root) > len(pfx) + 1:
                root = root[len(pfx):]
                break
        return root

    def gather_proposals(self):
        """
        Gather proposals from all three v5 engines and merge into
        a unified proposals dictionary keyed by root form.
        """
        self._build_attestation_index()

        # 1. From distributional analysis
        dist_proposals = self.dist.get('meaning_proposals', [])
        for p in dist_proposals:
            root = p.get('token', '')
            if root and root not in self.vocab:
                if root not in self.proposals:
                    self.proposals[root] = {
                        'root': root,
                        'meanings': [],
                        'sources': set(),
                        'attestation_count': len(self.attestations.get(root, [])),
                    }
                self.proposals[root]['meanings'].append({
                    'meaning': f"[{p.get('proposed_field', 'unknown')} domain]",
                    'confidence': p.get('confidence', 0.1),
                    'source': 'distributional',
                    'evidence': f"Distributional similarity to {p.get('similar_to', 'known tokens')} "
                                f"in semantic field {p.get('proposed_field', 'unknown')}",
                })
                self.proposals[root]['sources'].add('distributional')

        # 2. From comparative reconstruction
        recon_proposals = self.recon.get('vocabulary_scan', {}).get('proposals', [])
        for p in recon_proposals:
            root = p.get('token', '')
            if root and root not in self.vocab:
                if root not in self.proposals:
                    self.proposals[root] = {
                        'root': root,
                        'meanings': [],
                        'sources': set(),
                        'attestation_count': len(self.attestations.get(root, [])),
                    }
                self.proposals[root]['meanings'].append({
                    'meaning': p.get('proposed_meaning', ''),
                    'confidence': p.get('confidence', 0.1),
                    'source': 'comparative',
                    'evidence': f"NES cognate: Proto-NES *{p.get('proto_form', '?')} "
                                f"via {p.get('sound_law', 'regular correspondence')}",
                })
                self.proposals[root]['sources'].add('comparative')

        # Also from reconstruction new_proposal_details
        for p in self.recon.get('new_proposal_details', []):
            predicted = p.get('predicted_meroitic', '')
            root = self._get_root(predicted) if predicted else ''
            if root and root not in self.vocab:
                if root not in self.proposals:
                    self.proposals[root] = {
                        'root': root,
                        'meanings': [],
                        'sources': set(),
                        'attestation_count': len(self.attestations.get(root, [])),
                    }
                self.proposals[root]['meanings'].append({
                    'meaning': p.get('proto_meaning', ''),
                    'confidence': p.get('confidence', 0.1),
                    'source': 'comparative',
                    'evidence': f"Predicted from Proto-NES *{p.get('proto_form', '?')} "
                                f"matched to {p.get('attested_token', '?')}",
                })
                self.proposals[root]['sources'].add('comparative')

        # 3. From Bayesian decoder breakthroughs
        new_readings = self.bayes.get('new_readings', [])
        for b in new_readings:
            root = b.get('root', '')
            if root and root not in self.vocab:
                if root not in self.proposals:
                    self.proposals[root] = {
                        'root': root,
                        'meanings': [],
                        'sources': set(),
                        'attestation_count': len(self.attestations.get(root, [])),
                    }
                self.proposals[root]['meanings'].append({
                    'meaning': b.get('new_meaning', ''),
                    'confidence': b.get('posterior', 0.1),
                    'source': 'bayesian',
                    'evidence': f"Bayesian posterior from {b.get('source', 'unknown')} evidence "
                                f"in inscription {b.get('inscription', '?')}",
                })
                self.proposals[root]['sources'].add('bayesian')

    def rank_proposals(self) -> List[Dict]:
        """
        Rank all proposals by combined confidence, number of sources,
        and attestation frequency.
        """
        ranked = []
        for root, data in self.proposals.items():
            # Combine confidence from multiple meanings (take best, boost by count)
            if not data['meanings']:
                continue

            best_conf = max(m['confidence'] for m in data['meanings'])
            source_count = len(data['sources'])
            attest_count = data['attestation_count']

            # Cross-method bonus: multiple independent sources increase confidence
            cross_bonus = min(0.15, (source_count - 1) * 0.08)
            # Attestation bonus: more occurrences = more reliable
            attest_bonus = min(0.10, attest_count * 0.02)

            combined = min(0.95, best_conf + cross_bonus + attest_bonus)

            # Determine tier
            if combined >= 0.70 and source_count >= 2:
                tier = TIER_ESTABLISHED
            elif combined >= 0.45 and source_count >= 2:
                tier = TIER_PROPOSED
            elif combined >= 0.20:
                tier = TIER_SPECULATIVE
            else:
                tier = TIER_UNKNOWN

            # Best meaning is the one with highest confidence
            best_meaning = max(data['meanings'], key=lambda m: m['confidence'])

            ranked.append({
                'root': root,
                'best_meaning': best_meaning['meaning'],
                'combined_confidence': round(combined, 4),
                'tier': tier,
                'source_count': source_count,
                'attestation_count': attest_count,
                'sources': sorted(data['sources']),
                'evidence_chain': [
                    {'meaning': m['meaning'],
                     'confidence': m['confidence'],
                     'source': m['source'],
                     'evidence': m['evidence']}
                    for m in sorted(data['meanings'],
                                    key=lambda m: m['confidence'], reverse=True)
                ],
            })

        ranked.sort(key=lambda x: x['combined_confidence'], reverse=True)
        return ranked

    def build_enhanced_lexicon(self, ranked: List[Dict]) -> Dict:
        """
        Build an enhanced lexicon that merges established vocabulary
        with new proposals.
        """
        enhanced = {}

        # Start with established vocabulary
        for root, v in self.vocab.items():
            enhanced[root] = {
                'translation': v.get('translation', ''),
                'certainty': v.get('certainty', 0),
                'category': v.get('category', ''),
                'tier': TIER_ESTABLISHED if v.get('certainty', 0) >= 0.7 else TIER_PROPOSED,
                'source': 'established_lexicon',
            }

        # Add new proposals
        for p in ranked:
            root = p['root']
            if root not in enhanced and p['tier'] in (TIER_ESTABLISHED, TIER_PROPOSED, TIER_SPECULATIVE):
                enhanced[root] = {
                    'translation': p['best_meaning'],
                    'certainty': p['combined_confidence'],
                    'category': 'v5_proposal',
                    'tier': p['tier'],
                    'source': ', '.join(p['sources']),
                }

        return enhanced

    def compute_statistics(self, ranked: List[Dict], enhanced: Dict) -> Dict:
        """Compute summary statistics for the new readings."""
        tier_counts = defaultdict(int)
        for p in ranked:
            tier_counts[p['tier']] += 1

        established_count = sum(1 for v in self.vocab.values()
                                if v.get('certainty', 0) >= 0.7)
        proposed_count = sum(1 for v in self.vocab.values()
                             if 0.3 <= v.get('certainty', 0) < 0.7)

        return {
            'established_vocabulary': len(self.vocab),
            'established_high_confidence': established_count,
            'established_partial': proposed_count,
            'new_proposals_total': len(ranked),
            'new_by_tier': dict(tier_counts),
            'enhanced_lexicon_size': len(enhanced),
            'vocabulary_increase': len(enhanced) - len(self.vocab),
            'corpus_coverage': self._compute_coverage(enhanced),
        }

    def _compute_coverage(self, lexicon: Dict) -> float:
        """Compute what fraction of corpus tokens are covered by the lexicon."""
        total = 0
        covered = 0
        for insc in self.corpus:
            for tok in insc.get('text', '').split(':'):
                tok = tok.strip()
                if not tok:
                    continue
                total += 1
                root = self._get_root(tok)
                if root in lexicon or tok[0:1].isupper():
                    covered += 1
        return round(covered / total, 4) if total > 0 else 0

    def run_full_analysis(self) -> Dict:
        """Execute the complete new readings pipeline."""
        self.gather_proposals()
        ranked = self.rank_proposals()
        enhanced = self.build_enhanced_lexicon(ranked)
        stats = self.compute_statistics(ranked, enhanced)

        return {
            'proposals': ranked,
            'proposal_count': len(ranked),
            'enhanced_lexicon': enhanced,
            'enhanced_lexicon_size': len(enhanced),
            'statistics': stats,
            'top_proposals': ranked[:15],
        }


if __name__ == '__main__':
    compiler = NewReadingsCompiler()
    results = compiler.run_full_analysis()

    print("=" * 70)
    print("  V5 NEW READINGS COMPILER")
    print("=" * 70)
    stats = results['statistics']
    print(f"\n  Established vocabulary: {stats['established_vocabulary']}")
    print(f"  New proposals: {stats['new_proposals_total']}")
    print(f"  Enhanced lexicon: {stats['enhanced_lexicon_size']}")
    print(f"  Vocabulary increase: +{stats['vocabulary_increase']}")
    print(f"  Corpus coverage: {stats['corpus_coverage']:.1%}")

    print(f"\n  New proposals by tier:")
    for tier, count in sorted(stats.get('new_by_tier', {}).items()):
        print(f"    {tier:15s}: {count}")

    if results['top_proposals']:
        print(f"\n  Top proposals:")
        for p in results['top_proposals'][:10]:
            print(f"    {p['root']:15s} = {p['best_meaning']:20s} "
                  f"[{p['tier']}] conf={p['combined_confidence']:.3f} "
                  f"sources={','.join(p['sources'])}")

    print("\n  DONE")
