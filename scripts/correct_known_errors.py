#!/usr/bin/env python3
"""Correct known BPM and key errors based on MultiTracks verification."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from davidbot.database.database import get_db_session
from sqlalchemy import text

# Known corrections based on MultiTracks verification
CORRECTIONS = [
    {
        'title': 'I Know That I Know',
        'artist': 'The Belonging Co',
        'correct_key': 'A',       # Database has A (correct)
        'correct_bpm': 142,       # Database has 85 (WRONG) - should be 142
        'source': 'MultiTracks verified'
    },
    # Add more corrections as we find them
]

def apply_corrections(dry_run=True):
    """Apply known corrections to the database."""
    print("🔧 Known Musical Data Corrections")
    print("=" * 40)
    
    if dry_run:
        print("DRY RUN - No changes will be made")
    
    with get_db_session() as session:
        for correction in CORRECTIONS:
            print(f"\\n🎵 {correction['title']} - {correction['artist']}")
            
            # Find the song in database
            result = session.execute(
                text("SELECT song_id, original_key, bpm FROM songs WHERE title = :title AND artist = :artist"),
                {'title': correction['title'], 'artist': correction['artist']}
            ).fetchone()
            
            if not result:
                print(f"   ❌ Song not found in database")
                continue
            
            song_id, db_key, db_bpm = result
            needs_update = False
            updates = []
            params = {'song_id': song_id}
            
            # Check key
            if correction['correct_key'] != db_key:
                print(f"   🔑 Key correction: {db_key} → {correction['correct_key']}")
                updates.append("original_key = :correct_key")
                params['correct_key'] = correction['correct_key']
                needs_update = True
            else:
                print(f"   ✅ Key is correct: {db_key}")
            
            # Check BPM
            if correction['correct_bpm'] != db_bpm:
                print(f"   🥁 BPM correction: {db_bpm} → {correction['correct_bpm']}")
                updates.append("bpm = :correct_bpm") 
                params['correct_bpm'] = correction['correct_bpm']
                needs_update = True
            else:
                print(f"   ✅ BPM is correct: {db_bpm}")
            
            if needs_update and not dry_run:
                update_sql = f"UPDATE songs SET {', '.join(updates)} WHERE song_id = :song_id"
                session.execute(text(update_sql), params)
                print(f"   💾 Applied corrections")
            elif needs_update:
                print(f"   🔍 Would apply corrections (dry run)")
            else:
                print(f"   ✅ No corrections needed")
            
            print(f"   📋 Source: {correction['source']}")
        
        if not dry_run:
            session.commit()
            print(f"\\n✅ All corrections committed to database")
        else:
            print(f"\\n🔍 Dry run complete - use --apply to make changes")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Apply known musical data corrections')
    parser.add_argument('--apply', action='store_true', help='Apply corrections to database')
    args = parser.parse_args()
    
    apply_corrections(dry_run=not args.apply)