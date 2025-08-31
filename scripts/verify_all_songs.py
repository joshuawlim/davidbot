#!/usr/bin/env python3
"""Verify BPM and key data for ALL 69 songs in the database."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from davidbot.database.database import get_db_session
from sqlalchemy import text

def get_all_songs():
    """Get all songs from database for verification."""
    print("🎵 Complete Database Verification - All 69 Songs")
    print("=" * 60)
    
    with get_db_session() as session:
        songs = session.execute(
            text("SELECT song_id, title, artist, original_key, bpm FROM songs WHERE is_active = true ORDER BY title")
        ).fetchall()
        
    print(f"Found {len(songs)} songs to verify\n")
    return songs

def generate_complete_checklist(songs):
    """Generate verification checklist for all songs."""
    print("📋 COMPLETE VERIFICATION CHECKLIST - ALL SONGS")
    print("=" * 60)
    print("Visit MultiTracks.com and verify each song's Key and BPM:")
    print("Copy this data into a spreadsheet or document for easy reference.\n")
    
    # Group by first letter for easier navigation
    songs_by_letter = {}
    for song in songs:
        first_letter = song.title[0].upper()
        if first_letter not in songs_by_letter:
            songs_by_letter[first_letter] = []
        songs_by_letter[first_letter].append(song)
    
    for letter in sorted(songs_by_letter.keys()):
        print(f"\n{'='*5} {letter} {'='*5}")
        for i, song in enumerate(songs_by_letter[letter], 1):
            search_title = song.title.replace(' ', '%20').replace('(', '%28').replace(')', '%29')
            print(f"\n{song.song_id:2d}. {song.title} - {song.artist}")
            print(f"    Current DB: Key {song.original_key} | {song.bpm} BPM")
            print(f"    URL: https://www.multitracks.com/search?q={search_title}")
            print(f"    ✓ Verified Key: ___  ✓ Verified BPM: ___")
            print(f"    ✓ Matches DB: ___  ✓ Notes: _______________")

def generate_verification_template(songs):
    """Generate a structured template for recording verification results."""
    print("📊 VERIFICATION DATA TEMPLATE")
    print("=" * 50)
    print("Copy this template and fill in verified data:")
    print()
    print("VERIFIED_DATA = {")
    
    for song in songs:
        title_key = song.title
        print(f'    "{title_key}": {{')
        print(f'        "artist": "{song.artist}",')
        print(f'        "current_key": "{song.original_key}",')
        print(f'        "current_bpm": {song.bpm},')
        print(f'        "correct_key": "",  # Fill from MultiTracks')
        print(f'        "correct_bpm": 0,   # Fill from MultiTracks')
        print(f'        "source": "MultiTracks.com verified YYYY-MM-DD",')
        print(f'        "matches": False,   # True if current data is correct')
        print(f'        "notes": ""')
        print(f'    }},')
    
    print("}")

def create_csv_template(songs):
    """Create a CSV template for easier data entry."""
    csv_filename = "song_verification_template.csv"
    
    print(f"\n📄 Creating CSV template: {csv_filename}")
    
    with open(csv_filename, 'w') as f:
        # Header
        f.write("song_id,title,artist,current_key,current_bpm,verified_key,verified_bpm,source,matches_db,notes\n")
        
        # Data rows
        for song in songs:
            f.write(f'{song.song_id},"{song.title}","{song.artist}",{song.original_key},{song.bpm},,,MultiTracks.com,,\n')
    
    print(f"✅ CSV template created: {csv_filename}")
    print(f"   1. Open in Excel/Google Sheets")
    print(f"   2. Fill in verified_key and verified_bpm columns")
    print(f"   3. Mark matches_db as TRUE/FALSE")
    print(f"   4. Add notes for any issues")
    print(f"   5. Use this data to create correction script")

def generate_batch_urls(songs):
    """Generate batched URLs for efficient verification."""
    print(f"\n🔗 BATCH VERIFICATION URLS")
    print("=" * 40)
    print("Open these in browser tabs (10 songs per batch):")
    
    batch_size = 10
    for i in range(0, len(songs), batch_size):
        batch = songs[i:i+batch_size]
        print(f"\n📦 Batch {i//batch_size + 1} (Songs {i+1}-{min(i+batch_size, len(songs))}):")
        
        for song in batch:
            search_title = song.title.replace(' ', '%20').replace('(', '%28').replace(')', '%29')
            print(f"   https://www.multitracks.com/search?q={search_title}")

def show_database_summary(songs):
    """Show summary statistics of current database."""
    print(f"\n📊 DATABASE SUMMARY")
    print("=" * 30)
    print(f"Total songs: {len(songs)}")
    
    # BPM distribution
    bpm_ranges = {
        "Slow (≤85)": 0,
        "Moderate (86-120)": 0, 
        "Fast (≥121)": 0,
        "Missing BPM": 0
    }
    
    # Key distribution
    keys = {}
    
    for song in songs:
        # BPM analysis
        if not song.bpm:
            bpm_ranges["Missing BPM"] += 1
        elif song.bpm <= 85:
            bpm_ranges["Slow (≤85)"] += 1
        elif song.bpm <= 120:
            bpm_ranges["Moderate (86-120)"] += 1
        else:
            bpm_ranges["Fast (≥121)"] += 1
        
        # Key analysis
        key = song.original_key or "Missing"
        keys[key] = keys.get(key, 0) + 1
    
    print("\n🥁 BPM Distribution:")
    for range_name, count in bpm_ranges.items():
        percentage = (count / len(songs)) * 100
        print(f"   {range_name}: {count} songs ({percentage:.1f}%)")
    
    print("\n🎹 Key Distribution:")
    for key in sorted(keys.keys()):
        count = keys[key]
        percentage = (count / len(songs)) * 100
        print(f"   {key}: {count} songs ({percentage:.1f}%)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Verify all songs in database')
    parser.add_argument('--checklist', action='store_true', help='Generate verification checklist')
    parser.add_argument('--template', action='store_true', help='Generate verification data template')
    parser.add_argument('--csv', action='store_true', help='Create CSV template for data entry')
    parser.add_argument('--urls', action='store_true', help='Generate batch URLs')
    parser.add_argument('--summary', action='store_true', help='Show database summary')
    parser.add_argument('--all', action='store_true', help='Generate all outputs')
    args = parser.parse_args()
    
    songs = get_all_songs()
    
    if args.all or args.summary:
        show_database_summary(songs)
    
    if args.all or args.checklist:
        generate_complete_checklist(songs)
    
    if args.all or args.urls:
        generate_batch_urls(songs)
    
    if args.all or args.csv:
        create_csv_template(songs)
    
    if args.all or args.template:
        generate_verification_template(songs)
    
    if not any([args.checklist, args.template, args.csv, args.urls, args.summary, args.all]):
        print("Use --help to see available options")
        print("Recommended: python3 verify_all_songs.py --csv --urls --summary")