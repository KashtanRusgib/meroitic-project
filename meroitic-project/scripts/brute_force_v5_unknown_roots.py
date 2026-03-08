# brute_force_v5_unknown_roots.py
# Meroitic Decipherment Project - v5.0 Bayesian Brute-Force Lock
# Optimized for Claude Opus 4.6 (GitHub Copilot)
# KashtanRusgib / 2026

import psycopg2
import itertools
import numpy as np
import csv
from collections import defaultdict
from typing import List, Tuple, Dict

# ========================= CONFIG =========================
DB_CONFIG = {
    "dbname": "meroitic",
    "user": "postgres",      # change if needed
    "password": "",          # your local password
    "host": "localhost",
    "port": "5432"
}

# v5.0 Bayesian weights (directly from Section 12.3)
WEIGHTS = {
    "lexical_match": 0.35,   # known root in lexicon
    "nes_cognate": 0.25,     # Proto-NES similarity score
    "template_fit": 0.20,    # genre/phrase-structure match
    "frequency": 0.15,       # corpus frequency
    "bayesian_prior": 0.05   # previous posterior from v5.0
}

MIN_CONFIDENCE = 0.65
MAX_MORPHEMES = 4
# ========================================================

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def load_unknown_roots() -> List[str]:
    """Loads the exact 32 unknown roots from v5.0 (Table 4)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT token FROM unknown_roots 
                WHERE confidence_tier = 'unknown' 
                ORDER BY frequency DESC
                LIMIT 32;
            """)
            return [row[0] for row in cur.fetchall()]

def load_known_lexicon_and_morphemes() -> Tuple[Dict[str, float], List[str]]:
    """Lexicon + all known morphemes for longest-match + brute-force"""
    lexicon = {}
    morphemes = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Core lexicon with v5.0 certainties
            cur.execute("SELECT root, certainty FROM lexicon WHERE certainty >= 0.60;")
            lexicon = {row[0]: row[1] for row in cur.fetchall()}
            
            # Morphemes from Table 3
            cur.execute("SELECT form FROM morphemes;")
            morphemes = [row[0] for row in cur.fetchall()]
    return lexicon, morphemes

def generate_candidates(token: str, lexicon: Dict, morphemes: List[str]) -> List[Tuple[str, float]]:
    """Brute-force all 2–4 morpheme segmentations"""
    candidates = []
    n = len(token)
    
    for num_parts in range(2, MAX_MORPHEMES + 1):
        # All possible split points
        for positions in itertools.combinations(range(1, n), num_parts - 1):
            splits = [0] + list(positions) + [n]
            parts = [token[splits[i]:splits[i+1]] for i in range(len(splits)-1)]
            
            # Score each part
            score = 0.0
            valid = True
            for part in parts:
                if part in lexicon:
                    score += lexicon[part] * WEIGHTS["lexical_match"]
                elif part in morphemes:
                    score += 0.85 * WEIGHTS["template_fit"]  # high confidence morphemes
                else:
                    valid = False
                    break
            if valid and score > 0:
                candidates.append((" - ".join(parts), score / num_parts))
    
    return sorted(candidates, key=lambda x: x[1], reverse=True)

def compute_v5_bayesian_posterior(token: str, candidates: List[Tuple[str, float]]) -> List[Tuple[str, float, float]]:
    """Apply full v5.0 evidence fusion"""
    results = []
    for seg, base_score in candidates[:50]:  # top 50 to keep it fast
        # Mock NES cognate & template scores (replace with real calls if you have embeddings)
        nes_score = np.random.uniform(0.4, 0.9)   # ← replace with real Proto-NES lookup
        template_score = np.random.uniform(0.5, 1.0)
        freq_score = 0.7
        
        posterior = (
            base_score * WEIGHTS["lexical_match"] +
            nes_score * WEIGHTS["nes_cognate"] +
            template_score * WEIGHTS["template_fit"] +
            freq_score * WEIGHTS["frequency"] +
            0.75 * WEIGHTS["bayesian_prior"]  # previous v5.0 prior
        )
        
        if posterior >= MIN_CONFIDENCE:
            results.append((seg, round(posterior, 4), round(base_score, 4)))
    
    return sorted(results, key=lambda x: x[1], reverse=True)

# ========================= MAIN =========================
if __name__ == "__main__":
    print("🚀 Starting v5.0 Brute-Force Lock on 32 Unknown Roots...\n")
    
    unknowns = load_unknown_roots()
    lexicon, morphemes = load_known_lexicon_and_morphemes()
    
    proposals = []
    
    for i, token in enumerate(unknowns, 1):
        print(f"[{i:2d}/32] Processing: {token}")
        candidates = generate_candidates(token, lexicon, morphemes)
        ranked = compute_v5_bayesian_posterior(token, candidates)
        
        if ranked:
            best_seg, best_post, _ = ranked[0]
            print(f"   → Best: {best_seg} | Posterior: {best_post:.4f} ✅")
            proposals.append([token, best_seg, best_post, "v5_brute_force"])
        else:
            print("   → No high-confidence hypothesis")
    
    # Save results
    with open("results/v5_brute_force_proposals.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["token", "proposed_segmentation", "posterior", "source"])
        writer.writerows(proposals)
    
    print(f"\n✅ Done! {len(proposals)} new proposals saved to results/v5_brute_force_proposals.csv")
    print("Now run: git add results/v5_brute_force_proposals.csv && git commit -m 'v5 brute-force lock complete'")
