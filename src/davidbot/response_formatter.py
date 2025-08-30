"""Response formatter for PRD format compliance."""

from typing import List
from .models import Song, SearchResult


class ResponseFormatter:
    """Formats bot responses according to PRD specifications."""
    
    def format_search_result(self, search_result: SearchResult) -> str:
        """
        Format search result in PRD format:
        "Title — Artist | Key G | 72 BPM | tags: altar-call | link: [URL] | matched: 'surrender'"
        """
        if not search_result or not search_result.songs:
            return "No songs found for your search."
        
        formatted_lines = []
        for song in search_result.songs:
            line = self._format_song_line(song, search_result.matched_term)
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_song_line(self, song: Song, matched_term: str) -> str:
        """Format a single song line in PRD format."""
        # Format tags as comma-separated string
        tags_str = ', '.join(song.tags)
        
        # Build the formatted line
        line = (f"{song.title} — {song.artist} | "
                f"Key {song.key} | "
                f"{song.bpm} BPM | "
                f"tags: {tags_str} | "
                f"link: {song.url} | "
                f"matched: '{matched_term}'")
        
        return line
    
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
        return "Please provide feedback in format '👍 1', '👍 2', or '👍 3' for songs 1-3."
    
    def format_no_feedback_context_message(self) -> str:
        """Format message when feedback provided without search context.""" 
        return "Please search first before providing feedback."