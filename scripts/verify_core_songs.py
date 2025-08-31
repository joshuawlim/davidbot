#!/usr/bin/env python3
"""Verify BPM and key data for the most commonly requested worship songs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from davidbot.database.database import get_db_session
from sqlalchemy import text

# Core worship songs that need accurate data verification
# Based on popularity, familiarity scores, and common worship themes
CORE_SONGS_TO_VERIFY = [
    # High familiarity/popular songs
    {"title": "Amazing Grace (My Chains Are Gone)", "artist": "Chris Tomlin"},
    {"title": "Goodness Of God", "artist": "Bethel Music"},
    {"title": "Way Maker", "artist": "Sinach"},
    {"title": "What a Beautiful Name", "artist": "Hillsong Worship"},
    {"title": "Great Are You Lord", "artist": "All Sons & Daughters"},
    
    # Common altar call songs
    {"title": "I Know That I Know", "artist": "The Belonging Co"},  # Known issue: 85→142 BPM
    {"title": "O Come to the Altar", "artist": "Elevation Worship"},
    {"title": "At The Altar", "artist": "Elevation Rhythm"},
    {"title": "Build My Life", "artist": "Pat Barrett"},
    
    # Fast/celebration songs
    {"title": "Good Day (Live)", "artist": "Planetshakers"},
    {"title": "Joy of the Lord (Live)", "artist": "Planetshakers"},
    {"title": "Forever YHWH", "artist": "Elevation Worship"},
    {"title": "Victory Shout", "artist": "Tasha Cobbs Leonard"},
    
    # Key ministry songs
    {"title": "Holy Forever", "artist": "Chris Tomlin"},
    {"title": "My Hallelujah", "artist": "Bethel Music"},
    {"title": "Center (Live)", "artist": "Bethel Music"},
    {"title": "Give Me Jesus", "artist": "UPPERROOM"},
]

# Manual verification data based on MultiTracks/authoritative sources
VERIFIED_DATA = {
    "I Know That I Know": {
        "artist": "The Belonging Co",
        "correct_key": "A",
        "correct_bpm": 142,
        "source": "MultiTracks.com verified",
        "notes": "Database had 85 BPM (wrong)"
    },
    # Add more as we verify them manually
}

def get_current_database_values():
    """Get current values for core songs from database."""
    print("🔍 Current Database Values for Core Songs")
    print("=" * 60)
    
    with get_db_session() as session:
        songs_data = []
        
        for song_info in CORE_SONGS_TO_VERIFY:
            result = session.execute(
                text("SELECT song_id, title, artist, original_key, bpm FROM songs WHERE title = :title AND artist = :artist"),
                {'title': song_info['title'], 'artist': song_info['artist']}
            ).fetchone()
            
            if result:
                song_data = {
                    'song_id': result.song_id,
                    'title': result.title,
                    'artist': result.artist,
                    'db_key': result.original_key,
                    'db_bpm': result.bpm,
                    'needs_verification': True
                }
                
                # Check if we have verified data
                if result.title in VERIFIED_DATA:
                    verified = VERIFIED_DATA[result.title]
                    song_data['verified_key'] = verified['correct_key']
                    song_data['verified_bpm'] = verified['correct_bpm']
                    song_data['source'] = verified['source']
                    song_data['key_correct'] = result.original_key == verified['correct_key']
                    song_data['bpm_correct'] = result.bpm == verified['correct_bpm']
                    song_data['needs_verification'] = not (song_data['key_correct'] and song_data['bpm_correct'])
                
                songs_data.append(song_data)
                
            else:
                print(f"❌ NOT FOUND: {song_info['title']} - {song_info['artist']}")
        
        return songs_data

def generate_verification_report(songs_data):
    """Generate a detailed verification report."""
    print(f"\n📊 CORE SONGS VERIFICATION REPORT")
    print("=" * 60)
    
    verified_count = 0
    error_count = 0
    needs_verification_count = 0
    
    for song in songs_data:
        print(f"\n🎵 {song['title']} - {song['artist']}")
        print(f"   ID: {song['song_id']}")
        print(f"   Database: Key {song['db_key']} | {song['db_bpm']} BPM")
        
        if 'verified_key' in song:
            # We have verification data
            if song['key_correct'] and song['bpm_correct']:
                print(f"   ✅ VERIFIED CORRECT")
                print(f"   Source: {song['source']}")
                verified_count += 1
            else:
                print(f"   ❌ DATA ERROR DETECTED")
                if not song['key_correct']:
                    print(f"      Key: {song['db_key']} → {song['verified_key']}")
                if not song['bpm_correct']:
                    print(f"      BPM: {song['db_bpm']} → {song['verified_bpm']}")
                print(f"   Source: {song['source']}")
                error_count += 1
        else:
            print(f"   ⚠️  NEEDS VERIFICATION")
            print(f"      Please verify against MultiTracks or authoritative source")
            needs_verification_count += 1
    
    print(f"\n📈 VERIFICATION SUMMARY")
    print(f"   ✅ Verified Correct: {verified_count}")
    print(f"   ❌ Errors Found: {error_count}")  
    print(f"   ⚠️  Needs Verification: {needs_verification_count}")
    print(f"   📊 Total Core Songs: {len(songs_data)}")
    
    if error_count > 0:
        print(f"\n🚨 CRITICAL: {error_count} songs have incorrect data!")
        print(f"   This will cause filtering and search issues.")
        print(f"   Run correction script to fix known errors.")
    
    if needs_verification_count > 0:
        print(f"\n📋 ACTION NEEDED: {needs_verification_count} songs need manual verification")
        print(f"   1. Look up each song on MultiTracks.com")
        print(f"   2. Note correct Key and BPM")
        print(f"   3. Add to VERIFIED_DATA in this script")
        print(f"   4. Run correction script to apply fixes")

def create_verification_checklist():
    """Create a checklist for manual verification."""
    print(f"\n📋 MANUAL VERIFICATION CHECKLIST")
    print("=" * 50)
    print(f"Visit MultiTracks.com and verify these songs:\n")
    
    checklist_count = 0
    for song_info in CORE_SONGS_TO_VERIFY:
        if song_info['title'] not in VERIFIED_DATA:
            checklist_count += 1
            print(f"{checklist_count:2d}. {song_info['title']} - {song_info['artist']}")
            print(f"    URL: https://www.multitracks.com/search?q={song_info['title'].replace(' ', '%20')}")
            print(f"    ✓ Key: ___  ✓ BPM: ___")
            print()
    
    print(f"Total songs to verify: {checklist_count}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Verify core worship song data')
    parser.add_argument('--checklist', action='store_true', help='Generate verification checklist')
    args = parser.parse_args()
    
    if args.checklist:
        create_verification_checklist()
    else:
        songs_data = get_current_database_values()
        generate_verification_report(songs_data)