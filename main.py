from fastapi import FastAPI, HTTPException
import sqlite3
import subprocess
import pandas as pd
import re
import requests
import os

app = FastAPI()

# Initialize SQLite database
os.makedirs("db", exist_ok=True)
conn = sqlite3.connect("db/meroitic.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS inscriptions (
    id TEXT PRIMARY KEY,
    site TEXT,
    museum TEXT,
    text TEXT,
    transliteration TEXT,
    context TEXT
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS vocabulary (
    word TEXT PRIMARY KEY,
    translation TEXT,
    notes TEXT
)
""")
conn.execute("""
CREATE TABLE IF NOT EXISTS analysis (
    id TEXT PRIMARY KEY,
    inscription_id TEXT,
    translation TEXT,
    confidence REAL,
    explanation TEXT,
    FOREIGN KEY (inscription_id) REFERENCES inscriptions(id)
)
""")
conn.commit()
conn.close()

@app.post("/scrape_inscriptions")
async def scrape_inscriptions(url: str):
    os.makedirs("data", exist_ok=True)
    result = subprocess.run(["node", "scrape.js", url], capture_output=True, text=True)
    with open("data/inscriptions.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
    cleaned = re.sub(r"<[^>]+>", "", result.stdout)
    lines = cleaned.split("\n")
    
    # Connect to database to check for existing IDs
    conn = sqlite3.connect("db/meroitic.db")
    existing_ids = set(row[0] for row in conn.execute("SELECT id FROM inscriptions").fetchall())
    
    # Generate unique IDs
    new_data = []
    base_id = len(existing_ids)
    for i in range(len(lines)):
        new_id = f"BM_{base_id + i}"
        while new_id in existing_ids:
            base_id += 1
            new_id = f"BM_{base_id + i}"
        new_data.append({
            "id": new_id,
            "site": "Unknown",
            "museum": "British Museum",
            "text": lines[i],
            "transliteration": "",
            "context": "Unknown"
        })
        existing_ids.add(new_id)
    
    df = pd.DataFrame(new_data)
    df.to_sql("inscriptions", conn, if_exists="append", index=False)
    conn.close()
    df.to_csv("data/meroitic_inscriptions.csv", index=False, mode='a', header=False)
    return {"status": "success", "data": lines}

@app.post("/transcribe")
async def transcribe(inscription_id: str, text: str, transliteration: str):
    conn = sqlite3.connect("db/meroitic.db")
    conn.execute("UPDATE inscriptions SET text = ?, transliteration = ? WHERE id = ?",
                 (text, transliteration, inscription_id))
    conn.commit()
    conn.close()
    return {"status": "success"}
