#!/usr/bin/env python3
"""Migration script to restructure Lyrics table from full_lyrics to first_line, chorus, bridge."""

import sys
import os
sys.path.insert(0, 'src')

from davidbot.database import get_db_session, get_engine
from davidbot.database.models import Base
from sqlalchemy import text

def migrate_lyrics_structure():
    """Migrate lyrics table structure."""
    
    print("Starting lyrics table migration...")
    
    engine = get_engine()
    with engine.begin() as conn:
        # Check if new columns already exist
        result = conn.execute(text("PRAGMA table_info(lyrics)"))
        columns = [row[1] for row in result]
        
        if 'first_line' in columns:
            print("Migration already applied - first_line column exists")
            return
        
        print("Current columns:", columns)
        
        # Step 1: Create new table with updated structure
        print("Creating new lyrics table with updated structure...")
        conn.execute(text("""
            CREATE TABLE lyrics_new (
                lyrics_id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INTEGER NOT NULL REFERENCES songs(song_id),
                first_line TEXT,
                chorus TEXT,
                bridge TEXT,
                language VARCHAR DEFAULT 'en',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Step 2: Migrate existing data - clear out old thematic summaries
        print("Clearing existing thematic summaries (will be replaced with actual lyric sections)...")
        conn.execute(text("""
            INSERT INTO lyrics_new (lyrics_id, song_id, first_line, chorus, bridge, language, created_at)
            SELECT lyrics_id, song_id, NULL, NULL, NULL, language, created_at
            FROM lyrics
        """))
        
        # Step 3: Drop old table and rename new one
        print("Replacing old table...")
        conn.execute(text("DROP TABLE lyrics"))
        conn.execute(text("ALTER TABLE lyrics_new RENAME TO lyrics"))
        
        print("Migration completed successfully!")
        print("Note: All lyrics sections are now NULL - populate with actual first_line, chorus, bridge content")

if __name__ == "__main__":
    migrate_lyrics_structure()