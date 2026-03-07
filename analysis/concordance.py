"""
Concordance Builder for Meroitic Inscriptions
===============================================
Builds word-level and morpheme-level concordances (KWIC — Key Word In Context)
across all known inscriptions. Shows every occurrence of every word/morpheme
with its surrounding context and source inscription metadata.
"""

from collections import defaultdict


def tokenize(text: str) -> list[str]:
    """Split inscription text into tokens."""
    return [t.strip() for t in text.split(":") if t.strip()]


def build_word_concordance(inscriptions: list[dict]) -> dict[str, list[dict]]:
    """Build a concordance mapping each unique word to all its occurrences with context.

    Returns a dict: word -> list of occurrence records with:
        - inscription_id, site, type
        - left_context, right_context (neighbouring tokens)
        - position (token index in inscription)
    """
    concordance: dict[str, list[dict]] = defaultdict(list)

    for insc in inscriptions:
        tokens = tokenize(insc["text"])
        for i, token in enumerate(tokens):
            left = tokens[max(0, i - 2) : i]
            right = tokens[i + 1 : i + 3]
            concordance[token].append({
                "inscription_id": insc["id"],
                "site": insc.get("site", ""),
                "type": insc.get("type", ""),
                "subtype": insc.get("subtype", ""),
                "position": i,
                "left_context": " : ".join(left),
                "keyword": token,
                "right_context": " : ".join(right),
                "full_text": insc["text"],
            })

    return dict(concordance)


def build_morpheme_concordance(inscriptions: list[dict]) -> dict[str, list[dict]]:
    """Build a concordance at the morpheme level (splitting on hyphens)."""
    concordance: dict[str, list[dict]] = defaultdict(list)

    for insc in inscriptions:
        tokens = tokenize(insc["text"])
        for i, token in enumerate(tokens):
            morphemes = [m for m in token.split("-") if m]
            for j, morph in enumerate(morphemes):
                concordance[morph].append({
                    "inscription_id": insc["id"],
                    "site": insc.get("site", ""),
                    "type": insc.get("type", ""),
                    "parent_token": token,
                    "morph_position": j,
                    "token_position": i,
                })

    return dict(concordance)


def build_collocations(inscriptions: list[dict], window: int = 2) -> dict[str, dict[str, int]]:
    """Build collocation statistics: for each word, count how often other words
    appear within a window of +/- `window` tokens.
    """
    collocations: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for insc in inscriptions:
        tokens = tokenize(insc["text"])
        for i, token in enumerate(tokens):
            for j in range(max(0, i - window), min(len(tokens), i + window + 1)):
                if i != j:
                    collocations[token][tokens[j]] += 1

    return {k: dict(v) for k, v in collocations.items()}


def format_kwic(occurrences: list[dict], max_show: int = 10) -> str:
    """Format KWIC (Key Word In Context) display for a word."""
    lines = []
    for occ in occurrences[:max_show]:
        left = occ["left_context"].rjust(30)
        kw = occ["keyword"].center(20)
        right = occ["right_context"].ljust(30)
        ref = f"[{occ['inscription_id']}, {occ['site']}, {occ['type']}]"
        lines.append(f"  {left} |{kw}| {right}  {ref}")
    if len(occurrences) > max_show:
        lines.append(f"  ... and {len(occurrences) - max_show} more occurrences")
    return "\n".join(lines)


def run_concordance(inscriptions: list[dict]) -> dict:
    """Run the full concordance analysis and print results."""
    print("=" * 70)
    print("CONCORDANCE ANALYSIS")
    print("=" * 70)

    # 1. Word concordance
    word_conc = build_word_concordance(inscriptions)
    print(f"\nTotal unique words/tokens: {len(word_conc)}")

    # Sort by frequency
    sorted_words = sorted(word_conc.items(), key=lambda x: -len(x[1]))

    print(f"\n--- KWIC Concordance (top 15 most frequent words) ---")
    for word, occurrences in sorted_words[:15]:
        print(f"\n  '{word}' — {len(occurrences)} occurrences:")
        print(format_kwic(occurrences))

    # 2. Morpheme concordance
    morph_conc = build_morpheme_concordance(inscriptions)
    sorted_morphs = sorted(morph_conc.items(), key=lambda x: -len(x[1]))

    print(f"\n--- Morpheme Concordance (top 15) ---")
    for morph, occurrences in sorted_morphs[:15]:
        # Show which parent tokens contain this morpheme
        parent_tokens = list(set(o["parent_token"] for o in occurrences))
        type_dist = defaultdict(int)
        for o in occurrences:
            type_dist[o["type"]] += 1
        print(f"\n  morpheme '{morph}' — {len(occurrences)} occurrences")
        print(f"    parent tokens: {', '.join(parent_tokens[:8])}")
        print(f"    type distribution: {dict(type_dist)}")

    # 3. Collocations
    collocs = build_collocations(inscriptions, window=2)
    print(f"\n--- Strong Collocations (words that frequently co-occur) ---")
    pairs_seen = set()
    colloc_pairs = []
    for word, neighbors in collocs.items():
        for neighbor, count in neighbors.items():
            pair = tuple(sorted([word, neighbor]))
            if pair not in pairs_seen and count >= 3:
                pairs_seen.add(pair)
                colloc_pairs.append((word, neighbor, count))
    colloc_pairs.sort(key=lambda x: -x[2])
    for w1, w2, count in colloc_pairs[:20]:
        print(f"  {w1:25s} <-> {w2:25s}  co-occurrences: {count}")

    # 4. Distribution by inscription type
    print(f"\n--- Word Distribution by Inscription Type ---")
    word_type_dist: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for word, occs in word_conc.items():
        for occ in occs:
            word_type_dist[word][occ["type"]] += 1

    for word, _ in sorted_words[:10]:
        dist = word_type_dist[word]
        dist_str = ", ".join(f"{t}={c}" for t, c in sorted(dist.items()))
        print(f"  {word:25s}  {dist_str}")

    return {
        "word_concordance": word_conc,
        "morpheme_concordance": morph_conc,
        "collocations": collocs,
        "word_type_distribution": word_type_dist,
    }
