#!/usr/bin/env python3
"""
Convert updatedlist_20250831.csv to JSON format for DavidBot import.
This script filters tags to only include approved tags from docs/tags.md.
"""

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Any


def load_approved_tags(tags_file: Path) -> Dict[str, str]:
    """Load approved tags from docs/tags.md"""
    approved_tags = {}  # lowercase -> original case mapping
    
    with open(tags_file, 'r') as f:
        for line in f:
            tag = line.strip()
            if tag:  # Skip empty lines
                approved_tags[tag.lower()] = tag  # Store lowercase mapping to original
    
    return approved_tags


def clean_tags(tag_string: str, approved_tags: Dict[str, str]) -> List[str]:
    """Clean and filter tags against approved list"""
    if not tag_string or pd.isna(tag_string):
        return []
    
    # Remove quotes and split by comma
    tag_string = str(tag_string).strip('"').strip("'")
    raw_tags = [tag.strip() for tag in tag_string.split(',')]
    
    # Filter against approved tags (case-insensitive)
    filtered_tags = []
    for tag in raw_tags:
        tag_clean = tag.strip()
        if tag_clean.lower() in approved_tags:
            # Use the original case from approved tags
            filtered_tags.append(approved_tags[tag_clean.lower()])
    
    return filtered_tags


def convert_csv_to_json(csv_file: Path, tags_file: Path, output_file: Path):
    """Convert CSV to JSON format for DavidBot import"""
    
    # Load approved tags
    print(f"Loading approved tags from {tags_file}")
    approved_tags = load_approved_tags(tags_file)
    print(f"Loaded {len(approved_tags)} approved tags")
    
    songs = []
    skipped_rows = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
            # Skip rows with missing essential data
            if not row.get('Title') or not row.get('Artist'):
                print(f"Skipping row {row_num}: Missing title or artist")
                skipped_rows += 1
                continue
            
            # Convert BPM to integer
            bpm = None
            if row.get('BPM') and str(row['BPM']).strip():
                try:
                    bpm = int(float(row['BPM']))
                except (ValueError, TypeError):
                    print(f"Warning: Invalid BPM '{row['BPM']}' for {row['Title']}")
            
            # Clean and filter tags
            tags = clean_tags(row.get('Tags', ''), approved_tags)
            
            # Process lead gender
            lead = row.get('Lead', '').strip()
            lead_gender = "Unknown"
            if lead in ['Male', 'Female']:
                lead_gender = lead
            elif 'Male/Female' in lead or 'Female/Male' in lead:
                lead_gender = "Both"
            elif lead:
                lead_gender = lead  # Keep original value if different format
            
            song = {
                "title": row['Title'].strip(),
                "artist": row['Artist'].strip(),
                "original_key": row.get('Key', '').strip() if row.get('Key') and row.get('Key').strip() else 'C',
                "bpm": bpm,
                "meter": row.get('Meter', '').strip() if row.get('Meter') else None,
                "tags": tags,
                "lead_gender": lead_gender,
                "url": row.get('Resource Link', '').strip() if row.get('Resource Link') else None,
                "lyrics": ""  # Empty placeholder for now
            }
            
            songs.append(song)
            
            # Log tag filtering for first few songs
            if row_num <= 5:
                original_tags = [tag.strip() for tag in str(row.get('Tags', '')).strip('"').split(',') if tag.strip()]
                filtered_count = len(tags)
                print(f"Row {row_num} ({song['title']}): {len(original_tags)} → {filtered_count} tags")
    
    print(f"\nProcessed {len(songs)} songs, skipped {skipped_rows} rows")
    print(f"Writing to {output_file}")
    
    # Write JSON output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {len(songs)} songs to JSON format")
    return len(songs)


def main():
    """Main function"""
    # Setup paths
    base_dir = Path(__file__).parent.parent
    csv_file = base_dir / "data" / "updatedlist_20250831.csv"
    tags_file = base_dir / "docs" / "tags.md"
    output_file = base_dir / "data" / "updatedlist_20250831.json"
    
    # Verify files exist
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        return 1
    
    if not tags_file.exists():
        print(f"Error: Tags file not found: {tags_file}")
        return 1
    
    print(f"Converting {csv_file} to {output_file}")
    print(f"Using approved tags from {tags_file}")
    
    try:
        song_count = convert_csv_to_json(csv_file, tags_file, output_file)
        
        print(f"\n✅ Success! Converted {song_count} songs")
        print(f"📁 Output file: {output_file}")
        print(f"\nNext steps:")
        print(f"1. Backup database: cp data/davidbot.db data/davidbot_backup_$(date +%Y%m%d).db")
        print(f"2. Import songs: PYTHONPATH=src python3 -m davidbot.manage import {output_file}")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    # Add pandas import at runtime if available
    try:
        import pandas as pd
    except ImportError:
        # Create a simple mock for pd.isna
        class pd:
            @staticmethod
            def isna(value):
                return value is None or value == '' or str(value).lower() == 'nan'
    
    sys.exit(main())