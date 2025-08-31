#!/usr/bin/env python3
"""Apply verification results from CSV to update database."""

import sys
import os
import csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from davidbot.database.database import get_db_session
from sqlalchemy import text

def read_verification_csv(filename):
    """Read verification results from CSV file."""
    corrections = []
    
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Only process rows that have verification data
                if row['verified_key'] and row['verified_bpm']:
                    try:
                        correction = {
                            'song_id': int(row['song_id']),
                            'title': row['title'],
                            'artist': row['artist'],
                            'current_key': row['current_key'],
                            'current_bpm': int(row['current_bpm']) if row['current_bpm'] != 'None' else None,
                            'verified_key': row['verified_key'],
                            'verified_bpm': int(row['verified_bpm']),
                            'source': row['source'],
                            'matches_db': row['matches_db'].upper() in ['TRUE', 'YES', '1'],
                            'notes': row['notes']
                        }
                        corrections.append(correction)
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  Skipping invalid row for {row['title']}: {e}")
    
    except FileNotFoundError:
        print(f"❌ CSV file not found: {filename}")
        print(f"   Run: python3 verify_all_songs.py --csv")
        return []
    
    return corrections

def analyze_verification_results(corrections):
    """Analyze verification results and show summary."""
    if not corrections:
        print("📊 No verification data found in CSV")
        return
    
    print(f"📊 VERIFICATION RESULTS ANALYSIS")
    print("=" * 50)
    print(f"Songs with verification data: {len(corrections)}")
    
    # Count matches vs errors
    matches = sum(1 for c in corrections if c['matches_db'])
    errors = len(corrections) - matches
    
    print(f"✅ Correct in database: {matches}")
    print(f"❌ Errors found: {errors}")
    
    if errors > 0:
        print(f"\n🚨 ERRORS DETECTED:")
        for correction in corrections:
            if not correction['matches_db']:
                print(f"   • {correction['title']} - {correction['artist']}")
                
                key_error = correction['current_key'] != correction['verified_key']
                bpm_error = correction['current_bpm'] != correction['verified_bpm']
                
                if key_error:
                    print(f"     Key: {correction['current_key']} → {correction['verified_key']}")
                if bpm_error:
                    print(f"     BPM: {correction['current_bpm']} → {correction['verified_bpm']}")
                if correction['notes']:
                    print(f"     Notes: {correction['notes']}")
    
    print(f"\n📈 Verification Coverage:")
    print(f"   Verified: {len(corrections)} / 69 songs ({len(corrections)/69*100:.1f}%)")
    print(f"   Remaining: {69 - len(corrections)} songs")

def apply_corrections(corrections, dry_run=True):
    """Apply corrections to database."""
    errors_to_fix = [c for c in corrections if not c['matches_db']]
    
    if not errors_to_fix:
        print("✅ No corrections needed - all verified data matches database!")
        return
    
    if dry_run:
        print(f"\n🔍 DRY RUN - Would correct {len(errors_to_fix)} songs")
        return
    
    print(f"\n💾 Applying {len(errors_to_fix)} corrections to database...")
    
    try:
        with get_db_session() as session:
            for correction in errors_to_fix:
                updates = []
                params = {'song_id': correction['song_id']}
                
                # Check what needs updating
                if correction['current_key'] != correction['verified_key']:
                    updates.append("original_key = :new_key")
                    params['new_key'] = correction['verified_key']
                
                if correction['current_bpm'] != correction['verified_bpm']:
                    updates.append("bpm = :new_bpm")
                    params['new_bpm'] = correction['verified_bpm']
                
                if updates:
                    # Add verification tracking
                    updates.append("updated_at = datetime('now')")
                    
                    update_sql = f"UPDATE songs SET {', '.join(updates)} WHERE song_id = :song_id"
                    session.execute(text(update_sql), params)
                    
                    print(f"   ✅ Updated: {correction['title']}")
                    if correction['current_key'] != correction['verified_key']:
                        print(f"      Key: {correction['current_key']} → {correction['verified_key']}")
                    if correction['current_bpm'] != correction['verified_bpm']:
                        print(f"      BPM: {correction['current_bpm']} → {correction['verified_bpm']}")
            
            session.commit()
            print(f"\n✅ All {len(errors_to_fix)} corrections applied successfully!")
            
    except Exception as e:
        print(f"❌ Error applying corrections: {e}")

def generate_verification_report(corrections):
    """Generate a detailed verification report."""
    report_filename = "verification_report.md"
    
    with open(report_filename, 'w') as f:
        f.write("# DavidBot Song Verification Report\\n\\n")
        f.write(f"**Date**: {__import__('datetime').date.today()}\\n")
        f.write(f"**Songs Verified**: {len(corrections)} / 69\\n\\n")
        
        # Summary
        matches = sum(1 for c in corrections if c['matches_db'])
        errors = len(corrections) - matches
        
        f.write("## Summary\\n\\n")
        f.write(f"- ✅ **Correct**: {matches} songs\\n")
        f.write(f"- ❌ **Errors**: {errors} songs\\n")
        f.write(f"- 📊 **Coverage**: {len(corrections)/69*100:.1f}%\\n\\n")
        
        if errors > 0:
            f.write("## Errors Found\\n\\n")
            for correction in corrections:
                if not correction['matches_db']:
                    f.write(f"### {correction['title']} - {correction['artist']}\\n")
                    f.write(f"**Song ID**: {correction['song_id']}\\n\\n")
                    
                    if correction['current_key'] != correction['verified_key']:
                        f.write(f"- **Key Error**: {correction['current_key']} → {correction['verified_key']}\\n")
                    if correction['current_bpm'] != correction['verified_bpm']:
                        f.write(f"- **BPM Error**: {correction['current_bpm']} → {correction['verified_bpm']}\\n")
                    
                    f.write(f"- **Source**: {correction['source']}\\n")
                    if correction['notes']:
                        f.write(f"- **Notes**: {correction['notes']}\\n")
                    f.write("\\n")
        
        f.write("## Verified Correct Songs\\n\\n")
        correct_songs = [c for c in corrections if c['matches_db']]
        for correction in correct_songs:
            f.write(f"- {correction['title']} - {correction['artist']} (Key {correction['verified_key']}, {correction['verified_bpm']} BPM)\\n")
    
    print(f"📄 Detailed report saved: {report_filename}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Apply verification results from CSV')
    parser.add_argument('--csv', default='song_verification_template.csv', help='CSV file with verification results')
    parser.add_argument('--apply', action='store_true', help='Apply corrections to database (default: dry run)')
    parser.add_argument('--report', action='store_true', help='Generate verification report')
    args = parser.parse_args()
    
    # Read verification data
    corrections = read_verification_csv(args.csv)
    
    if corrections:
        # Analyze results
        analyze_verification_results(corrections)
        
        # Apply corrections
        apply_corrections(corrections, dry_run=not args.apply)
        
        # Generate report if requested
        if args.report:
            generate_verification_report(corrections)
    else:
        print("\\n📋 To use this script:")
        print("1. Fill out the CSV file with verified data from MultiTracks")
        print("2. Run: python3 apply_verification_results.py")
        print("3. If results look good: python3 apply_verification_results.py --apply")