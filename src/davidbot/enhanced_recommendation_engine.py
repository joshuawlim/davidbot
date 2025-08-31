"""Enhanced recommendation engine with LLM query support."""

import logging
from typing import List, Optional, Dict, Any
from .models import SearchResult
from .llm_query_parser import ParsedQuery
from .database_recommendation_engine import DatabaseRecommendationEngine

logger = logging.getLogger(__name__)


class EnhancedRecommendationEngine:
    """Enhanced recommendation engine with natural language support."""
    
    def __init__(self, database_engine: DatabaseRecommendationEngine):
        """Initialize enhanced engine with database backend."""
        self.db_engine = database_engine
    
    def search_with_parsed_query(self, parsed_query: ParsedQuery, excluded_songs: Optional[List[str]] = None) -> Optional[SearchResult]:
        """Search using a parsed query structure."""
        if excluded_songs is None:
            excluded_songs = []
        
        logger.info(f"Enhanced search - themes: {parsed_query.themes}, BPM: {parsed_query.bpm_min}-{parsed_query.bpm_max}")
        
        # Handle different query types
        if parsed_query.intent == "more":
            return self._handle_more_request(parsed_query, excluded_songs)
        elif parsed_query.similarity_song:
            return self._handle_similarity_search(parsed_query, excluded_songs)
        else:
            return self._handle_theme_search(parsed_query, excluded_songs)
    
    def _handle_theme_search(self, parsed_query: ParsedQuery, excluded_songs: List[str]) -> Optional[SearchResult]:
        """Handle theme-based search with BPM and other filters."""
        from .database import get_db_session, Song
        from .database.repositories import SongRepository, ThemeMappingRepository
        from sqlalchemy import and_, or_
        
        try:
            with get_db_session() as session:
                song_repo = SongRepository(session)
                theme_repo = ThemeMappingRepository(session)
                
                # Start with theme-based filtering
                matching_songs = []
                for theme in parsed_query.themes:
                    theme_songs = song_repo.search_by_theme(theme, limit=20)
                    matching_songs.extend(theme_songs)
                
                # If no theme matches, fall back to text search
                if not matching_songs:
                    for theme in parsed_query.themes:
                        text_songs = song_repo.search_by_text(theme, limit=10)
                        matching_songs.extend(text_songs)
                
                # Apply BPM filtering
                if parsed_query.bpm_min or parsed_query.bpm_max:
                    matching_songs = self._filter_by_bpm(matching_songs, parsed_query.bpm_min, parsed_query.bpm_max)
                
                # Apply key preference filtering
                if parsed_query.key_preference:
                    matching_songs = self._filter_by_key(matching_songs, parsed_query.key_preference)
                
                # Exclude songs if requested
                if excluded_songs:
                    matching_songs = [song for song in matching_songs if song.title not in excluded_songs]
                
                # Remove duplicates while preserving order
                seen_titles = set()
                unique_songs = []
                for song in matching_songs:
                    if song.title not in seen_titles:
                        unique_songs.append(song)
                        seen_titles.add(song.title)
                
                if not unique_songs:
                    return None
                
                # Convert to bot models and apply familiarity scoring
                bot_songs = [self.db_engine._convert_db_song_to_bot_song(song) for song in unique_songs[:10]]
                scored_songs = self.db_engine._apply_familiarity_scoring(bot_songs)
                
                # Return top 5 results
                final_songs = scored_songs[:5]
                
                matched_themes = ", ".join(parsed_query.themes)
                return SearchResult(
                    songs=final_songs,
                    matched_term=matched_themes,
                    theme=matched_themes
                )
                
        except Exception as e:
            logger.error(f"Enhanced theme search failed: {e}")
            # Fallback to original database engine
            fallback_query = f"find songs on {' '.join(parsed_query.themes)}"
            return self.db_engine.search(fallback_query, excluded_songs)
    
    def _handle_similarity_search(self, parsed_query: ParsedQuery, excluded_songs: List[str]) -> Optional[SearchResult]:
        """Handle similarity-based search for 'songs like X'."""
        from .database import get_db_session, Song
        from .database.repositories import SongRepository, ThemeMappingRepository
        
        try:
            with get_db_session() as session:
                song_repo = SongRepository(session)
                theme_repo = ThemeMappingRepository(session)
                
                # Find the reference song
                reference_song = song_repo.search_by_text(parsed_query.similarity_song, limit=1)
                if not reference_song:
                    logger.warning(f"Reference song not found: {parsed_query.similarity_song}")
                    # Fall back to theme search
                    return self._handle_theme_search(parsed_query, excluded_songs)
                
                ref_song = reference_song[0]
                
                # Get themes from reference song
                ref_themes = theme_repo.get_themes_for_song(ref_song.song_id)
                theme_names = [theme.theme_name for theme in ref_themes]
                
                # Find similar songs based on themes and BPM
                similar_songs = []
                for theme in theme_names[:5]:  # Use top 5 themes
                    theme_songs = song_repo.search_by_theme(theme, limit=10)
                    similar_songs.extend(theme_songs)
                
                # Filter by BPM similarity (±20 BPM from reference)
                if ref_song.bpm:
                    bpm_min = max(60, ref_song.bpm - 20)
                    bpm_max = min(180, ref_song.bpm + 20)
                    similar_songs = self._filter_by_bpm(similar_songs, bpm_min, bpm_max)
                
                # Exclude reference song and excluded songs
                excluded_set = set(excluded_songs + [ref_song.title])
                similar_songs = [song for song in similar_songs if song.title not in excluded_set]
                
                # Remove duplicates
                seen_titles = set()
                unique_songs = []
                for song in similar_songs:
                    if song.title not in seen_titles:
                        unique_songs.append(song)
                        seen_titles.add(song.title)
                
                if not unique_songs:
                    return None
                
                # Convert and score
                bot_songs = [self.db_engine._convert_db_song_to_bot_song(song) for song in unique_songs[:10]]
                scored_songs = self.db_engine._apply_familiarity_scoring(bot_songs)
                
                return SearchResult(
                    songs=scored_songs[:5],
                    matched_term=f"similar to {parsed_query.similarity_song}",
                    theme=f"similar to {ref_song.title}"
                )
                
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return None
    
    def _handle_more_request(self, parsed_query: ParsedQuery, excluded_songs: List[str]) -> Optional[SearchResult]:
        """Handle 'more' requests with context."""
        # For now, treat as theme search with excluded songs
        return self._handle_theme_search(parsed_query, excluded_songs)
    
    def _filter_by_bpm(self, songs: List, bpm_min: Optional[int], bpm_max: Optional[int]) -> List:
        """Filter songs by BPM range."""
        if not bpm_min and not bpm_max:
            return songs
        
        filtered = []
        for song in songs:
            if not song.bpm:
                continue
            
            if bpm_min and song.bpm < bpm_min:
                continue
            if bpm_max and song.bpm > bpm_max:
                continue
            
            filtered.append(song)
        
        return filtered
    
    def _filter_by_key(self, songs: List, preferred_key: str) -> List:
        """Filter songs by preferred key."""
        # Simple key matching - could be enhanced with key relationships
        filtered = [song for song in songs if song.original_key == preferred_key]
        
        # If no exact matches, return all songs
        return filtered if filtered else songs
    
    def health_check(self) -> Dict[str, Any]:
        """Delegate health check to database engine."""
        return self.db_engine.health_check()
    
    def get_all_themes(self) -> List[str]:
        """Delegate theme retrieval to database engine."""
        return self.db_engine.get_all_themes()