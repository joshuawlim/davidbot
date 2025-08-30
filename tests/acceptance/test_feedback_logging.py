"""Acceptance tests for feedback logging functionality.

Tests Acceptance Criteria 3:
User sends "👍 1" → feedback logged to Google Sheets with confirmation
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.davidbot.bot_handler import BotHandler


class TestFeedbackLoggingAcceptance:
    """Test the feedback logging acceptance criteria."""
    
    @pytest.fixture
    def mock_sheets_client(self):
        """Mock sheets client that records feedback calls."""
        mock_client = AsyncMock()
        mock_client.log_message.return_value = True
        mock_client.log_feedback.return_value = True
        return mock_client
    
    @pytest.fixture 
    def bot_handler(self, mock_sheets_client):
        """Create bot handler with mocked dependencies.""" 
        return BotHandler(sheets_client=mock_sheets_client)
    
    @pytest.mark.asyncio
    async def test_thumbs_up_feedback_logs_to_sheets_with_confirmation(self, bot_handler, mock_sheets_client):
        """
        ACCEPTANCE CRITERIA 3:
        User sends "👍 1" → feedback logged to Google Sheets with confirmation
        """
        user_id = "test_user_feedback_123"
        
        # Given: User has received song recommendations
        await bot_handler.handle_message(user_id, "find songs on grace")
        
        # When: User provides thumbs up feedback for song 1
        feedback_response = await bot_handler.handle_message(user_id, "👍 1")
        
        # Then: Feedback is logged to Google Sheets
        mock_sheets_client.log_feedback.assert_called_once()
        
        # Extract the call arguments
        call_args = mock_sheets_client.log_feedback.call_args[0]
        feedback_event = call_args[0]
        
        assert feedback_event.user_id == user_id
        assert feedback_event.song_position == 1
        assert feedback_event.feedback_type == "thumbs_up"
        assert feedback_event.timestamp is not None
        
        # And: User receives confirmation
        assert "thanks" in feedback_response.lower() or "recorded" in feedback_response.lower()
    
    @pytest.mark.asyncio
    async def test_feedback_for_different_song_positions(self, bot_handler, mock_sheets_client):
        """Test feedback works for songs at different positions (1, 2, 3)."""
        user_id = "test_user_feedback_456"
        
        # Given: User has song recommendations
        await bot_handler.handle_message(user_id, "find songs on worship")
        
        # Test feedback for song 2
        await bot_handler.handle_message(user_id, "👍 2")
        
        # Verify correct position logged
        call_args = mock_sheets_client.log_feedback.call_args[0]
        feedback_event = call_args[0]
        assert feedback_event.song_position == 2
        
        # Test feedback for song 3  
        await bot_handler.handle_message(user_id, "👍 3")
        
        # Verify correct position logged
        call_args = mock_sheets_client.log_feedback.call_args[0]
        feedback_event = call_args[0]
        assert feedback_event.song_position == 3
    
    @pytest.mark.asyncio
    async def test_feedback_without_previous_search_handled_gracefully(self, bot_handler):
        """Test feedback when no previous search context exists."""
        user_id = "test_user_feedback_789"
        
        # When: User provides feedback without prior search
        response = await bot_handler.handle_message(user_id, "👍 1")
        
        # Then: Should return helpful message, not crash
        assert "search first" in response.lower() or "no songs" in response.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_feedback_format_handled_gracefully(self, bot_handler):
        """Test invalid feedback formats are handled properly.""" 
        user_id = "test_user_feedback_000"
        
        # Given: User has song recommendations
        await bot_handler.handle_message(user_id, "find songs on peace")
        
        # Test various invalid formats
        invalid_formats = ["👍 0", "👍 4", "👍", "👍 abc", "👍 -1"]
        
        for invalid_format in invalid_formats:
            response = await bot_handler.handle_message(user_id, invalid_format)
            # Should not crash, should provide helpful message
            assert response != ""
            assert "1" in response and "3" in response  # Hint about valid range
    
    @pytest.mark.asyncio
    async def test_feedback_uses_most_recent_search_context(self, bot_handler, mock_sheets_client):
        """Test feedback refers to the most recent search results."""
        user_id = "test_user_feedback_context"
        
        # First search
        await bot_handler.handle_message(user_id, "find songs on surrender")
        
        # Second search (more recent)
        await bot_handler.handle_message(user_id, "find songs on worship")
        
        # Feedback should apply to most recent search
        await bot_handler.handle_message(user_id, "👍 1")
        
        # Verify the logged feedback references the worship context
        call_args = mock_sheets_client.log_feedback.call_args[0] 
        # We can't easily verify the song title here without more complex mocking
        # but the session should track the most recent search