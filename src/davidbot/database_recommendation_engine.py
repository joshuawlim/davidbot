"""Database-powered recommendation engine replacing hardcoded songs."""

import logging
from typing import List, Optional, Dict
from .models import Song as BotSong, SearchResult  # Existing bot models
from .database import get_db_session, Song, Lyrics, SongRepository, SongUsageRepository, ThemeMappingRepository, LyricsRepository

logger = logging.getLogger(__name__)


class DatabaseRecommendationEngine:
    """Engine for finding song recommendations from SQLite database."""
    
    def __init__(self):
        """Initialize database-powered recommendation engine."""
        self._song_cache: Dict[int, BotSong] = {}
        logger.info("Database recommendation engine initialized")
    
    def _convert_db_song_to_bot_song(self, db_song: Song, lyrics: Optional[Lyrics] = None) -> BotSong:
        """Convert database Song model to bot Song model."""
        # Check cache first
        if db_song.song_id in self._song_cache:
            return self._song_cache[db_song.song_id]
        
        # Get themes for search terms
        with get_db_session() as session:
            theme_repo = ThemeMappingRepository(session)
            themes = theme_repo.get_themes_for_song(db_song.song_id)
            search_terms = [theme.theme_name for theme in themes]
        
        # Convert to bot model format
        bot_song = BotSong(
            title=db_song.title,
            artist=db_song.artist,
            key=db_song.original_key,
            bpm=db_song.bpm or 80,  # Default BPM if None
            tags=db_song.tags_list,
            url=db_song.resource_link or "",
            search_terms=search_terms
        )
        
        # Cache for future use
        self._song_cache[db_song.song_id] = bot_song
        return bot_song
    
    def search(self, query: str, excluded_songs: Optional[List[str]] = None) -> Optional[SearchResult]:
        """Search for songs matching the query using database."""
        if excluded_songs is None:
            excluded_songs = []
        
        logger.info(f"Searching database for: '{query}' (excluding: {excluded_songs})")
        
        try:
            with get_db_session() as session:
                song_repo = SongRepository(session)
                theme_repo = ThemeMappingRepository(session)
                lyrics_repo = LyricsRepository(session)
                
                # Extract search terms from query
                query_lower = query.lower()
                potential_themes = self._extract_themes_from_query(query_lower)
                
                # Search by themes first (most accurate)
                matching_songs = []
                matched_theme = None
                
                for theme in potential_themes:
                    theme_songs = song_repo.search_by_theme(theme, limit=10)
                    if theme_songs:
                        matched_theme = theme
                        # Convert to bot models, excluding already returned songs
                        for db_song in theme_songs:
                            if db_song.title not in excluded_songs:
                                bot_song = self._convert_db_song_to_bot_song(db_song)
                                matching_songs.append(bot_song)
                        break
                
                # Fallback to text search if no theme matches found
                if not matching_songs:
                    logger.info(f"No theme matches found, trying text search for: {query}")
                    text_songs = song_repo.search_by_text(query, limit=10)
                    
                    for db_song in text_songs:
                        if db_song.title not in excluded_songs:
                            bot_song = self._convert_db_song_to_bot_song(db_song)
                            matching_songs.append(bot_song)
                    
                    matched_theme = "text_match"
                
                # Additional fallback: search lyrics content
                if not matching_songs:
                    logger.info(f"No text matches found, trying lyrics search for: {query}")
                    lyrics_matches = lyrics_repo.search_lyrics_content(query, limit=5)
                    
                    for lyrics in lyrics_matches:
                        db_song = song_repo.get_by_id(lyrics.song_id)
                        if db_song and db_song.title not in excluded_songs:
                            bot_song = self._convert_db_song_to_bot_song(db_song, lyrics)
                            matching_songs.append(bot_song)
                    
                    matched_theme = "lyrics_match"
                
                if not matching_songs:
                    logger.warning(f"No songs found for query: '{query}'")
                    return None
                
                # Apply familiarity scoring to boost familiar songs
                scored_songs = self._apply_familiarity_scoring(matching_songs)
                
                # Return up to 3 songs (matching original behavior)
                selected_songs = scored_songs[:3]
                
                logger.info(f"Found {len(selected_songs)} songs for theme '{matched_theme}'")
                
                return SearchResult(
                    songs=selected_songs,
                    matched_term=matched_theme or query,
                    theme=matched_theme or query
                )
                
        except Exception as e:
            logger.error(f"Database search failed: {e}")
            # Fallback behavior - return None to let bot handle gracefully
            return None
    
    def _extract_themes_from_query(self, query_lower: str) -> List[str]:
        """Extract potential themes from user query."""
        # Common theme mappings and synonyms
        theme_mappings = {
            'surrender': ['surrender', 'yielding', 'giving up', 'submission'],
            'worship': ['worship', 'praise', 'adoration', 'honor'],
            'grace': ['grace', 'mercy', 'forgiveness', 'undeserved'],
            'love': ['love', 'loving', 'beloved', 'affection'],
            'peace': ['peace', 'calm', 'rest', 'tranquil', 'still'],
            'hope': ['hope', 'hopeful', 'future', 'expectation'],
            'faith': ['faith', 'trust', 'belief', 'confidence'],
            'joy': ['joy', 'joyful', 'happiness', 'celebration'],
            'redemption': ['redemption', 'salvation', 'saved', 'redeemed'],
            'commitment': ['commitment', 'dedication', 'devoted'],
            'consecration': ['consecration', 'holy', 'sacred', 'set apart'],
            'altar-call': ['altar call', 'altar-call', 'invitation', 'response'],
            'blood': ['blood', 'cross', 'sacrifice', 'calvary'],
            'cleansing': ['cleansing', 'clean', 'wash', 'pure', 'purify'],
        }
        
        found_themes = []
        
        # Direct theme matches
        for theme, synonyms in theme_mappings.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    found_themes.append(theme)
                    break
        
        # Extract potential theme words directly from query
        words = query_lower.replace('find songs on', '').replace('find songs about', '').split()
        for word in words:
            word = word.strip(',.')
            if len(word) > 2:  # Ignore very short words
                found_themes.append(word)
        
        return found_themes
    
    def _apply_familiarity_scoring(self, songs: List[BotSong]) -> List[BotSong]:
        """Apply familiarity scoring to boost familiar songs in results."""
        if not songs:
            return songs
            
        try:
            with get_db_session() as session:
                usage_repo = SongUsageRepository(session)
                
                # Calculate familiarity scores for all songs
                songs_with_scores = []
                for song in songs:
                    # Find the database song by title and artist
                    db_song = session.query(Song).filter(
                        Song.title == song.title,
                        Song.artist == song.artist
                    ).first()
                    
                    if db_song:
                        familiarity_score = usage_repo.calculate_familiarity_score(db_song.song_id)
                    else:
                        familiarity_score = 0.0
                    
                    songs_with_scores.append({
                        'song': song,
                        'familiarity_score': familiarity_score,
                        'original_order': len(songs_with_scores)  # Preserve original order for ties
                    })
                
                # Sort by familiarity score (descending), then by original order (ascending) for ties
                songs_with_scores.sort(key=lambda x: (-x['familiarity_score'], x['original_order']))
                
                # Extract sorted songs
                sorted_songs = [item['song'] for item in songs_with_scores]
                
                # Log scoring results
                if songs_with_scores:
                    logger.info(f"Familiarity scoring applied:")
                    for item in songs_with_scores[:3]:  # Log top 3
                        score = item['familiarity_score']
                        song = item['song']
                        logger.info(f"  {song.title} by {song.artist}: score {score}")
                
                return sorted_songs
                
        except Exception as e:
            logger.error(f"Error applying familiarity scoring: {e}")
            return songs  # Return original order on error
    
    def get_all_themes(self) -> List[str]:
        """Get all available themes from database."""
        try:
            with get_db_session() as session:
                theme_repo = ThemeMappingRepository(session)
                return theme_repo.get_all_themes()
        except Exception as e:
            logger.error(f"Failed to get themes from database: {e}")
            return []
    
    def get_songs_by_theme(self, theme: str, limit: int = 10) -> List[BotSong]:
        """Get all songs for a specific theme."""
        try:
            with get_db_session() as session:
                song_repo = SongRepository(session)
                db_songs = song_repo.search_by_theme(theme, limit=limit)
                
                return [self._convert_db_song_to_bot_song(song) for song in db_songs]
        except Exception as e:
            logger.error(f"Failed to get songs for theme '{theme}': {e}")
            return []
    
    def get_song_count(self) -> int:
        """Get total number of active songs in database."""
        try:
            with get_db_session() as session:
                song_repo = SongRepository(session)
                songs = song_repo.get_all_active()
                return len(songs)
        except Exception as e:
            logger.error(f"Failed to get song count: {e}")
            return 0
    
    def health_check(self) -> Dict[str, any]:
        """Check database health and return status."""
        try:
            song_count = self.get_song_count()
            themes = self.get_all_themes()
            
            return {
                "status": "healthy" if song_count > 0 else "warning",
                "song_count": song_count,
                "theme_count": len(themes),
                "themes": themes[:10],  # First 10 themes for preview
                "cache_size": len(self._song_cache)
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "song_count": 0,
                "theme_count": 0
            }


# Backward compatibility - create instance with same interface
def create_recommendation_engine():
    """Factory function to create recommendation engine."""
    try:
        # Try database-powered engine first
        engine = DatabaseRecommendationEngine()
        health = engine.health_check()
        
        if health["status"] == "healthy":
            logger.info(f"Database engine initialized with {health['song_count']} songs")
            return engine
        else:
            logger.warning(f"Database engine health check failed: {health}")
            # Could fallback to hardcoded engine here if needed
            return engine
            
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {e}")
        # Import and return original hardcoded engine as fallback
        from .recommendation_engine import RecommendationEngine
        logger.info("Falling back to hardcoded recommendation engine")
        return RecommendationEngine()