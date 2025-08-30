"""Acceptance tests for song search functionality.

Tests Acceptance Criteria 1: 
User sends "find songs on surrender" → bot returns 3 songs in PRD format
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.davidbot.bot_handler import BotHandler
from src.davidbot.models import Song, SearchResult


class TestSongSearchAcceptance:
    """Test the core song search acceptance criteria."""
    
    @pytest.fixture
    def mock_sheets_client(self):
        """Mock sheets client that doesn't fail."""
        mock_client = AsyncMock()
        mock_client.log_message.return_value = True
        return mock_client
    
    @pytest.fixture 
    def bot_handler(self, mock_sheets_client):
        """Create bot handler with mocked dependencies."""
        return BotHandler(sheets_client=mock_sheets_client)
    
    @pytest.mark.asyncio
    async def test_find_songs_on_surrender_returns_three_songs_in_prd_format(self, bot_handler):
        """
        ACCEPTANCE CRITERIA 1:
        User sends "find songs on surrender" → bot returns 3 songs in PRD format:
        "Title — Artist | Key G | 72 BPM | tags: altar-call | link: [URL] | matched: 'surrender'"
        """
        # Given: User sends search query
        user_id = "test_user_123"
        query = "find songs on surrender"
        
        # When: Bot processes the search
        response = await bot_handler.handle_message(user_id, query)
        
        # Then: Response contains exactly 3 songs in PRD format
        lines = response.strip().split('\n')
        assert len(lines) == 3, f"Expected 3 songs, got {len(lines)}"
        
        for line in lines:
            # Verify PRD format: "Title — Artist | Key X | ## BPM | tags: tag | link: [URL] | matched: 'term'"
            assert " — " in line, f"Missing title-artist separator in: {line}"
            assert " | Key " in line, f"Missing key info in: {line}"
            assert " BPM | " in line, f"Missing BPM info in: {line}"
            assert "tags: " in line, f"Missing tags in: {line}"
            assert "link: " in line, f"Missing link in: {line}"
            assert "matched: 'surrender'" in line, f"Missing matched term in: {line}"
    
    @pytest.mark.asyncio  
    async def test_search_returns_different_songs_for_different_themes(self, bot_handler):
        """Verify different search terms return different themed songs."""
        user_id = "test_user_456"
        
        # Test surrender theme
        surrender_response = await bot_handler.handle_message(user_id, "find songs on surrender")
        surrender_lines = surrender_response.strip().split('\n')
        
        # Test worship theme  
        worship_response = await bot_handler.handle_message(user_id, "find songs on worship")
        worship_lines = worship_response.strip().split('\n')
        
        # Should return different songs
        assert surrender_lines != worship_lines
        assert len(surrender_lines) == 3
        assert len(worship_lines) == 3
        
        # Check matched terms are different
        assert "matched: 'surrender'" in surrender_response
        assert "matched: 'worship'" in worship_response
    
    @pytest.mark.asyncio
    async def test_search_with_partial_match_works(self, bot_handler):
        """Test that partial word matches work correctly."""
        user_id = "test_user_789"
        
        # Test with partial match
        response = await bot_handler.handle_message(user_id, "find songs with grace")
        lines = response.strip().split('\n')
        
        assert len(lines) == 3
        # Should match on the term 'grace'
        for line in lines:
            assert "matched: 'grace'" in line
    
    @pytest.mark.asyncio
    async def test_unknown_theme_returns_appropriate_response(self, bot_handler):
        """Test handling of search terms with no matches."""
        user_id = "test_user_000"
        
        response = await bot_handler.handle_message(user_id, "find songs about quantum physics")
        
        # Should return a helpful message, not crash
        assert "No songs found" in response or "Sorry" in response
        assert response != ""