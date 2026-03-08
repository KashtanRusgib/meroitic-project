# Meroitic Script Decipherment Project

This repository contains code, database schema, and datasets for deciphering Meroitic script (3rd century BCE–5th century CE).

## Project Structure
- **src/**: Python scripts for linguistic analysis.
- **data/**: Sample datasets.
- **db/**: PostgreSQL schema and sample data.
- **kushites/**: Meroitic research files (LFS).
- **REMimagesMeroitic/**: Inscription images (LFS).
- **scripts/**: Additional scripts.
- **mcp_servers/**: Server code.
- **docs/**: Documentation.
- **logs/**: Summaries of large logs.

## Setup Instructions
1. Clone: `git clone https://github.com/mreggx/meroitic-project.git`
2. Install Git LFS: `git lfs install`
3. Pull LFS files: `git lfs pull`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up database: `psql -f db/schema.sql` and `psql -f db/sample_data.sql`
6. Run: `python src/main.py`

## Datasets
- **Standard Git**: Samples (e.g., `sample_inscriptions.csv`, <10 MB).
- **LFS**: Key files (e.g., `kushites/rem_0000-0000_2000_num_1_1_845.pdf`, 206 MB).
- **External**: PDFs, logs at [Zenodo/Google Drive link].

## Progress

### v6.0 — Heavy-Compute Decipherment Engine (latest)

Leverages full Codespace compute for exhaustive decipherment:

| Metric | Value |
|--------|-------|
| Corpus size | 103 inscriptions (66 original + 37 expanded) |
| Total tokens | 984 |
| Unique tokens | 116 |
| Unknown tokens | 85 (73%) |
| Brute-force hypotheses | 784 morphological segmentations |
| MCMC samples | 9,840,000 (10K per token) |
| Belief propagation iterations | 2 (converged) |
| Average posterior | 0.070 |
| New readings proposed | 30 |
| Tokens solved (root known) | 11 |
| NES cognate proposals | 50 |
| Elapsed compute time | 15.7s |

**Key NES cognate proposals:**

| Token | Root | NES Proto-form | Meaning | Similarity |
|-------|------|---------------|---------|-----------|
| beletense | bel | \*ber | door/gate | 0.933 |
| menteyose | me | \*ne | holy/sacred | 0.867 |
| akinimnoteri | ak | \*ag | mouth | 0.867 |
| se | se | \*he | to come | 0.870 |

**Source distribution for Bayesian decoder:**

| Source | Count |
|--------|-------|
| Lexicon (known vocabulary) | 885 |
| Onomastic (proper names) | 76 |
| Comparative (NES cognates) | 15 |
| Comparative via brute-force | 4 |
| Segmentation analysis | 3 |
| Distributional transfer | 1 |

**Confidence by inscription type:**

| Type | Count | Avg Posterior |
|------|-------|--------------|
| Funerary | 56 | 0.0816 |
| Religious | 28 | 0.0575 |
| Royal | 19 | 0.0489 |

**Engine architecture:**
1. **Exhaustive Brute-Force Segmenter** — generates all prefix+root+suffix decompositions (up to 6 morphemes), scores against 8 criteria (root recognition, frequency, NES cognate similarity, morpheme coherence, positional template, cross-inscription consistency, phonotactic well-formedness, suffix certainty)
2. **Bayesian MCMC Decoder** — 8 evidence channels (lexicon, bilingual, comparative, distributional, positional, template, phonotactic, cross-inscription), Metropolis-Hastings sampling (10K samples/token), iterative belief propagation across all inscriptions
3. **Weighted Levenshtein NES Matcher** — Meroitic-specific phonological substitution costs for all 125 NES proto-forms

Run: `python3 scripts/heavy_compute_decipherment.py`

### Previous versions
- **v5.0**: 16-stage pipeline with Bayesian decoder, distributional semantics, Proto-NES reconstruction
- **v4.0**: 12-stage pipeline with NES lexicon, bilingual analysis, cryptanalysis, brute-force segmenter
- **v3.0**: Cognate mining, morphosyntax, template engine, corpus ingestion
- **v1–v2**: Core analysis suite, cross-corpus consistency, phonological comparison

## License
MIT License

## Contact
[Your email]
