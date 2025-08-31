"""Unit tests for response formatter."""

import pytest
from src.davidbot.response_formatter import ResponseFormatter
from src.davidbot.models import Song, SearchResult


class TestResponseFormatter:
    """Test the response formatter functionality."""
    
    @pytest.fixture
    def formatter(self):
        """Create response formatter instance."""
        return ResponseFormatter()
    
    @pytest.fixture
    def sample_search_result(self):
        """Create sample search result for testing.""" 
        songs = [
            Song("Amazing Grace", "John Newton", "D", 84, ["grace", "salvation"], 
                 "https://example.com/amazing-grace", ["grace"]),
            Song("How Great Thou Art", "Carl Boberg", "G", 90, ["praise", "majesty"],
                 "https://example.com/how-great", ["worship"])
        ]
        return SearchResult(songs=songs, matched_term="grace", theme="grace")
    
    def test_format_search_result_prd_compliance(self, formatter, sample_search_result):
        """Test that search results are formatted in exact PRD format."""
        formatted = formatter.format_search_result(sample_search_result)
        lines = formatted.split('\n')
        
        assert len(lines) == 2
        
        # Test first song format
        first_line = lines[0]
        assert "Amazing Grace — John Newton" in first_line
        assert "Key D" in first_line  
        assert "84 BPM" in first_line
        assert "tags: grace, salvation" in first_line
        assert "link: https://example.com/amazing-grace" in first_line
        assert "rationale: matched 'grace'" in first_line
    
    def test_format_empty_result(self, formatter):
        """Test formatting when no songs found."""
        empty_result = SearchResult(songs=[], matched_term="unknown", theme="unknown")
        formatted = formatter.format_search_result(empty_result)
        
        assert "No songs found" in formatted
    
    def test_format_feedback_confirmation(self, formatter):
        """Test feedback confirmation message formatting."""
        confirmation = formatter.format_feedback_confirmation(2)
        assert "Thanks for the feedback on song 2!" == confirmation
    
    def test_format_invalid_feedback_message(self, formatter):
        """Test invalid feedback message contains guidance."""
        message = formatter.format_invalid_feedback_message()
        assert "👍 1" in message
        assert "👍 2" in message  
        assert "👍 3" in message