"""Response formatter for PRD format compliance."""

from typing import List, Dict, Any
from .models import Song, SearchResult


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
        """Format a single song line in PRD format."""
        # Format tags as comma-separated string (lowercase for PRD format)
        tags_str = ', '.join(song.tags)
        
        # PRD format: Title — Artist | Suggested Key | BPM | tags: ... | link: ... | rationale: matched 'term'
        return (f"{song.title} — {song.artist} | Key {song.key} | {song.bpm} BPM | "
                f"tags: {tags_str} | link: {song.url} | rationale: matched '{matched_term}'")
    
    def format_no_previous_search_message(self) -> str:
        """Format message when user requests 'more' without previous search."""
        return "Please search first before requesting more songs."
    
    def format_session_expired_message(self) -> str:
        """Format message when user session has expired."""
        return "Your search session has expired. Please search first before requesting more songs."
    
    def format_feedback_confirmation(self, song_position: int) -> str:
        """Format confirmation message for feedback."""
        return f"Thanks for the feedback on song {song_position}!"
    
    def format_invalid_feedback_message(self) -> str:
        """Format message for invalid feedback format."""
        return "Try: 👍 1 for first song, 👍 2 for second song, 👍 3 for third song."
    
    def format_no_feedback_context_message(self) -> str:
        """Format message when feedback provided without search context.""" 
        return "Please search first before providing feedback."