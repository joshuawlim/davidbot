#!/usr/bin/env python3
"""CLI tool for enhancing song tags in DavidBot database."""

import sys
import os
import asyncio
import argparse
from typing import List
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from davidbot.tag_enhancer import SongTagEnhancer, TagEnhancementResult

def print_enhancement_summary(results: List[TagEnhancementResult]):
    """Print detailed summary of tag enhancement results."""
    print("\n" + "="*70)
    print("🎵 TAG ENHANCEMENT SUMMARY")
    print("="*70)
    
    total = len(results)
    successful_search = len([r for r in results if r.search_successful])
    high_confidence = len([r for r in results if r.confidence_score > 0.7])
    medium_confidence = len([r for r in results if 0.4 <= r.confidence_score <= 0.7])
    
    print(f"📊 STATISTICS:")
    print(f"  Total songs processed: {total}")
    print(f"  Search successful: {successful_search} ({successful_search/total*100:.1f}%)")
    print(f"  High confidence (>0.7): {high_confidence} ({high_confidence/total*100:.1f}%)")
    print(f"  Medium confidence (0.4-0.7): {medium_confidence} ({medium_confidence/total*100:.1f}%)")
    
    # Show songs with significant improvements
    significant_improvements = [r for r in results if len(r.suggested_tags) > len(r.original_tags) + 1]
    if significant_improvements:
        print(f"\n🏷️  SIGNIFICANT IMPROVEMENTS ({len(significant_improvements)} songs):")
        for result in significant_improvements[:10]:  # Show top 10
            added_tags = set(result.suggested_tags) - set(result.original_tags)
            print(f"  {result.title} - {result.artist}")
            print(f"    Added: {sorted(added_tags)}")
            print(f"    Confidence: {result.confidence_score:.2f}")
    
    # Show high confidence enhancements
    if high_confidence > 0:
        print(f"\n✅ HIGH CONFIDENCE ENHANCEMENTS:")
        high_conf_results = [r for r in results if r.confidence_score > 0.7]
        for result in high_conf_results[:5]:  # Show top 5
            print(f"  {result.title} - {result.artist}")
            print(f"    Before: {result.original_tags}")
            print(f"    After:  {result.suggested_tags}")

async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Enhance DavidBot song tags using web search")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without updating database (default)")
    parser.add_argument("--apply", action="store_true", 
                       help="Apply changes to database")
    parser.add_argument("--song-id", type=int,
                       help="Process only specific song by ID")
    parser.add_argument("--confidence-threshold", type=float, default=0.5,
                       help="Minimum confidence to apply changes (default: 0.5)")
    parser.add_argument("--db-path", type=str, default="data/davidbot.db",
                       help="Path to database file")
    parser.add_argument("--taxonomy", type=str, default="docs/tags.md",
                       help="Path to worship tag taxonomy file")
    
    args = parser.parse_args()
    
    # Determine run mode
    dry_run = not args.apply
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made to database")
        print("Use --apply to actually update the database")
    else:
        print("💾 APPLY MODE - Changes will be written to database")
        print(f"Minimum confidence threshold: {args.confidence_threshold}")
    
    print("\n" + "="*70)
    print("🚀 Starting DavidBot Tag Enhancement")
    print("="*70)
    
    # Initialize enhancer
    enhancer = SongTagEnhancer(db_path=args.db_path, taxonomy_file=args.taxonomy)
    
    try:
        if args.song_id:
            # Process single song
            print(f"Processing single song ID: {args.song_id}")
            songs = enhancer.get_songs_from_db()
            target_song = None
            for song in songs:
                if song['song_id'] == args.song_id:
                    target_song = song
                    break
            
            if not target_song:
                print(f"❌ Song ID {args.song_id} not found")
                return
            
            result = await enhancer.enhance_song(
                target_song['song_id'],
                target_song['title'],
                target_song['artist'],
                target_song['tags']
            )
            results = [result]
        else:
            # Process all songs
            print("Processing all songs...")
            results = await enhancer.enhance_all_songs(dry_run=dry_run)
        
        # Apply updates if not dry run
        if not dry_run:
            updates_applied = 0
            for result in results:
                if result.confidence_score >= args.confidence_threshold:
                    if enhancer.update_song_tags(result.song_id, result.suggested_tags):
                        updates_applied += 1
            
            print(f"\n✅ Applied {updates_applied} updates to database")
        
        # Print summary
        print_enhancement_summary(results)
        
        if dry_run and results:
            print(f"\n💡 To apply these changes, run with --apply")
            print(f"   Example: python scripts/enhance_tags.py --apply --confidence-threshold 0.6")
        
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during tag enhancement: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))