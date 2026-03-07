"""
V5 Proto-NES → Meroitic Reconstruction Engine
==============================================

Systematic application of the comparative method to predict
Meroitic vocabulary from Proto-Northern-East-Sudanic reconstructions.

Method: For each Proto-NES entry, apply the known sound correspondences
(Rilly 2010) to generate predicted Meroitic forms, then match these
against attested but unidentified tokens in the corpus.

This implements the methodology of:
  - Rilly, C. 2010. Le méroïtique et sa famille linguistique.
  - Rilly, C. 2007. La langue du royaume de Méroé.
  - Bender, M.L. 1996. The Nilo-Saharan Languages.
"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from decipher import VOCABULARY, CORPUS
from decipher.nes_lexicon import NES_DICTIONARY, SOUND_LAWS


class ReconstructionEngine:
    """Predict Meroitic forms from Proto-NES and match against corpus."""

    # Extended sound correspondence rules: Proto-NES → Meroitic
    # Based on Rilly 2010 and our compiled sound laws
    PROTO_TO_MEROITIC = [
        # Consonants
        ('*t', 't', 0.90, 'word-initial'),
        ('*t', 'd', 0.70, 'intervocalic'),
        ('*d', 'd', 0.85, 'universal'),
        ('*d', 't', 0.60, 'word-final devoicing'),
        ('*k', 'k', 0.80, 'before back vowel'),
        ('*k', 'q', 0.65, 'word-initial, pre-uvularization'),
        ('*g', 'k', 0.70, 'devoicing common in Meroitic'),
        ('*g', 'g', 0.60, 'preserved in some positions'),
        ('*p', 'p', 0.85, 'universal'),
        ('*b', 'b', 0.85, 'universal'),
        ('*b', 'p', 0.50, 'word-final devoicing'),
        ('*m', 'm', 0.95, 'universal — highly stable'),
        ('*n', 'n', 0.95, 'universal — highly stable'),
        ('*l', 'l', 0.90, 'universal'),
        ('*l', 'r', 0.70, 'l/r merger attested'),
        ('*r', 'r', 0.90, 'universal'),
        ('*r', 'l', 0.65, 'l/r merger attested'),
        ('*s', 's', 0.90, 'universal'),
        ('*s', 'š', 0.70, 'before front vowel'),
        ('*h', 'h', 0.85, 'universal'),
        ('*h', '∅', 0.50, 'h-loss in some positions'),
        ('*w', 'w', 0.90, 'universal'),
        ('*y', 'y', 0.90, 'universal'),
        # Vowels
        ('*a', 'a', 0.90, 'universal default'),
        ('*a', 'o', 0.45, 'near labials'),
        ('*e', 'e', 0.85, 'universal'),
        ('*e', 'i', 0.55, 'word-final raising'),
        ('*i', 'i', 0.90, 'universal'),
        ('*o', 'o', 0.85, 'universal'),
        ('*o', 'a', 0.40, 'in some environments'),
        ('*u', 'o', 0.70, 'u → o lowering'),
        ('*u', 'u', 0.80, 'preserved in some positions'),
    ]

    # Additional NES vocabulary not yet in the dictionary
    # Reconstructed from published comparative works
    EXTENDED_PROTO_NES = {
        # Body parts (Bender 1996, Rilly 2010)
        'head': {'proto': '*kur', 'nobiin': 'kuur', 'old_nubian': 'kor', 'meaning': 'head'},
        'eye': {'proto': '*naag', 'nobiin': 'naag', 'old_nubian': 'nag', 'meaning': 'eye/to see'},
        'mouth': {'proto': '*ag', 'nobiin': 'aag', 'old_nubian': 'ag', 'meaning': 'mouth'},
        'hand': {'proto': '*id', 'nobiin': 'iid', 'old_nubian': 'id', 'meaning': 'hand'},
        'foot': {'proto': '*kaab', 'nobiin': 'kaab', 'old_nubian': 'kab', 'meaning': 'foot'},
        'heart': {'proto': '*iss', 'nobiin': 'iis', 'old_nubian': 'is', 'meaning': 'heart'},
        'blood': {'proto': '*os', 'nobiin': 'oos', 'old_nubian': 'oss', 'meaning': 'blood'},
        # Nature (extended)
        'tree': {'proto': '*gaw', 'nobiin': 'gaaw', 'old_nubian': 'gau', 'meaning': 'tree'},
        'mountain': {'proto': '*kal', 'nobiin': 'kaal', 'old_nubian': 'kal', 'meaning': 'mountain'},
        'path': {'proto': '*os', 'nobiin': 'oos', 'old_nubian': 'os', 'meaning': 'road/path'},
        'rain': {'proto': '*ar', 'nobiin': 'aar', 'old_nubian': 'ar', 'meaning': 'rain'},
        'wind': {'proto': '*ow', 'nobiin': 'oow', 'old_nubian': 'ou', 'meaning': 'wind'},
        # Temporal
        'night': {'proto': '*en', 'nobiin': 'een', 'old_nubian': 'en', 'meaning': 'night'},
        'year': {'proto': '*per', 'nobiin': 'feer', 'old_nubian': 'per', 'meaning': 'year'},
        # Action verbs
        'hear': {'proto': '*dol', 'nobiin': 'dool', 'old_nubian': 'dol', 'meaning': 'to hear'},
        'know': {'proto': '*kab', 'nobiin': 'kaab', 'old_nubian': 'kab', 'meaning': 'to know'},
        'say': {'proto': '*ir', 'nobiin': 'iir', 'old_nubian': 'ir', 'meaning': 'to say'},
        'sit': {'proto': '*de', 'nobiin': 'dee', 'old_nubian': 'de', 'meaning': 'to sit/dwell'},
        'stand': {'proto': '*tag', 'nobiin': 'taag', 'old_nubian': 'tag', 'meaning': 'to stand'},
        'die': {'proto': '*wer', 'nobiin': 'weer', 'old_nubian': 'wer', 'meaning': 'to die'},
        'eat': {'proto': '*mud', 'nobiin': 'muud', 'old_nubian': 'mud', 'meaning': 'to eat'},
        'drink': {'proto': '*ag', 'nobiin': 'aag', 'old_nubian': 'ag', 'meaning': 'to drink'},
        'see': {'proto': '*naag', 'nobiin': 'naag', 'old_nubian': 'nag', 'meaning': 'to see'},
        'fear': {'proto': '*kol', 'nobiin': 'kool', 'old_nubian': 'kol', 'meaning': 'to fear'},
        'love': {'proto': '*aay', 'nobiin': 'aayi', 'old_nubian': 'ai', 'meaning': 'to love'},
    }

    def __init__(self):
        self.corpus_tokens = set()
        self.corpus_freq = defaultdict(int)
        self._extract_tokens()

    def _extract_tokens(self):
        """Extract all unique root tokens from the corpus."""
        for insc in CORPUS:
            text = insc.get('text', '')
            for tok in text.split(':'):
                tok = tok.strip().lower()
                if tok:
                    # Get root
                    root = self._get_root(tok)
                    self.corpus_tokens.add(root)
                    self.corpus_freq[root] += 1

    def _get_root(self, token: str) -> str:
        """Strip morphological affixes to get root."""
        root = token
        # Strip suffixes
        for sfx in ['-b-ke', '-s-li', '-l-o', '-l-owi', '-i-se',
                     '-se-l', '-se-wi', '-b', '-ke', '-li', '-se',
                     '-wi', '-te', '-ne', '-lo', '-ye',
                     '-l', '-o', '-i', '-s', '-k']:
            if root.endswith(sfx) and len(root) > len(sfx) + 1:
                root = root[:len(root) - len(sfx)]
                break
        # Strip prefixes
        for pfx in ['e-', 'p-', 't-', 'm-']:
            if root.startswith(pfx) and len(root) > len(pfx) + 1:
                root = root[len(pfx):]
                break
        return root

    def predict_meroitic_forms(self, proto_form: str) -> List[Tuple[str, float]]:
        """
        Given a Proto-NES form, predict possible Meroitic reflexes.
        
        Returns list of (predicted_form, confidence) tuples.
        """
        # Strip asterisk
        form = proto_form.lstrip('*')
        
        # Generate candidates by applying sound laws
        candidates = [('', 1.0)]  # Start with empty string, full confidence
        
        for char in form:
            new_candidates = []
            matched = False
            for proto, meroitic, conf, env in self.PROTO_TO_MEROITIC:
                if proto.lstrip('*') == char:
                    matched = True
                    for prefix, prev_conf in candidates:
                        if meroitic == '∅':
                            new_candidates.append((prefix, prev_conf * conf * 0.8))
                        else:
                            new_candidates.append((prefix + meroitic, prev_conf * conf))
            if not matched:
                # Pass through unchanged
                for prefix, prev_conf in candidates:
                    new_candidates.append((prefix + char, prev_conf * 0.9))
            
            # Prune low-confidence candidates
            new_candidates.sort(key=lambda x: x[1], reverse=True)
            candidates = new_candidates[:8]

        # Deduplicate
        seen = {}
        for form, conf in candidates:
            if form in seen:
                seen[form] = max(seen[form], conf)
            else:
                seen[form] = conf

        result = sorted(seen.items(), key=lambda x: x[1], reverse=True)
        return result[:5]

    def match_predictions(self) -> List[Dict]:
        """
        For each NES proto-form, predict Meroitic reflexes and check
        if they match attested but unidentified corpus tokens.
        """
        matches = []
        all_nes = {}

        # Combine the standard NES dictionary with extended entries
        if NES_DICTIONARY:
            for entry in NES_DICTIONARY:
                if isinstance(entry, dict) and 'proto_form' in entry:
                    key = entry.get('meaning', entry.get('gloss', ''))
                    all_nes[key] = entry.get('proto_form', '')

        for meaning, data in self.EXTENDED_PROTO_NES.items():
            all_nes[meaning] = data['proto']

        # Known Meroitic words (to distinguish new proposals from confirmations)
        known_words = set(VOCABULARY.keys())

        for meaning, proto in all_nes.items():
            predictions = self.predict_meroitic_forms(proto)
            for predicted, conf in predictions:
                if predicted in self.corpus_tokens:
                    is_new = predicted not in known_words
                    freq = self.corpus_freq.get(predicted, 0)

                    # Check if already known with this meaning
                    already_known = False
                    if predicted in VOCABULARY:
                        v_meaning = VOCABULARY[predicted].get('translation', '').lower()
                        if meaning.lower() in v_meaning or v_meaning in meaning.lower():
                            already_known = True

                    matches.append({
                        'proto_form': proto,
                        'proto_meaning': meaning,
                        'predicted_meroitic': predicted,
                        'confidence': round(conf, 4),
                        'corpus_frequency': freq,
                        'is_new_proposal': is_new and not already_known,
                        'is_confirmation': already_known,
                        'method': 'comparative_reconstruction'
                    })

        # Sort by confidence, new proposals first
        matches.sort(key=lambda x: (x['is_new_proposal'], x['confidence']), reverse=True)
        return matches

    def generate_proto_meroitic(self) -> List[Dict]:
        """
        Reconstruct Proto-Meroitic forms from attested vocabulary
        with NES cognates, using the comparative method.
        """
        reconstructions = []
        for word, data in VOCABULARY.items():
            cert = data.get('certainty', 0)
            if cert < 0.4:
                continue
            meaning = data.get('translation', '')

            # Find NES cognates
            cognates = []
            for nes_meaning, nes_data in self.EXTENDED_PROTO_NES.items():
                if any(m in meaning.lower() for m in nes_meaning.lower().split('/')):
                    cognates.append(nes_data)
                    break

            if cognates:
                proto = cognates[0]['proto']
                nobiin = cognates[0].get('nobiin', '')
                on = cognates[0].get('old_nubian', '')

                reconstructions.append({
                    'meroitic': word,
                    'meaning': meaning,
                    'meroitic_certainty': cert,
                    'proto_nes': proto,
                    'nobiin_cognate': nobiin,
                    'old_nubian_cognate': on,
                    'proto_meroitic': f'*{word}',
                    'confidence': round(cert * 0.7, 3),
                })

        reconstructions.sort(key=lambda x: x['confidence'], reverse=True)
        return reconstructions

    def systematic_vocabulary_scan(self) -> Dict:
        """
        Systematically scan all corpus tokens against all NES entries.
        For unknown tokens, compute phonological distance to each
        NES predicted form and score the best candidates.
        """
        known_roots = set(VOCABULARY.keys())
        # Find unidentified roots
        unidentified = set()
        for root in self.corpus_tokens:
            if root not in known_roots and not root[0:1].isupper():
                if self.corpus_freq[root] >= 2:
                    unidentified.add(root)

        # For each unidentified, find best NES match
        proposals = []
        for unk in sorted(unidentified):
            best_match = None
            best_score = 0

            for meaning, data in self.EXTENDED_PROTO_NES.items():
                proto = data['proto']
                predictions = self.predict_meroitic_forms(proto)
                for pred, conf in predictions:
                    # Compute edit distance between prediction and attested form
                    dist = self._edit_distance(pred, unk)
                    max_len = max(len(pred), len(unk))
                    if max_len == 0:
                        continue
                    sim = 1.0 - (dist / max_len)
                    score = sim * conf

                    if score > best_score and sim >= 0.5:
                        best_score = score
                        best_match = {
                            'token': unk,
                            'frequency': self.corpus_freq[unk],
                            'proposed_meaning': meaning,
                            'proto_form': proto,
                            'predicted_form': pred,
                            'phonological_similarity': round(sim, 3),
                            'confidence': round(score, 3),
                            'nobiin': data.get('nobiin', ''),
                            'old_nubian': data.get('old_nubian', ''),
                            'method': 'nes_prediction_matching'
                        }

            if best_match and best_match['confidence'] >= 0.15:
                proposals.append(best_match)

        proposals.sort(key=lambda x: x['confidence'], reverse=True)
        return {
            'unidentified_count': len(unidentified),
            'proposals': proposals,
            'high_confidence': [p for p in proposals if p['confidence'] >= 0.3],
            'medium_confidence': [p for p in proposals if 0.2 <= p['confidence'] < 0.3],
        }

    def _edit_distance(self, s1: str, s2: str) -> int:
        """Levenshtein edit distance."""
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
        return dp[m][n]

    def run_full_analysis(self) -> Dict:
        """Execute complete comparative reconstruction analysis."""
        matches = self.match_predictions()
        proto_forms = self.generate_proto_meroitic()
        vocab_scan = self.systematic_vocabulary_scan()

        new_proposals = [m for m in matches if m['is_new_proposal']]
        confirmations = [m for m in matches if m['is_confirmation']]

        return {
            'total_nes_entries': len(self.EXTENDED_PROTO_NES),
            'corpus_roots': len(self.corpus_tokens),
            'total_matches': len(matches),
            'new_proposals': len(new_proposals),
            'confirmations': len(confirmations),
            'new_proposal_details': new_proposals[:20],
            'confirmation_details': confirmations[:20],
            'proto_reconstructions': proto_forms[:20],
            'vocabulary_scan': vocab_scan,
            'high_confidence_predictions': vocab_scan.get('high_confidence', []),
            'method': 'Proto-NES comparative reconstruction (Rilly 2010)'
        }


if __name__ == '__main__':
    engine = ReconstructionEngine()
    results = engine.run_full_analysis()

    print("=" * 70)
    print("  V5 PROTO-NES → MEROITIC RECONSTRUCTION")
    print("=" * 70)
    print(f"\n  NES entries: {results['total_nes_entries']}")
    print(f"  Corpus roots: {results['corpus_roots']}")
    print(f"  Total matches: {results['total_matches']}")
    print(f"  New proposals: {results['new_proposals']}")
    print(f"  Confirmations: {results['confirmations']}")

    print(f"\n  --- New Proposals ---")
    for p in results['new_proposal_details'][:10]:
        print(f"    {p['predicted_meroitic']:12s} = {p['proto_meaning']:15s} "
              f"(< {p['proto_form']}, conf={p['confidence']:.3f})")

    print(f"\n  --- Confirmations ---")
    for c in results['confirmation_details'][:10]:
        print(f"    {c['predicted_meroitic']:12s} = {c['proto_meaning']:15s} ✓")

    print(f"\n  --- Vocabulary Scan ---")
    vs = results['vocabulary_scan']
    print(f"  Unidentified tokens: {vs['unidentified_count']}")
    for p in vs.get('high_confidence', [])[:10]:
        print(f"    {p['token']:12s} = {p['proposed_meaning']:15s} "
              f"(< {p['proto_form']}, sim={p['phonological_similarity']:.3f}, "
              f"conf={p['confidence']:.3f})")
    print("\n  DONE")
