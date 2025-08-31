"""Response formatter for PRD format compliance."""

from typing import List, Dict, Any, Optional
from .models import Song, SearchResult
from .database import get_db_session, LyricsRepository


class ResponseFormatter:
    """Formats bot responses according to PRD specifications."""
    
    def format_search_result(self, search_result: SearchResult) -> str:
        """
        DEPRECATED: Use format_individual_songs() instead for new UX.
        Format search result in PRD format as single message.
        """
        if not search_result or not search_result.songs:
            return "No songs found for your search."
        
        formatted_lines = []
        for song in search_result.songs:
            line = self._format_song_line(song, search_result.matched_term)
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def format_individual_songs(self, search_result: SearchResult) -> List[str]:
        """
        Format search result as individual messages for improved UX.
        Returns list of formatted strings, one per song.
        """
        if not search_result or not search_result.songs:
            return ["No songs found for your search."]
        
        individual_messages = []
        for song in search_result.songs:
            message = self._format_song_line(song, search_result.matched_term)
            individual_messages.append(message)
        
        return individual_messages
    
    def _format_song_line(self, song: Song, matched_term: str) -> str:
        """Format a single song line in clean, readable format."""
        # Select 3-5 most relevant tags based on the search term
        relevant_tags = self._select_relevant_tags(song.tags, matched_term)
        tags_str = ', '.join(relevant_tags)
        
        # Get chorus and bridge snippets
        chorus_snippet = self._get_lyrics_snippet(song.title, song.artist, 'chorus')
        bridge_snippet = self._get_lyrics_snippet(song.title, song.artist, 'bridge')
        
        # Build the response
        lines = [
            f"{song.title} - {song.artist}",
            f"Key {song.key} | {song.bpm} BPM",
            f"{tags_str}",
            f"{song.url}"
        ]
        
        # Add lyrics snippets only if available
        if chorus_snippet:
            lines.append(f"Chorus: {chorus_snippet}")
        if bridge_snippet:
            lines.append(f"Bridge: {bridge_snippet}")
            
        return '\n'.join(lines)
    
    def _get_lyrics_snippet(self, title: str, artist: str, section: str) -> Optional[str]:
        """Get first 4-6 words of chorus or bridge for a song."""
        try:
            with get_db_session() as session:
                lyrics_repo = LyricsRepository(session)
                
                # Find the song to get its ID
                from .database import Song as DBSong
                db_song = session.query(DBSong).filter(
                    DBSong.title == title,
                    DBSong.artist == artist
                ).first()
                
                if not db_song:
                    return None
                
                # Get lyrics
                lyrics = lyrics_repo.get_by_song_id(db_song.song_id)
                if not lyrics:
                    return None
                
                # Extract the requested section (chorus or bridge)
                if section == 'chorus':
                    section_text = lyrics.chorus
                elif section == 'bridge':
                    section_text = lyrics.bridge
                else:
                    return None
                
                if not section_text:
                    return None
                
                # Get first 4-6 words
                words = section_text.split()[:6]
                return ' '.join(words)
                
        except Exception:
            return None
    
    def _select_relevant_tags(self, tags: List[str], search_term: str) -> List[str]:
        """Select 3-5 most relevant tags based on search query."""
        if not tags:
            return []
        
        # Convert search term to lowercase for matching
        search_lower = search_term.lower() if search_term else ""
        
        # Priority system for tag selection
        exact_matches = []
        partial_matches = []
        semantic_matches = []
        other_tags = []
        
        # Define semantic relationships for common worship terms
        semantic_groups = {
            'joy': ['celebration', 'rejoice', 'gladness', 'happiness'],
            'worship': ['praise', 'adoration', 'exaltation', 'glory'],
            'love': ['devotion', 'heart', 'affection', 'beloved'],
            'faith': ['trust', 'belief', 'confidence', 'assurance'],
            'holy': ['sacred', 'pure', 'sanctified', 'consecrated'],
            'spirit': ['presence', 'power', 'wind', 'fire'],
            'jesus': ['christ', 'savior', 'lord', 'messiah'],
            'peace': ['rest', 'calm', 'quiet', 'stillness'],
            'hope': ['expectation', 'future', 'promise', 'anchor'],
            'freedom': ['liberation', 'release', 'deliverance', 'breakthrough']
        }
        
        for tag in tags:
            tag_lower = tag.lower()
            
            # Exact match with search term
            if search_lower in tag_lower or tag_lower in search_lower:
                exact_matches.append(tag)
            # Partial word match
            elif any(word in tag_lower for word in search_lower.split()):
                partial_matches.append(tag)
            # Semantic match - check if search term maps to this tag
            elif search_lower in semantic_groups and tag_lower in semantic_groups[search_lower]:
                semantic_matches.append(tag)
            # Reverse semantic match - check if tag maps to search term
            elif any(search_lower in group and tag_lower == key for key, group in semantic_groups.items()):
                semantic_matches.append(tag)
            else:
                other_tags.append(tag)
        
        # Build final tag list (3-5 tags)
        selected = []
        
        # Add exact matches first (up to 2)
        selected.extend(exact_matches[:2])
        
        # Add partial matches (up to 2 more)
        remaining = 5 - len(selected)
        selected.extend(partial_matches[:min(2, remaining)])
        
        # Add semantic matches (up to remaining slots)
        remaining = 5 - len(selected)
        selected.extend(semantic_matches[:remaining])
        
        # Fill with other high-quality tags if still under 3
        while len(selected) < 3 and other_tags:
            # Prefer common worship tags
            priority_tags = ['worship', 'praise', 'faith', 'love', 'holy spirit', 'jesus', 'god', 'lord']
            priority_found = [tag for tag in other_tags if any(priority in tag.lower() for priority in priority_tags)]
            
            if priority_found:
                selected.append(priority_found[0])
                other_tags.remove(priority_found[0])
            else:
                selected.append(other_tags[0])
                other_tags.pop(0)
        
        # Ensure we have at least 3 tags if available, max 5
        final_count = min(max(len(selected), 3), 5)
        return selected[:final_count] if selected else tags[:3]
    
    def format_no_previous_search_message(self) -> str:
        """Format message when user requests 'more' without previous search."""
        return "Please search first before requesting more songs."
    
    def format_session_expired_message(self) -> str:
        """Format message when user session has expired."""
        return "Your search session has expired. Please search first before requesting more songs."
    
    def format_feedback_confirmation(self, song_position: int, feedback_type: str = "thumbs_up", song_title: str = None) -> str:
        """Format confirmation message for feedback."""
        if feedback_type == "thumbs_up":
            if song_title:
                return f"✅ Great! I've noted that '{song_title}' worked well for this situation."
            else:
                return f"✅ Thanks! I've noted song {song_position} as a good choice."
        elif feedback_type == "thumbs_down":
            if song_title:
                return f"📝 Got it. I'll remember that '{song_title}' wasn't quite right for this context."
            else:
                return f"📝 Thanks for the feedback on song {song_position}. I'll adjust future recommendations."
        else:
            return f"Thanks for the feedback on song {song_position}!"
    
    def format_invalid_feedback_message(self) -> str:
        """Format message for invalid feedback format."""
        return "Try: 👍 1 for first song, 👍 2 for second song, 👍 3 for third song, etc."
    
    def format_no_feedback_context_message(self) -> str:
        """Format message when feedback provided without search context.""" 
        return "Please search first before providing feedback."