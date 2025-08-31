"""Acceptance tests for 'more' command functionality.

Tests Acceptance Criteria 2:
User sends "more" within 60 minutes → returns 3 different songs from same theme
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.davidbot.bot_handler import BotHandler


class TestMoreCommandAcceptance:
    """Test the 'more' command acceptance criteria."""
    
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
    async def test_more_command_returns_different_songs_same_theme(self, bot_handler):
        """
        ACCEPTANCE CRITERIA 2:
        User sends "more" within 60 minutes → returns 3 different songs from same theme
        """
        user_id = "test_user_more_123"
        
        # Given: User has performed initial search
        initial_response = await bot_handler.handle_message(user_id, "find songs on surrender")
        initial_lines = initial_response.strip().split('\n')
        
        # When: User requests more songs
        more_response = await bot_handler.handle_message(user_id, "more")
        more_lines = more_response.strip().split('\n')
        
        # Then: Returns 3 different songs from same theme
        assert len(more_lines) == 3, f"Expected 3 more songs, got {len(more_lines)}"
        
        # Verify same theme (matched term)
        for line in more_lines:
            assert "matched: 'surrender'" in line, f"Different theme in: {line}"
        
        # Verify different songs (no duplicates)
        assert initial_lines != more_lines, "More command returned same songs"
        
        # Verify PRD format maintained
        for line in more_lines:
            assert " — " in line and " | Key " in line and " BPM | " in line
    
    @pytest.mark.asyncio
    async def test_more_command_without_previous_search_fails_gracefully(self, bot_handler):
        """Test 'more' command when no previous search exists."""
        user_id = "test_user_more_456"
        
        # When: User sends 'more' without prior search
        response = await bot_handler.handle_message(user_id, "more")
        
        # Then: Should return helpful message, not crash
        assert isinstance(response, list)
        response_text = response[0].lower() if response else ""
        assert "previous search" in response_text or "search first" in response_text
        assert response != []
    
    @pytest.mark.asyncio
    async def test_multiple_more_commands_return_different_sets(self, bot_handler):
        """Test that multiple 'more' commands return different song sets."""
        user_id = "test_user_more_789"
        
        # Initial search
        await bot_handler.handle_message(user_id, "find songs on worship")
        
        # First 'more'
        more1_response = await bot_handler.handle_message(user_id, "more")
        more1_lines = more1_response.strip().split('\n')
        
        # Second 'more'
        more2_response = await bot_handler.handle_message(user_id, "more") 
        more2_lines = more2_response.strip().split('\n')
        
        # Should be different sets
        assert more1_lines != more2_lines, "Multiple 'more' commands returned same songs"
        assert len(more1_lines) == 3
        assert len(more2_lines) == 3
        
        # Both should match same theme
        for line in more1_lines + more2_lines:
            assert "matched: 'worship'" in line
    
    @pytest.mark.asyncio
    async def test_more_command_respects_session_context(self, bot_handler):
        """Test that 'more' uses context from the user's session, not other users."""
        user1_id = "test_user1"
        user2_id = "test_user2"
        
        # User1 searches for surrender
        await bot_handler.handle_message(user1_id, "find songs on surrender")
        
        # User2 searches for worship  
        await bot_handler.handle_message(user2_id, "find songs on worship")
        
        # User1 says more - should get surrender songs
        user1_more = await bot_handler.handle_message(user1_id, "more")
        assert isinstance(user1_more, list)
        user1_combined = "\n".join(user1_more)
        assert "rationale: matched 'surrender'" in user1_combined
        
        # User2 says more - should get worship songs
        user2_more = await bot_handler.handle_message(user2_id, "more")
        assert isinstance(user2_more, list)
        user2_combined = "\n".join(user2_more)
        assert "rationale: matched 'worship'" in user2_combined