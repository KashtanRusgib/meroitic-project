"""
Inscription Type Clustering
=============================
Clusters Meroitic inscriptions by type (funerary, royal, religious) using
lexical feature vectors and unsupervised clustering methods.

Since we work with a small corpus and no heavy dependencies are required,
this module implements lightweight clustering from scratch:
  - TF feature vectors from token frequencies
  - Cosine similarity
  - Agglomerative (hierarchical) clustering
  - Supervised type-signature detection based on known keyword profiles
"""

import math
from collections import Counter, defaultdict
from typing import Optional


def tokenize(text: str) -> list[str]:
    """Split inscription text into base morphemes (split on : and -)."""
    tokens = []
    for word in text.split(":"):
        word = word.strip()
        if word:
            for morph in word.split("-"):
                morph = morph.strip()
                if morph:
                    tokens.append(morph.lower())
    return tokens


# Known type-signature keywords (based on scholarly analysis)
TYPE_SIGNATURES = {
    "funerary": {
        "keywords": {"ate", "yi", "wos", "pesto", "abr", "kdi", "lh", "sr"},
        "strong_markers": {"ate", "yi"},  # offering formula terms
        "description": "Offering tables and funerary stelae with the standard offering formula",
    },
    "royal": {
        "keywords": {"qore", "kdke", "ktke", "amni", "tenke", "akine", "to", "beke", "qo"},
        "strong_markers": {"qore", "kdke"},
        "description": "Royal enthronement texts, decrees, and commemorative stelae",
    },
    "religious": {
        "keywords": {"apedmk", "mk", "sebke", "mhe", "mnp", "selele", "plote"},
        "strong_markers": {"apedmk", "sebke", "mhe"},
        "description": "Temple inscriptions, votive texts, and graffiti at religious sites",
    },
}


def compute_tf_vectors(inscriptions: list[dict]) -> list[dict]:
    """Compute term-frequency feature vectors for each inscription."""
    vectors = []
    for insc in inscriptions:
        tokens = tokenize(insc["text"])
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        vector = {token: count / total for token, count in tf.items()}
        vectors.append({
            "id": insc["id"],
            "vector": vector,
            "tokens": tokens,
            "metadata": {k: v for k, v in insc.items() if k != "text"},
        })
    return vectors


def cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse feature vectors."""
    common_keys = set(v1.keys()) & set(v2.keys())
    if not common_keys:
        return 0.0
    dot = sum(v1[k] * v2[k] for k in common_keys)
    norm1 = math.sqrt(sum(val ** 2 for val in v1.values()))
    norm2 = math.sqrt(sum(val ** 2 for val in v2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def compute_similarity_matrix(vectors: list[dict]) -> list[list[float]]:
    """Compute pairwise cosine similarity matrix."""
    n = len(vectors)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            sim = cosine_similarity(vectors[i]["vector"], vectors[j]["vector"])
            matrix[i][j] = sim
            matrix[j][i] = sim
    return matrix


def agglomerative_cluster(vectors: list[dict], sim_matrix: list[list[float]],
                          n_clusters: int = 3) -> list[list[int]]:
    """Simple agglomerative (average-linkage) clustering.

    Returns list of clusters, each a list of inscription indices.
    """
    n = len(vectors)
    # Start with each item in its own cluster
    clusters: list[set[int]] = [set([i]) for i in range(n)]
    active = set(range(n))

    while len(active) > n_clusters:
        best_sim = -1.0
        best_pair = (0, 0)
        active_list = sorted(active)
        for i_idx in range(len(active_list)):
            for j_idx in range(i_idx + 1, len(active_list)):
                ci, cj = active_list[i_idx], active_list[j_idx]
                # Average linkage
                total_sim = 0.0
                count = 0
                for a in clusters[ci]:
                    for b in clusters[cj]:
                        total_sim += sim_matrix[a][b]
                        count += 1
                avg_sim = total_sim / count if count else 0
                if avg_sim > best_sim:
                    best_sim = avg_sim
                    best_pair = (ci, cj)

        # Merge best pair
        ci, cj = best_pair
        clusters[ci] = clusters[ci] | clusters[cj]
        active.discard(cj)

    return [sorted(clusters[i]) for i in sorted(active)]


def signature_based_classification(inscriptions: list[dict]) -> list[dict]:
    """Classify inscriptions by matching against known type signatures.

    Returns classification results with confidence scores.
    """
    results = []
    for insc in inscriptions:
        tokens = set(tokenize(insc["text"]))
        scores = {}
        for type_name, sig in TYPE_SIGNATURES.items():
            keyword_overlap = tokens & sig["keywords"]
            strong_overlap = tokens & sig["strong_markers"]
            # Score: weighted by strong markers
            score = len(keyword_overlap) + 2 * len(strong_overlap)
            scores[type_name] = {
                "score": score,
                "keyword_matches": keyword_overlap,
                "strong_matches": strong_overlap,
            }

        best_type = max(scores.keys(), key=lambda t: scores[t]["score"])
        total_score = sum(s["score"] for s in scores.values())
        confidence = scores[best_type]["score"] / total_score if total_score else 0

        results.append({
            "id": insc["id"],
            "predicted_type": best_type,
            "confidence": confidence,
            "actual_type": insc.get("type", "unknown"),
            "scores": scores,
            "correct": best_type == insc.get("type", ""),
        })
    return results


def extract_type_profiles(inscriptions: list[dict]) -> dict:
    """Extract lexical profiles for each inscription type.

    Shows which words/morphemes are characteristic of each type.
    """
    type_tokens: dict[str, list[str]] = defaultdict(list)
    for insc in inscriptions:
        itype = insc.get("type", "unknown")
        type_tokens[itype].extend(tokenize(insc["text"]))

    profiles = {}
    all_counter = Counter()
    for tokens in type_tokens.values():
        all_counter.update(tokens)

    for itype, tokens in type_tokens.items():
        counter = Counter(tokens)
        total = len(tokens)
        # Compute relative frequency vs corpus average
        distinctive = {}
        for token, count in counter.items():
            tf = count / total
            corpus_tf = all_counter[token] / sum(all_counter.values())
            ratio = tf / corpus_tf if corpus_tf > 0 else 0
            distinctive[token] = {
                "count": count,
                "tf": tf,
                "corpus_tf": corpus_tf,
                "distinctiveness": ratio,
            }
        # Sort by distinctiveness
        sorted_tokens = sorted(distinctive.items(), key=lambda x: -x[1]["distinctiveness"])
        profiles[itype] = {
            "total_tokens": total,
            "unique_tokens": len(counter),
            "distinctive_vocabulary": sorted_tokens[:15],
        }

    return profiles


def run_clustering(inscriptions: list[dict]) -> dict:
    """Run the full clustering analysis and print results."""
    print("=" * 70)
    print("INSCRIPTION TYPE CLUSTERING")
    print("=" * 70)

    # 1. Signature-based classification
    print("\n--- Signature-Based Classification ---")
    classifications = signature_based_classification(inscriptions)
    correct = sum(1 for c in classifications if c["correct"])
    total = len(classifications)
    print(f"  Accuracy: {correct}/{total} ({100 * correct / total:.1f}%)\n")

    print(f"  {'ID':12s} {'Predicted':12s} {'Actual':12s} {'Conf':6s} {'Match':5s}  Key Matches")
    for c in classifications:
        best = c["predicted_type"]
        matches = c["scores"][best]["keyword_matches"] | c["scores"][best]["strong_matches"]
        match_str = ", ".join(sorted(matches)[:5])
        mark = "✓" if c["correct"] else "✗"
        print(f"  {c['id']:12s} {c['predicted_type']:12s} {c['actual_type']:12s} {c['confidence']:.3f} {mark:5s}  {match_str}")

    # 2. Unsupervised clustering
    print(f"\n--- Unsupervised Agglomerative Clustering (k=3) ---")
    vectors = compute_tf_vectors(inscriptions)
    sim_matrix = compute_similarity_matrix(vectors)
    clusters = agglomerative_cluster(vectors, sim_matrix, n_clusters=3)

    for ci, members in enumerate(clusters):
        print(f"\n  Cluster {ci + 1} ({len(members)} inscriptions):")
        type_dist = Counter()
        for idx in members:
            itype = inscriptions[idx].get("type", "unknown")
            type_dist[itype] += 1
            print(f"    {inscriptions[idx]['id']:12s}  {itype:12s}  {inscriptions[idx].get('site', ''):20s}")
        print(f"    Type distribution: {dict(type_dist)}")

    # 3. Type profiles
    print(f"\n--- Lexical Profiles by Type ---")
    profiles = extract_type_profiles(inscriptions)
    for itype, profile in profiles.items():
        print(f"\n  Type: {itype.upper()}")
        print(f"    Total tokens: {profile['total_tokens']}, Unique: {profile['unique_tokens']}")
        print(f"    Most distinctive vocabulary:")
        for token, stats in profile["distinctive_vocabulary"]:
            print(f"      {token:15s}  count={stats['count']:2d}  tf={stats['tf']:.3f}  distinctiveness={stats['distinctiveness']:.2f}")

    # 4. Similarity analysis between types
    print(f"\n--- Inter-Type Similarity ---")
    type_groups: dict[str, list[int]] = defaultdict(list)
    for i, insc in enumerate(inscriptions):
        type_groups[insc.get("type", "unknown")].append(i)

    types = sorted(type_groups.keys())
    print(f"  {'':15s}", end="")
    for t in types:
        print(f"  {t:12s}", end="")
    print()
    for t1 in types:
        print(f"  {t1:15s}", end="")
        for t2 in types:
            sims = []
            for i in type_groups[t1]:
                for j in type_groups[t2]:
                    sims.append(sim_matrix[i][j])
            avg = sum(sims) / len(sims) if sims else 0
            print(f"  {avg:12.3f}", end="")
        print()

    return {
        "classifications": classifications,
        "clusters": clusters,
        "profiles": profiles,
        "similarity_matrix": sim_matrix,
    }
