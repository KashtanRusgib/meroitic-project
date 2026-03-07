"""
Morpheme Pattern Analyzer for Meroitic Script
================================================
Identifies recurring word patterns and morpheme boundaries in Meroitic
transliterations using frequency analysis, n-gram extraction, and
affix detection based on known grammatical morphemes.
"""

import re
from collections import Counter, defaultdict
from typing import Optional


def tokenize_inscription(text: str) -> list[str]:
    """Split a Meroitic transliteration into tokens.

    Meroitic cursive uses ':' as a word separator.
    Hyphens connect morphemes within a word.
    """
    tokens = [t.strip() for t in text.split(":") if t.strip()]
    return tokens


def split_morphemes(token: str) -> list[str]:
    """Split a token into morphemes at hyphen boundaries."""
    return [m for m in token.split("-") if m]


def extract_all_tokens(inscriptions: list[dict]) -> list[str]:
    """Extract all tokens from a list of inscriptions."""
    tokens = []
    for insc in inscriptions:
        tokens.extend(tokenize_inscription(insc["text"]))
    return tokens


def word_frequency(inscriptions: list[dict]) -> Counter:
    """Count whole-token (word) frequencies across all inscriptions."""
    return Counter(extract_all_tokens(inscriptions))


def morpheme_frequency(inscriptions: list[dict]) -> Counter:
    """Count individual morpheme frequencies across all inscriptions."""
    counter: Counter = Counter()
    for token in extract_all_tokens(inscriptions):
        counter.update(split_morphemes(token))
    return counter


def ngram_frequency(inscriptions: list[dict], n: int = 2) -> Counter:
    """Compute n-gram (token-level) frequencies across inscriptions."""
    counter: Counter = Counter()
    for insc in inscriptions:
        tokens = tokenize_inscription(insc["text"])
        for i in range(len(tokens) - n + 1):
            gram = tuple(tokens[i : i + n])
            counter[gram] += 1
    return counter


def detect_affixes(inscriptions: list[dict], known_morphemes: Optional[dict] = None) -> dict:
    """Detect prefixes and suffixes from token structure.

    Returns a dict with 'prefixes' and 'suffixes', each mapping the
    affix string to its frequency and known function (if available).
    """
    from .data import KNOWN_MORPHEMES
    if known_morphemes is None:
        known_morphemes = KNOWN_MORPHEMES

    prefix_counter: Counter = Counter()
    suffix_counter: Counter = Counter()

    for token in extract_all_tokens(inscriptions):
        parts = split_morphemes(token)
        if len(parts) >= 2:
            # Last part is likely a suffix
            for part in parts[1:]:
                suffix_counter[part] += 1
            # First part could be a prefix if it's short (1-2 chars)
            if len(parts[0]) <= 2:
                prefix_counter[parts[0]] += 1

    def annotate(counter, affix_type):
        results = {}
        for affix, count in counter.most_common():
            key = f"{affix}-" if affix_type == "prefix" else f"-{affix}"
            info = {"count": count, "function": "unknown"}
            if key in known_morphemes:
                info["function"] = known_morphemes[key]["function"]
            results[key] = info
        return results

    return {
        "prefixes": annotate(prefix_counter, "prefix"),
        "suffixes": annotate(suffix_counter, "suffix"),
    }


def find_word_patterns(inscriptions: list[dict]) -> dict:
    """Identify recurring structural patterns in tokens.

    Groups tokens by their morpheme-structure template
    (e.g., 'ROOT-SUFFIX-SUFFIX') and reports frequency.
    """
    pattern_groups: dict[str, list[str]] = defaultdict(list)
    for token in extract_all_tokens(inscriptions):
        parts = split_morphemes(token)
        template = "-".join(
            "ROOT" if i == 0 else f"M{i}" for i in range(len(parts))
        )
        pattern_groups[template].append(token)

    return {
        template: {
            "count": len(tokens),
            "examples": list(set(tokens))[:10],
        }
        for template, tokens in sorted(
            pattern_groups.items(), key=lambda x: -len(x[1])
        )
    }


def detect_morpheme_boundaries(inscriptions: list[dict], known_vocab: Optional[dict] = None) -> list[dict]:
    """Attempt automatic morpheme boundary detection.

    Uses known vocabulary roots to split tokens further.
    Returns a list of segmentation proposals.
    """
    from .data import KNOWN_VOCABULARY
    if known_vocab is None:
        known_vocab = KNOWN_VOCABULARY

    roots = sorted(known_vocab.keys(), key=len, reverse=True)  # longest first
    proposals = []

    seen = set()
    for token in extract_all_tokens(inscriptions):
        if token in seen:
            continue
        seen.add(token)

        parts = split_morphemes(token)
        segmentation = []
        for part in parts:
            matched = False
            for root in roots:
                if part == root:
                    segmentation.append({"segment": root, "type": "root", "meaning": known_vocab[root]["translation"]})
                    matched = True
                    break
                elif part.startswith(root) and len(part) > len(root):
                    remainder = part[len(root):]
                    segmentation.append({"segment": root, "type": "root", "meaning": known_vocab[root]["translation"]})
                    segmentation.append({"segment": remainder, "type": "suffix_candidate"})
                    matched = True
                    break
            if not matched:
                # Check if it could be a proper name (capitalized)
                if part and part[0].isupper():
                    segmentation.append({"segment": part, "type": "proper_name"})
                else:
                    segmentation.append({"segment": part, "type": "unknown"})

        proposals.append({
            "token": token,
            "original_parts": parts,
            "segmentation": segmentation,
        })

    return proposals


def run_morpheme_analysis(inscriptions: list[dict]) -> dict:
    """Run the full morpheme analysis pipeline and return results."""
    print("=" * 70)
    print("MORPHEME PATTERN ANALYSIS")
    print("=" * 70)

    # 1. Word frequency
    wf = word_frequency(inscriptions)
    print(f"\n--- Word Frequencies (top 25) ---")
    for word, count in wf.most_common(25):
        print(f"  {word:30s}  {count:3d}")

    # 2. Morpheme frequency
    mf = morpheme_frequency(inscriptions)
    print(f"\n--- Morpheme Frequencies (top 25) ---")
    for morph, count in mf.most_common(25):
        print(f"  {morph:20s}  {count:3d}")

    # 3. Bigram patterns
    bg = ngram_frequency(inscriptions, n=2)
    print(f"\n--- Bigram Patterns (top 15) ---")
    for gram, count in bg.most_common(15):
        print(f"  {' : '.join(gram):40s}  {count:3d}")

    # 4. Trigram patterns
    tg = ngram_frequency(inscriptions, n=3)
    print(f"\n--- Trigram Patterns (top 10) ---")
    for gram, count in tg.most_common(10):
        print(f"  {' : '.join(gram):50s}  {count:3d}")

    # 5. Affix detection
    affixes = detect_affixes(inscriptions)
    print(f"\n--- Detected Suffixes ---")
    for affix, info in affixes["suffixes"].items():
        print(f"  {affix:10s}  count={info['count']:3d}  function={info['function']}")
    print(f"\n--- Detected Prefixes ---")
    for affix, info in affixes["prefixes"].items():
        print(f"  {affix:10s}  count={info['count']:3d}  function={info['function']}")

    # 6. Structural patterns
    patterns = find_word_patterns(inscriptions)
    print(f"\n--- Word Structure Templates ---")
    for template, info in patterns.items():
        print(f"  {template:25s}  count={info['count']:3d}  examples: {', '.join(info['examples'][:5])}")

    # 7. Morpheme boundary proposals
    boundaries = detect_morpheme_boundaries(inscriptions)
    print(f"\n--- Morpheme Boundary Proposals (complex tokens) ---")
    for prop in boundaries:
        if len(prop["segmentation"]) > 1 or any(s["type"] == "suffix_candidate" for s in prop["segmentation"]):
            segments_str = " + ".join(
                f"[{s['segment']}({s['type']}" + (f"={s.get('meaning', '')}" if s.get('meaning') else "") + ")]"
                for s in prop["segmentation"]
            )
            print(f"  {prop['token']:30s} → {segments_str}")

    return {
        "word_frequency": wf,
        "morpheme_frequency": mf,
        "bigrams": bg,
        "trigrams": tg,
        "affixes": affixes,
        "patterns": patterns,
        "boundary_proposals": boundaries,
    }
