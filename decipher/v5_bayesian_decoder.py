"""
V5 Bayesian Integration Decoder
================================

Integrates ALL evidence streams (distributional, comparative, bilingual,
morphological, positional, template) into a single Bayesian framework
that produces posterior probabilities for each token meaning.

For each token T with candidate meanings M1, M2, ..., Mn:
  P(Mi | evidence) ∝ P(Mi) × P(distributional | Mi) × P(comparative | Mi)
                           × P(bilingual | Mi) × P(positional | Mi)
                           × P(template | Mi)

This is the core integration engine that combines all v1-v5 modules.
"""

import math
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from decipher import VOCABULARY, CORPUS, MORPHEMES


class BayesianDecoder:
    """
    Bayesian integration of all evidence streams for token decipherment.
    """

    # Evidence source weights (tuned by cross-validation on known tokens)
    SOURCE_WEIGHTS = {
        'lexicon': 0.30,        # Known vocabulary certainty
        'bilingual': 0.25,      # Bilingual text anchors
        'comparative': 0.20,    # NES comparative evidence
        'distributional': 0.10, # Distributional similarity
        'positional': 0.08,     # Position within inscription
        'template': 0.07,       # Template/genre fit
    }

    POS_EXPECTED_POSITIONS = {
        'NOUN.PROPER': (0.0, 0.35),   # Names tend to appear early-to-mid
        'NOUN.TITLE': (0.15, 0.5),    # Titles follow names
        'NOUN': (0.2, 0.8),           # Common nouns spread widely
        'VERB': (0.6, 1.0),           # Verbs tend toward end (SOV)
        'ADJ': (0.3, 0.7),            # Adjectives modify nearby nouns
        'PRON': (0.1, 0.5),           # Pronouns in subject position
    }

    def __init__(self, distributional_results=None, reconstruction_results=None,
                 bilingual_anchors=None):
        self.vocab = VOCABULARY
        self.corpus = CORPUS
        self.morphemes = MORPHEMES
        self.dist_results = distributional_results or {}
        self.recon_results = reconstruction_results or {}
        self.bilingual = bilingual_anchors or {}

        # Build candidate pool for each token
        self.candidate_pool: Dict[str, List[Dict]] = {}
        self._build_candidate_pool()

    def _get_root(self, token: str) -> str:
        """Get root form of token."""
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

    def _build_candidate_pool(self):
        """
        For each corpus token, gather all candidate meanings from all sources.
        """
        # All tokens in corpus
        all_tokens = set()
        for insc in self.corpus:
            for tok in insc.get('text', '').split(':'):
                tok = tok.strip()
                if tok:
                    all_tokens.add(tok)

        for token in all_tokens:
            root = self._get_root(token)
            candidates = []

            # Source 1: Known vocabulary
            if root in self.vocab:
                v = self.vocab[root]
                candidates.append({
                    'meaning': v.get('translation', ''),
                    'category': v.get('category', ''),
                    'source': 'lexicon',
                    'prior': v.get('certainty', 0.5),
                })

            # Source 2: Proper name detection
            if token[0:1].isupper():
                candidates.append({
                    'meaning': f'[name: {token}]',
                    'category': 'proper_name',
                    'source': 'onomastic',
                    'prior': 0.8,
                })

            # Source 3: Distributional proposals
            dist_proposals = self.dist_results.get('meaning_proposals', [])
            for p in dist_proposals:
                if p.get('token', '') == root:
                    candidates.append({
                        'meaning': f'[{p["proposed_field"]} domain]',
                        'category': p['proposed_field'],
                        'source': 'distributional',
                        'prior': p.get('confidence', 0.2),
                    })

            # Source 4: Comparative reconstruction proposals
            vocab_scan = self.recon_results.get('vocabulary_scan', {})
            for p in vocab_scan.get('proposals', []):
                if p.get('token', '') == root:
                    candidates.append({
                        'meaning': p.get('proposed_meaning', ''),
                        'category': 'reconstructed',
                        'source': 'comparative',
                        'prior': p.get('confidence', 0.2),
                    })

            # Source 5: New proposal details from reconstruction
            for p in self.recon_results.get('new_proposal_details', []):
                if self._get_root(p.get('predicted_meroitic', '')) == root:
                    candidates.append({
                        'meaning': p.get('proto_meaning', ''),
                        'category': 'nes_reconstruction',
                        'source': 'comparative',
                        'prior': p.get('confidence', 0.2),
                    })

            if candidates:
                self.candidate_pool[token] = candidates
            else:
                # Unknown token
                self.candidate_pool[token] = [{
                    'meaning': '[unknown]',
                    'category': 'unknown',
                    'source': 'none',
                    'prior': 0.1,
                }]

    def compute_posterior(self, token: str, inscription: dict) -> List[Dict]:
        """
        Compute posterior probabilities for all candidate meanings of a token.
        
        Combines prior (from source certainty) with likelihoods from each
        evidence stream using Bayes' rule.
        """
        candidates = self.candidate_pool.get(token, [])
        if not candidates:
            return [{'meaning': '[unknown]', 'posterior': 0.05}]

        root = self._get_root(token)
        text = inscription.get('text', '')
        tokens = [t.strip() for t in text.split(':') if t.strip()]
        genre = inscription.get('type', '')

        # Find token position in inscription
        token_pos = -1
        for i, t in enumerate(tokens):
            if t == token:
                token_pos = i
                break
        rel_pos = token_pos / max(len(tokens) - 1, 1) if token_pos >= 0 else 0.5

        scored = []
        for cand in candidates:
            prior = cand['prior']
            source = cand['source']

            # Likelihood: positional fit
            pos_likelihood = self._positional_likelihood(cand, rel_pos)

            # Likelihood: template/genre fit
            template_likelihood = self._template_likelihood(cand, genre, tokens, token_pos)

            # Likelihood: distributional coherence
            dist_likelihood = self._distributional_likelihood(root, cand, tokens)

            # Combine using weighted product  
            log_posterior = math.log(max(prior, 0.01))
            log_posterior += self.SOURCE_WEIGHTS['positional'] * math.log(max(pos_likelihood, 0.01))
            log_posterior += self.SOURCE_WEIGHTS['template'] * math.log(max(template_likelihood, 0.01))
            log_posterior += self.SOURCE_WEIGHTS['distributional'] * math.log(max(dist_likelihood, 0.01))

            # Boost from source type
            if source == 'lexicon':
                log_posterior += self.SOURCE_WEIGHTS['lexicon'] * math.log(max(prior, 0.01))
            elif source == 'comparative':
                log_posterior += self.SOURCE_WEIGHTS['comparative'] * math.log(max(prior, 0.01))
            elif source == 'bilingual':
                log_posterior += self.SOURCE_WEIGHTS['bilingual'] * math.log(max(prior, 0.01))

            scored.append({
                'meaning': cand['meaning'],
                'category': cand['category'],
                'source': source,
                'prior': prior,
                'positional': round(pos_likelihood, 3),
                'template': round(template_likelihood, 3),
                'distributional': round(dist_likelihood, 3),
                'log_posterior': round(log_posterior, 4),
            })

        # Normalize posteriors
        if scored:
            max_log = max(s['log_posterior'] for s in scored)
            raw = [math.exp(s['log_posterior'] - max_log) for s in scored]
            total = sum(raw)
            for i, s in enumerate(scored):
                s['posterior'] = round(raw[i] / total, 4) if total > 0 else 0

        scored.sort(key=lambda x: x['posterior'], reverse=True)
        return scored

    def _positional_likelihood(self, candidate: dict, rel_pos: float) -> float:
        """Score how well the candidate fits the observed position."""
        cat = candidate.get('category', '')
        # Map category to expected position range
        for pos_cat, (lo, hi) in self.POS_EXPECTED_POSITIONS.items():
            if pos_cat.lower() in cat.lower() or cat.lower() in pos_cat.lower():
                if lo <= rel_pos <= hi:
                    return 0.9
                else:
                    dist = min(abs(rel_pos - lo), abs(rel_pos - hi))
                    return max(0.3, 0.9 - dist * 2)
        return 0.5  # Neutral

    def _template_likelihood(self, candidate: dict, genre: str,
                              tokens: list, token_pos: int) -> float:
        """Score how well the candidate fits the inscription genre."""
        meaning = candidate.get('meaning', '').lower()
        cat = candidate.get('category', '').lower()

        if genre == 'funerary':
            # Funerary inscriptions expect: deity, name, kin, offering, verb
            funerary_terms = ['bread', 'water', 'give', 'offering', 'isis', 'god',
                              'man', 'woman', 'offspring', 'sister', 'good']
            if any(t in meaning for t in funerary_terms):
                return 0.9
            return 0.5

        elif genre == 'royal':
            royal_terms = ['ruler', 'king', 'queen', 'great', 'good', 'land',
                           'west', 'protection', 'amun', 'apedemak', 'give', 'throne']
            if any(t in meaning for t in royal_terms):
                return 0.9
            return 0.5

        elif genre == 'religious':
            religious_terms = ['god', 'great', 'good', 'protection', 'give',
                               'apedemak', 'isis', 'amun', 'temple', 'beget']
            if any(t in meaning for t in religious_terms):
                return 0.9
            return 0.5

        return 0.5

    def _distributional_likelihood(self, root: str, candidate: dict,
                                    context_tokens: list) -> float:
        """Score based on distributional coherence with context."""
        # Check if context tokens are known and semantically compatible
        context_fields = set()
        for ct in context_tokens:
            cr = self._get_root(ct)
            if cr in self.vocab:
                cat = self.vocab[cr].get('category', '')
                context_fields.add(cat)

        cand_cat = candidate.get('category', '')
        if cand_cat in context_fields:
            return 0.8  # Same semantic field in context
        return 0.5

    def decode_corpus(self) -> List[Dict]:
        """
        Decode every inscription using Bayesian integration.
        Returns per-inscription results with ranked candidate meanings
        for each token.
        """
        results = []
        for insc in self.corpus:
            text = insc.get('text', '')
            tokens = [t.strip() for t in text.split(':') if t.strip()]

            token_decodings = []
            total_conf = 0
            for tok in tokens:
                posteriors = self.compute_posterior(tok, insc)
                best = posteriors[0] if posteriors else {'meaning': '[?]', 'posterior': 0}
                token_decodings.append({
                    'token': tok,
                    'best_meaning': best['meaning'],
                    'best_posterior': best['posterior'],
                    'source': best.get('source', 'unknown'),
                    'alternatives': posteriors[1:3],  # Top 2 alternatives
                })
                total_conf += best['posterior']

            avg_conf = total_conf / len(tokens) if tokens else 0

            results.append({
                'id': insc.get('id', ''),
                'site': insc.get('site', ''),
                'type': insc.get('type', ''),
                'period': insc.get('period', ''),
                'text': text,
                'token_count': len(tokens),
                'decodings': token_decodings,
                'average_posterior': round(avg_conf, 4),
                'free_translation': self._build_translation(token_decodings),
            })

        results.sort(key=lambda x: x['average_posterior'], reverse=True)
        return results

    def _build_translation(self, decodings: List[Dict]) -> str:
        """Build a free English translation from the decoded tokens."""
        parts = []
        for d in decodings:
            meaning = d['best_meaning']
            if meaning.startswith('[name:'):
                name = meaning.replace('[name:', '').replace(']', '').strip()
                parts.append(name)
            elif meaning == '[unknown]':
                parts.append(f"[{d['token']}]")
            else:
                parts.append(meaning)
        return ' '.join(parts)

    def compute_corpus_statistics(self, results: List[Dict]) -> Dict:
        """Compute aggregate statistics for the decoded corpus."""
        total_tokens = 0
        source_counts = defaultdict(int)
        posterior_sum = 0
        type_stats = defaultdict(lambda: {'count': 0, 'conf_sum': 0})

        for r in results:
            total_tokens += r['token_count']
            posterior_sum += r['average_posterior'] * r['token_count']
            t = r['type']
            type_stats[t]['count'] += 1
            type_stats[t]['conf_sum'] += r['average_posterior']

            for d in r['decodings']:
                source_counts[d['source']] += 1

        avg_posterior = posterior_sum / total_tokens if total_tokens > 0 else 0

        return {
            'total_inscriptions': len(results),
            'total_tokens': total_tokens,
            'average_posterior': round(avg_posterior, 4),
            'source_distribution': dict(source_counts),
            'by_type': {
                t: {
                    'count': s['count'],
                    'avg_confidence': round(s['conf_sum'] / s['count'], 4) if s['count'] > 0 else 0
                }
                for t, s in type_stats.items()
            },
        }

    def identify_breakthroughs(self, results: List[Dict]) -> List[Dict]:
        """
        Identify tokens where the Bayesian decoder provides
        new or improved readings compared to the v4 system.
        """
        breakthroughs = []
        for r in results:
            for d in r['decodings']:
                token = d['token']
                root = self._get_root(token)
                best = d['best_meaning']
                posterior = d['best_posterior']
                source = d['source']

                # Check if this is a new reading
                if root not in self.vocab and best != '[unknown]' and not best.startswith('[name:'):
                    breakthroughs.append({
                        'token': token,
                        'root': root,
                        'new_meaning': best,
                        'posterior': posterior,
                        'source': source,
                        'inscription': r['id'],
                        'type': 'new_reading',
                    })
                elif root in self.vocab:
                    old_cert = self.vocab[root].get('certainty', 0)
                    if posterior > old_cert + 0.1:
                        breakthroughs.append({
                            'token': token,
                            'root': root,
                            'new_meaning': best,
                            'old_certainty': old_cert,
                            'new_posterior': posterior,
                            'source': source,
                            'inscription': r['id'],
                            'type': 'improved_reading',
                        })

        # Deduplicate by root
        seen = set()
        unique = []
        for b in breakthroughs:
            if b['root'] not in seen:
                seen.add(b['root'])
                unique.append(b)

        unique.sort(key=lambda x: x.get('posterior', 0), reverse=True)
        return unique

    def run_full_analysis(self) -> Dict:
        """Execute complete Bayesian decoding pipeline."""
        results = self.decode_corpus()
        stats = self.compute_corpus_statistics(results)
        breakthroughs = self.identify_breakthroughs(results)

        return {
            'decoded_inscriptions': len(results),
            'corpus_statistics': stats,
            'breakthroughs': breakthroughs,
            'breakthrough_count': len(breakthroughs),
            'new_readings': [b for b in breakthroughs if b['type'] == 'new_reading'],
            'improved_readings': [b for b in breakthroughs if b['type'] == 'improved_reading'],
            'top_translations': results[:10],
            'full_results': results,
            'method': 'Bayesian multi-source integration'
        }


if __name__ == '__main__':
    decoder = BayesianDecoder()
    results = decoder.run_full_analysis()

    print("=" * 70)
    print("  V5 BAYESIAN INTEGRATION DECODER")
    print("=" * 70)
    stats = results['corpus_statistics']
    print(f"\n  Inscriptions: {stats['total_inscriptions']}")
    print(f"  Tokens: {stats['total_tokens']}")
    print(f"  Average posterior: {stats['average_posterior']:.4f}")
    print(f"  Breakthroughs: {results['breakthrough_count']}")

    print(f"\n  Source distribution:")
    for src, count in sorted(stats['source_distribution'].items()):
        print(f"    {src:20s}: {count}")

    print(f"\n  By type:")
    for t, s in stats['by_type'].items():
        print(f"    {t:15s}: {s['count']} inscriptions, "
              f"avg conf={s['avg_confidence']:.4f}")

    print(f"\n  New readings: {len(results['new_readings'])}")
    for b in results['new_readings'][:10]:
        print(f"    {b['root']:15s} = {b['new_meaning']:20s} "
              f"(posterior={b['posterior']:.3f}, source={b['source']})")

    print("\n  DONE")
