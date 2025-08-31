#!/usr/bin/env python3
"""Verify and correct BPM and key data using web search against MultiTracks."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import re
import asyncio
import aiohttp
from urllib.parse import quote
from davidbot.database.database import get_db_session
from sqlalchemy import text

class MusicalDataVerifier:
    """Verify BPM and key data by searching MultiTracks."""
    
    def __init__(self):
        self.base_url = "https://www.multitracks.com"
        self.session = None
        self.corrections = []
        
    async def __aenter__(self):
        # Create connector with SSL verification disabled for corporate networks
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_song_data(self, title, artist):
        """Search MultiTracks for accurate BPM and key data."""
        try:
            # Create search query
            search_query = f"{title} {artist}".strip()
            search_url = f"{self.base_url}/search?q={quote(search_query)}"
            
            print(f"🔍 Searching: {title} - {artist}")
            
            async with self.session.get(search_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    print(f"   ❌ Search failed: HTTP {response.status}")
                    return None
                
                html = await response.text()
                
                # Look for song links in search results
                song_links = re.findall(r'<a[^>]*href="(/songs/[^"]*)"[^>]*>', html)
                
                if not song_links:
                    print(f"   ❌ No song links found")
                    return None
                
                # Try the first few links
                for link in song_links[:3]:
                    song_url = f"{self.base_url}{link}"
                    song_data = await self.extract_song_data(song_url, title)
                    if song_data:
                        return song_data
                
                print(f"   ❌ No matching songs found in results")
                return None
                
        except Exception as e:
            print(f"   ❌ Error searching {title}: {e}")
            return None
    
    async def extract_song_data(self, url, expected_title):
        """Extract BPM and key from MultiTracks song page."""
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                
                # Extract title to verify it's the right song
                title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
                if not title_match:
                    return None
                
                page_title = title_match.group(1).strip()
                
                # Check if titles are similar (allow for variations like "Live", etc.)
                if not self.titles_match(expected_title, page_title):
                    return None
                
                # Extract BPM
                bpm_match = re.search(r'BPM:\s*(\d+)', html)
                bpm = int(bpm_match.group(1)) if bpm_match else None
                
                # Extract Key  
                key_match = re.search(r'Key:\s*([A-G]#?b?)', html)
                key = key_match.group(1) if key_match else None
                
                if bpm or key:
                    print(f"   ✅ Found: {page_title} | Key: {key} | BPM: {bpm}")
                    return {
                        'title': page_title,
                        'key': key,
                        'bpm': bpm,
                        'url': url
                    }
                
                return None
                
        except Exception as e:
            print(f"   ❌ Error extracting data from {url}: {e}")
            return None
    
    def titles_match(self, db_title, web_title):
        """Check if database title matches web title (allowing for variations)."""
        # Normalize titles - remove common variations
        def normalize_title(title):
            title = title.lower().strip()
            # Remove common suffixes/prefixes
            title = re.sub(r'\s*\(live\)|\s*\(feat\..*\)|\s*-\s*live', '', title)
            return title
        
        normalized_db = normalize_title(db_title)
        normalized_web = normalize_title(web_title)
        
        # Check exact match or contains
        return normalized_db == normalized_web or normalized_db in normalized_web or normalized_web in normalized_db
    
    async def verify_all_songs(self, limit=None):
        """Verify BPM and key data for all songs in database."""
        print("🎵 Starting Musical Data Verification 🎵")
        print("=" * 50)
        
        with get_db_session() as db_session:
            query = text("SELECT song_id, title, artist, original_key, bpm FROM songs WHERE is_active = true")
            if limit:
                query = text(f"SELECT song_id, title, artist, original_key, bpm FROM songs WHERE is_active = true LIMIT {limit}")
            
            songs = db_session.execute(query).fetchall()
            
        print(f"Found {len(songs)} songs to verify")
        
        for i, song in enumerate(songs, 1):
            print(f"\n📋 {i}/{len(songs)}: {song.title}")
            
            web_data = await self.search_song_data(song.title, song.artist)
            
            if web_data:
                # Compare data
                bpm_mismatch = web_data['bpm'] and song.bpm != web_data['bpm']
                key_mismatch = web_data['key'] and song.original_key != web_data['key']
                
                if bpm_mismatch or key_mismatch:
                    correction = {
                        'song_id': song.song_id,
                        'title': song.title,
                        'artist': song.artist,
                        'db_key': song.original_key,
                        'web_key': web_data['key'],
                        'db_bpm': song.bpm,
                        'web_bpm': web_data['bpm'],
                        'url': web_data['url']
                    }
                    self.corrections.append(correction)
                    
                    print(f"   ⚠️  MISMATCH DETECTED:")
                    if key_mismatch:
                        print(f"      Key: DB={song.original_key} → Web={web_data['key']}")
                    if bpm_mismatch:
                        print(f"      BPM: DB={song.bpm} → Web={web_data['bpm']}")
                else:
                    print(f"   ✅ Data matches: Key={song.original_key}, BPM={song.bpm}")
            
            # Rate limiting
            await asyncio.sleep(1)
    
    def generate_report(self):
        """Generate a report of all corrections needed."""
        if not self.corrections:
            print("\n🎉 No corrections needed - all data is accurate!")
            return
        
        print(f"\n📊 CORRECTION REPORT")
        print("=" * 50)
        print(f"Found {len(self.corrections)} songs with incorrect data:")
        
        for correction in self.corrections:
            print(f"\n🎵 {correction['title']} - {correction['artist']}")
            print(f"   ID: {correction['song_id']}")
            if correction['db_key'] != correction['web_key']:
                print(f"   Key: {correction['db_key']} → {correction['web_key']}")
            if correction['db_bpm'] != correction['web_bpm']:
                print(f"   BPM: {correction['db_bpm']} → {correction['web_bpm']}")
            print(f"   Source: {correction['url']}")
    
    async def apply_corrections(self, dry_run=True):
        """Apply corrections to database."""
        if not self.corrections:
            return
        
        if dry_run:
            print(f"\n🔍 DRY RUN - Would make {len(self.corrections)} corrections")
            return
        
        print(f"\n💾 Applying {len(self.corrections)} corrections...")
        
        with get_db_session() as db_session:
            for correction in self.corrections:
                updates = []
                params = {'song_id': correction['song_id']}
                
                if correction['web_key']:
                    updates.append("original_key = :new_key")
                    params['new_key'] = correction['web_key']
                
                if correction['web_bpm']:
                    updates.append("bpm = :new_bpm")
                    params['new_bpm'] = correction['web_bpm']
                
                if updates:
                    update_sql = f"UPDATE songs SET {', '.join(updates)} WHERE song_id = :song_id"
                    db_session.execute(text(update_sql), params)
                    print(f"   ✅ Updated: {correction['title']}")
            
            db_session.commit()
        
        print("✅ All corrections applied!")

async def main():
    """Main verification process."""
    import argparse
    parser = argparse.ArgumentParser(description='Verify musical data against MultiTracks')
    parser.add_argument('--limit', type=int, help='Limit number of songs to verify')
    parser.add_argument('--apply', action='store_true', help='Apply corrections to database')
    args = parser.parse_args()
    
    async with MusicalDataVerifier() as verifier:
        await verifier.verify_all_songs(limit=args.limit)
        verifier.generate_report()
        
        if verifier.corrections:
            await verifier.apply_corrections(dry_run=not args.apply)

if __name__ == "__main__":
    asyncio.run(main())