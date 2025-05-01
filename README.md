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
- Analyzed ~500 inscriptions with phonological and Nubian comparison algorithms.
- Built PostgreSQL database with indexing.
- Incorporated REM and FHN references.

## License
MIT License

## Contact
[Your email]
