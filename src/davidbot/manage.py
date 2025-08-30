#!/usr/bin/env python3
"""Management commands for DavidBot database operations."""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from davidbot.database import (
    init_database, reset_database, backup_database, get_database_info,
    get_db_session, Song, Lyrics, SongUsage, ThemeMapping,
    SongRepository, LyricsRepository, SongUsageRepository, ThemeMappingRepository
)


def init_db_command():
    """Initialize the database tables."""
    print("Initializing database...")
    init_database()
    info = get_database_info()
    print(f"Database initialized: {info['url']}")
    print(f"Tables created: {list(info.get('tables', {}).keys())}")


def reset_db_command():
    """Reset the database (WARNING: destroys all data)."""
    response = input("⚠️  This will DELETE ALL DATA. Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    print("Resetting database...")
    reset_database()
    print("Database reset completed.")


def backup_command(backup_path: str):
    """Create a database backup."""
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data/backups/davidbot_backup_{timestamp}.db"
        
    # Ensure backup directory exists
    Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating backup: {backup_path}")
    backup_database(backup_path)
    print("Backup completed.")


def info_command():
    """Show database information."""
    info = get_database_info()
    print(f"Database URL: {info['url']}")
    print(f"Driver: {info['driver']}")
    print(f"Database exists: {info['database_exists']}")
    
    if info.get('tables'):
        print("\nTable counts:")
        for table, count in info['tables'].items():
            print(f"  {table}: {count}")


def import_songs_command(json_file: str):
    """Import songs from JSON file."""
    if not os.path.exists(json_file):
        print(f"Error: File not found: {json_file}")
        return
    
    with open(json_file, 'r') as f:
        songs_data = json.load(f)
    
    if not isinstance(songs_data, list):
        print("Error: JSON file must contain an array of songs")
        return
    
    print(f"Importing {len(songs_data)} songs...")
    
    with get_db_session() as session:
        song_repo = SongRepository(session)
        lyrics_repo = LyricsRepository(session)
        theme_repo = ThemeMappingRepository(session)
        
        imported = 0
        for song_data in songs_data:
            try:
                # Check if song already exists
                existing = song_repo.get_by_title_and_artist(
                    song_data.get('title', ''),
                    song_data.get('artist', '')
                )
                
                if existing:
                    print(f"Skipping existing song: {song_data.get('title')} - {song_data.get('artist')}")
                    continue
                
                # Create song
                song = song_repo.create({
                    'title': song_data.get('title', ''),
                    'artist': song_data.get('artist', ''),
                    'original_key': song_data.get('key', 'C'),
                    'bpm': song_data.get('bpm'),
                    'tags': json.dumps(song_data.get('tags', [])),
                    'resource_link': song_data.get('url', ''),
                    'boy_keys': json.dumps(song_data.get('boy_keys', [])),
                    'girl_keys': json.dumps(song_data.get('girl_keys', [])),
                })
                
                # Create lyrics if provided
                if song_data.get('lyrics'):
                    lyrics_repo.create({
                        'song_id': song.song_id,
                        'full_lyrics': song_data['lyrics'],
                        'language': song_data.get('language', 'en')
                    })
                
                # Create theme mappings
                for tag in song_data.get('tags', []):
                    theme_repo.create({
                        'song_id': song.song_id,
                        'theme_name': tag,
                        'confidence_score': 1.0,
                        'source': 'import'
                    })
                
                imported += 1
                print(f"✓ {song_data.get('title')} - {song_data.get('artist')}")
                
            except Exception as e:
                print(f"✗ Failed to import {song_data.get('title', 'Unknown')}: {e}")
    
    print(f"\nImport completed: {imported} songs imported")


def export_songs_command(json_file: str):
    """Export songs to JSON file."""
    print(f"Exporting songs to: {json_file}")
    
    with get_db_session() as session:
        song_repo = SongRepository(session)
        lyrics_repo = LyricsRepository(session)
        
        songs = song_repo.get_all_active()
        export_data = []
        
        for song in songs:
            lyrics = lyrics_repo.get_by_song_id(song.song_id)
            
            song_data = {
                'title': song.title,
                'artist': song.artist,
                'key': song.original_key,
                'bpm': song.bpm,
                'tags': song.tags_list,
                'url': song.resource_link,
                'boy_keys': song.boy_keys_list,
                'girl_keys': song.girl_keys_list,
                'lyrics': lyrics.full_lyrics if lyrics else None,
            }
            export_data.append(song_data)
    
    # Ensure export directory exists
    Path(json_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(json_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Exported {len(export_data)} songs")


def search_command(query: str, preview: bool = False):
    """Search for songs."""
    print(f"Searching for: '{query}'")
    
    with get_db_session() as session:
        song_repo = SongRepository(session)
        lyrics_repo = LyricsRepository(session)
        
        # Search by theme first
        theme_songs = song_repo.search_by_theme(query, limit=5)
        if theme_songs:
            print(f"\nFound {len(theme_songs)} songs by theme:")
            for song in theme_songs:
                print(f"  • {song.title} - {song.artist} ({song.original_key}, {song.bpm} BPM)")
                if preview:
                    lyrics = lyrics_repo.get_by_song_id(song.song_id)
                    if lyrics:
                        preview_text = lyrics.full_lyrics[:100] + "..." if len(lyrics.full_lyrics) > 100 else lyrics.full_lyrics
                        print(f"    Preview: {preview_text}")
        
        # Search by text
        text_songs = song_repo.search_by_text(query, limit=5)
        if text_songs:
            print(f"\nFound {len(text_songs)} songs by text:")
            for song in text_songs:
                print(f"  • {song.title} - {song.artist} ({song.original_key}, {song.bpm} BPM)")


def add_lyrics_command(title: str, first_line: str = None, chorus: str = None, bridge: str = None):
    """Add lyrics sections to a song."""
    print("Note: add-lyrics command is deprecated. Use 'update-lyrics' command instead for the new structure.")
    print(f"Looking for song: {title}")


def update_lyrics_command(title: str, first_line: str = None, chorus: str = None, bridge: str = None):
    """Update lyrics sections (first_line, chorus, bridge) for a song."""
    with get_db_session() as session:
        song_repo = SongRepository(session)
        lyrics_repo = LyricsRepository(session)
        
        # Find song by title (case-insensitive)
        songs = session.query(Song).filter(Song.title.ilike(f"%{title}%")).all()
        
        if not songs:
            print(f"No songs found matching: {title}")
            return
        
        if len(songs) > 1:
            print(f"Multiple songs found. Please be more specific:")
            for song in songs:
                print(f"  • {song.title} - {song.artist}")
            return
        
        song = songs[0]
        print(f"Updating lyrics for: {song.title} by {song.artist}")
        
        # Check if lyrics already exist
        existing_lyrics = lyrics_repo.get_by_song_id(song.song_id)
        
        updates = {}
        if first_line is not None:
            updates['first_line'] = first_line
            print(f"  First line: {first_line}")
        if chorus is not None:
            updates['chorus'] = chorus
            print(f"  Chorus: {chorus}")
        if bridge is not None:
            updates['bridge'] = bridge
            print(f"  Bridge: {bridge}")
        
        if not updates:
            print("No lyrics sections provided. Use --first-line, --chorus, or --bridge")
            return
        
        if existing_lyrics:
            lyrics_repo.update(song.song_id, updates)
            print(f"Updated lyrics sections for: {song.title}")
        else:
            updates['song_id'] = song.song_id
            updates['language'] = 'en'
            lyrics_repo.create(updates)
            print(f"Created lyrics record for: {song.title}")


def list_themes_command():
    """List all themes in the database."""
    with get_db_session() as session:
        theme_repo = ThemeMappingRepository(session)
        themes = theme_repo.get_all_themes()
        
        print(f"Found {len(themes)} themes:")
        for theme in sorted(themes):
            songs = theme_repo.get_songs_for_theme(theme, limit=100)
            print(f"  • {theme} ({len(songs)} songs)")


def record_usage_command(title: str, service_type: str = 'worship', notes: str = None):
    """Record that a song was used in service."""
    with get_db_session() as session:
        song_repo = SongRepository(session)
        usage_repo = SongUsageRepository(session)
        
        # Find song by title (case-insensitive)
        songs = session.query(Song).filter(Song.title.ilike(f"%{title}%")).all()
        
        if not songs:
            print(f"No songs found matching: {title}")
            return
        
        if len(songs) > 1:
            print(f"Multiple songs found. Please be more specific:")
            for song in songs:
                print(f"  • {song.title} - {song.artist}")
            return
        
        song = songs[0]
        
        # Record usage
        usage = usage_repo.record_usage(
            song_id=song.song_id,
            service_type=service_type,
            notes=notes
        )
        
        session.commit()
        print(f"✅ Recorded usage: {song.title} by {song.artist} ({service_type})")
        
        # Show updated familiarity score
        score = usage_repo.calculate_familiarity_score(song.song_id)
        print(f"   Familiarity score: {score}/10.0")


def familiarity_command(title: str = None):
    """Show familiarity scores for songs."""
    with get_db_session() as session:
        usage_repo = SongUsageRepository(session)
        
        if title:
            # Show specific song
            songs = session.query(Song).filter(Song.title.ilike(f"%{title}%")).all()
            
            if not songs:
                print(f"No songs found matching: {title}")
                return
            
            for song in songs:
                score = usage_repo.calculate_familiarity_score(song.song_id)
                usage_count = usage_repo.get_usage_count(song.song_id, days=365)
                recent_usage = usage_repo.get_usage_history(song.song_id, limit=5)
                
                print(f"{song.title} by {song.artist}:")
                print(f"  Familiarity Score: {score}/10.0")
                print(f"  Used {usage_count} times in last year")
                
                if recent_usage:
                    print("  Recent usage:")
                    for usage in recent_usage:
                        date_str = usage.used_date.strftime('%Y-%m-%d')
                        print(f"    • {date_str} ({usage.service_type})")
                else:
                    print("  No usage recorded")
                print()
        else:
            # Show top familiar songs
            familiar_songs = usage_repo.get_most_familiar_songs(limit=15)
            
            if not familiar_songs:
                print("No songs have been used yet.")
                return
            
            print("Most Familiar Songs (by usage frequency):")
            print("=" * 50)
            
            for i, item in enumerate(familiar_songs, 1):
                song = item['song']
                score = item['familiarity_score']
                usage_count = usage_repo.get_usage_count(song.song_id, days=365)
                
                print(f"{i:2d}. {song.title} - {song.artist}")
                print(f"    Score: {score}/10.0 ({usage_count} uses this year)")


def usage_stats_command():
    """Show usage statistics."""
    with get_db_session() as session:
        usage_repo = SongUsageRepository(session)
        
        # Recent usage (last 90 days)
        recent_usage = usage_repo.get_recent_usage(days=90)
        
        print(f"Usage Statistics (Last 90 days)")
        print("=" * 40)
        print(f"Total song uses: {len(recent_usage)}")
        
        if recent_usage:
            # Group by service type
            service_types = {}
            for usage in recent_usage:
                service_type = usage.service_type
                if service_type not in service_types:
                    service_types[service_type] = 0
                service_types[service_type] += 1
            
            print("\nBy service type:")
            for service_type, count in sorted(service_types.items()):
                print(f"  • {service_type}: {count} uses")
            
            # Most used songs
            song_counts = {}
            for usage in recent_usage:
                song_id = usage.song_id
                if song_id not in song_counts:
                    song_counts[song_id] = []
                song_counts[song_id].append(usage)
            
            if song_counts:
                print(f"\nTop songs (last 90 days):")
                
                # Sort by usage count
                sorted_songs = sorted(song_counts.items(), key=lambda x: len(x[1]), reverse=True)
                
                for i, (song_id, usages) in enumerate(sorted_songs[:10], 1):
                    song = session.query(Song).filter(Song.song_id == song_id).first()
                    if song:
                        print(f"  {i:2d}. {song.title} - {song.artist} ({len(usages)} times)")


def set_baseline_familiarity_command():
    """Set baseline familiarity for popular worship songs."""
    with get_db_session() as session:
        usage_repo = SongUsageRepository(session)
        
        print("Setting baseline familiarity scores for popular worship songs...")
        print("This will create historical usage records to establish familiarity.\n")
        
        usage_repo.set_popular_songs_baseline()


def set_song_baseline_command(title: str, score: float):
    """Set baseline familiarity for a specific song."""
    with get_db_session() as session:
        usage_repo = SongUsageRepository(session)
        
        # Find song by title
        songs = session.query(Song).filter(Song.title.ilike(f"%{title}%")).all()
        
        if not songs:
            print(f"No songs found matching: {title}")
            return
        
        if len(songs) > 1:
            print(f"Multiple songs found. Please be more specific:")
            for song in songs:
                print(f"  • {song.title} - {song.artist}")
            return
        
        song = songs[0]
        
        try:
            usage_repo.set_baseline_familiarity(song.song_id, score)
            session.commit()
            
            actual_score = usage_repo.calculate_familiarity_score(song.song_id)
            print(f"✅ Set baseline familiarity for: {song.title} by {song.artist}")
            print(f"   Target score: {score}/10.0, Actual score: {actual_score}/10.0")
            
        except ValueError as e:
            print(f"❌ Error: {e}")


def main():
    """Main entry point for management commands."""
    parser = argparse.ArgumentParser(description="DavidBot database management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Database commands
    subparsers.add_parser('init', help='Initialize database tables')
    subparsers.add_parser('reset', help='Reset database (WARNING: destroys data)')
    subparsers.add_parser('info', help='Show database information')
    
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('path', nargs='?', help='Backup file path (optional)')
    
    # Import/Export commands
    import_parser = subparsers.add_parser('import', help='Import songs from JSON')
    import_parser.add_argument('file', help='JSON file to import')
    
    export_parser = subparsers.add_parser('export', help='Export songs to JSON')
    export_parser.add_argument('file', help='JSON file to export to')
    
    # Search commands
    search_parser = subparsers.add_parser('search', help='Search for songs')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--preview', action='store_true', help='Show lyrics preview')
    
    # Lyrics commands
    lyrics_parser = subparsers.add_parser('add-lyrics', help='Add lyrics to a song (deprecated)')
    lyrics_parser.add_argument('title', help='Song title (partial match)')
    lyrics_parser.add_argument('lyrics', help='Lyrics text')
    
    update_lyrics_parser = subparsers.add_parser('update-lyrics', help='Update lyrics sections for a song')
    update_lyrics_parser.add_argument('title', help='Song title (partial match)')
    update_lyrics_parser.add_argument('--first-line', help='First line of the song')
    update_lyrics_parser.add_argument('--chorus', help='Main chorus section')
    update_lyrics_parser.add_argument('--bridge', help='Bridge section')
    
    # Theme commands
    subparsers.add_parser('themes', help='List all themes')
    
    # Usage tracking commands
    usage_parser = subparsers.add_parser('record-usage', help='Record song usage at service')
    usage_parser.add_argument('title', help='Song title (partial match)')
    usage_parser.add_argument('--service-type', default='worship', help='Service type (worship, youth, special)')
    usage_parser.add_argument('--notes', help='Optional notes (altar call, opening, etc.)')
    
    familiarity_parser = subparsers.add_parser('familiarity', help='Show familiarity scores')
    familiarity_parser.add_argument('title', nargs='?', help='Song title to check (optional)')
    
    subparsers.add_parser('usage-stats', help='Show usage statistics')
    
    # Baseline familiarity commands
    subparsers.add_parser('set-baseline', help='Set baseline familiarity for popular songs')
    
    baseline_parser = subparsers.add_parser('set-song-baseline', help='Set baseline familiarity for specific song')
    baseline_parser.add_argument('title', help='Song title (partial match)')
    baseline_parser.add_argument('score', type=float, help='Familiarity score (0.0-10.0)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'init':
            init_db_command()
        elif args.command == 'reset':
            reset_db_command()
        elif args.command == 'info':
            info_command()
        elif args.command == 'backup':
            backup_command(args.path)
        elif args.command == 'import':
            import_songs_command(args.file)
        elif args.command == 'export':
            export_songs_command(args.file)
        elif args.command == 'search':
            search_command(args.query, args.preview)
        elif args.command == 'add-lyrics':
            add_lyrics_command(args.title, args.lyrics)
        elif args.command == 'update-lyrics':
            update_lyrics_command(args.title, 
                                getattr(args, 'first_line', None), 
                                getattr(args, 'chorus', None), 
                                getattr(args, 'bridge', None))
        elif args.command == 'themes':
            list_themes_command()
        elif args.command == 'record-usage':
            record_usage_command(args.title, 
                                getattr(args, 'service_type', 'worship'),
                                getattr(args, 'notes', None))
        elif args.command == 'familiarity':
            familiarity_command(getattr(args, 'title', None))
        elif args.command == 'usage-stats':
            usage_stats_command()
        elif args.command == 'set-baseline':
            set_baseline_familiarity_command()
        elif args.command == 'set-song-baseline':
            set_song_baseline_command(args.title, args.score)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()