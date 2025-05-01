#!/usr/bin/env python3
import re
import csv
import os
from pathlib import Path

def extract_inscription_data(file_path, rem_range_start, rem_range_end):
    """Extract data for inscriptions within a specified REM range from a text file, including transcription data."""
    inscriptions = []
    current_inscription = None
    rem_pattern = re.compile(r"REM (\d{4})")
    title_pattern = re.compile(r"^(.*?)(?:\s*\[.*?\])?$")
    transcription_start_keywords = ["fac-similé", "transcription", "épitaphe", "texte gravé", "inscription sur", "cursive", "gravée"]
    section_headers = ["bibliographie", "localisation actuelle", "description de l'inscription", "dimensions", "identification du monument"]
    in_transcription_section = False
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            rem_match = rem_pattern.search(line)
            if rem_match:
                rem_num = int(rem_match.group(1))
                if rem_range_start <= rem_num <= rem_range_end:
                    if current_inscription:
                        inscriptions.append(current_inscription)
                    # Start a new inscription entry
                    current_inscription = {
                        'rem_number': f"REM_{rem_num:04d}",
                        'title': '',
                        'origin': '',
                        'description': '',
                        'transcription': '',
                        'notes': '',
                        'image_path': ''
                    }
                    # Look for title in the current or next few lines
                    for j in range(i, min(i+5, len(lines))):
                        title_match = title_pattern.match(lines[j].strip())
                        if title_match and lines[j].strip() and not lines[j].startswith("REM"):
                            current_inscription['title'] = title_match.group(1).strip()
                            break
                    # Extract description or other details from surrounding lines
                    description_lines = []
                    for j in range(i+1, min(i+30, len(lines))):
                        if rem_pattern.search(lines[j]):
                            break
                        if any(keyword in lines[j].lower() for keyword in transcription_start_keywords):
                            in_transcription_section = True
                            break
                        description_lines.append(lines[j].strip())
                    current_inscription['description'] = ' '.join(description_lines).strip()
                    in_transcription_section = False
            elif current_inscription and line.strip():
                # Continue processing based on whether in transcription section
                if not rem_pattern.search(line):
                    if in_transcription_section:
                        current_inscription['transcription'] += ' ' + line.strip()
                        # Stop transcription section if we hit a new major section or another REM
                        if any(term in line.lower() for term in section_headers):
                            in_transcription_section = False
                    elif any(keyword in line.lower() for keyword in transcription_start_keywords):
                        in_transcription_section = True
                        current_inscription['transcription'] += ' ' + line.strip()
                    # Check for potential Meroitic script patterns (e.g., sequences of short words or special characters)
                    elif not in_transcription_section and (len(line.split()) < 5 and any(c in line for c in ":-&|")):
                        in_transcription_section = True
                        current_inscription['transcription'] += ' ' + line.strip()
                    else:
                        current_inscription['description'] += ' ' + line.strip()
    
    if current_inscription:
        inscriptions.append(current_inscription)
    
    return inscriptions

def update_csv(inscriptions, csv_path):
    """Update the CSV file with new inscription data."""
    # Read existing CSV data
    existing_data = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_data = list(reader)
    
    # Append new inscriptions, avoiding duplicates by REM number
    existing_rem_numbers = {row['rem_number'] for row in existing_data}
    for inscription in inscriptions:
        if inscription['rem_number'] not in existing_rem_numbers:
            existing_data.append(inscription)
    
    # Write updated data back to CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['rem_number', 'title', 'origin', 'description', 'transcription', 'notes', 'image_path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_data:
            writer.writerow(row)

def main():
    # Define paths
    text_files = [
        ("data/rem_0001_to_0387.txt", 1, 387),
        ("data/rem_0401_to_0851.txt", 401, 851),
        ("data/rem_1001_to_1278.txt", 1001, 1278)
    ]
    csv_path = "data/meroitic_inscriptions.csv"
    
    # Extract inscriptions from each text file
    all_inscriptions = []
    for file_path, start, end in text_files:
        print(f"Processing {file_path} for REM {start} to {end}...")
        inscriptions = extract_inscription_data(file_path, start, end)
        all_inscriptions.extend(inscriptions)
        print(f"Extracted {len(inscriptions)} inscriptions from {file_path}")
    
    # Update CSV with extracted data
    update_csv(all_inscriptions, csv_path)
    print(f"Updated {csv_path} with {len(all_inscriptions)} new inscriptions.")

if __name__ == "__main__":
    main()
