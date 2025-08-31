"""Acceptance tests for session management functionality.

Tests Acceptance Criteria 4:
Session context persists for 60 minutes, then expires
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.davidbot.bot_handler import BotHandler


class TestSessionManagementAcceptance:
    """Test the session management acceptance criteria."""
    
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
    async def test_session_persists_within_60_minutes(self, bot_handler):
        """
        ACCEPTANCE CRITERIA 4:
        Session context persists for 60 minutes, then expires
        """
        user_id = "test_user_session_123"
        
        # Given: User performs initial search  
        await bot_handler.handle_message(user_id, "find songs on surrender")
        
        # When: User requests more within 60 minutes (simulate time passing but < 60 min)
        # Session should still be active within 60 minutes
        # No need to mock time - session should persist
        more_response = await bot_handler.handle_message(user_id, "more")
        
        # Then: Context is preserved and more songs returned
        assert isinstance(more_response, list), "More command should return list of messages"
        
        # Should return songs (not error message)
        assert len(more_response) > 0
        combined_response = "\n".join(more_response)
        assert "rationale: matched 'surrender'" in combined_response
    
    @pytest.mark.asyncio  
    async def test_session_expires_after_60_minutes(self, bot_handler):
        """Test that session context expires after exactly 60 minutes."""
        user_id = "test_user_session_456"
        
        # Given: User performs initial search  
        await bot_handler.handle_message(user_id, "find songs on worship")
        
        # When: User requests more after 60+ minutes
        # Manually expire the session by setting old timestamp
        session = bot_handler.session_manager.get_session(user_id)
        if session:
            session.last_activity = datetime.now() - timedelta(minutes=61)
            
        more_response = await bot_handler.handle_message(user_id, "more")
        
        # Then: Session has expired, more command fails gracefully
        assert isinstance(more_response, list), "More command should return list"
        assert len(more_response) == 1, "Should return single error message"
        response_text = more_response[0].lower()
        assert "previous search" in response_text or "expired" in response_text
    
    @pytest.mark.asyncio
    async def test_session_activity_updates_expiry_timer(self, bot_handler):
        """Test that any activity resets the 60-minute timer."""
        user_id = "test_user_session_789"
        
        # Initial search
        await bot_handler.handle_message(user_id, "find songs on joy")
        
        # Activity after some time - should reset timer  
        await bot_handler.handle_message(user_id, "more")
        
        # For this test, we'll manually test that session activity updates work
        # by checking that the session timestamp gets updated
        session_before = bot_handler.session_manager.get_session(user_id)
        original_activity = session_before.last_activity if session_before else None
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.1)  # Increased delay to ensure measurable timestamp difference
        
        # Any activity should update the timer
        more_response = await bot_handler.handle_message(user_id, "more")
        
        session_after = bot_handler.session_manager.get_session(user_id) 
        updated_activity = session_after.last_activity if session_after else None
        
        assert isinstance(more_response, list), "More command should return list"
        assert len(more_response) > 0, "Session should still be active - should return songs"
        
        # Verify that activity timestamp was updated (proving timer reset works)
        assert updated_activity > original_activity, "Session activity should be updated by more command"
    
    @pytest.mark.asyncio
    async def test_concurrent_user_sessions_are_independent(self, bot_handler):
        """Test that different users have independent session timers."""
        user1_id = "test_user1_session"
        user2_id = "test_user2_session" 
        
        # User 1 searches
        await bot_handler.handle_message(user1_id, "find songs on praise")
        
        # User 2 searches
        await bot_handler.handle_message(user2_id, "find songs on worship")
        
        # Manually expire User 1's session only
        user1_session = bot_handler.session_manager.get_session(user1_id)
        if user1_session:
            user1_session.last_activity = datetime.now() - timedelta(minutes=61)
        
        # User 1's session should be expired
        user1_response = await bot_handler.handle_message(user1_id, "more")
        assert isinstance(user1_response, list), "More command should return list"
        assert len(user1_response) == 1, "Should return single error message"
        response_text = user1_response[0].lower()
        assert "previous search" in response_text or "expired" in response_text
        
        # User 2's session should still be active
        user2_response = await bot_handler.handle_message(user2_id, "more")
        assert isinstance(user2_response, list), "More command should return list"
        assert len(user2_response) > 0, "User 2 session should still be active"
    
    @pytest.mark.asyncio
    async def test_feedback_works_within_session_timeout(self, bot_handler, mock_sheets_client):
        """Test that feedback logging works within the session timeout."""
        user_id = "test_user_feedback_session"
        
        # Search for songs
        await bot_handler.handle_message(user_id, "find songs on praise")
        
        # 59 minutes later, provide feedback - should work
        with patch('src.davidbot.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=59)
            
            feedback_response = await bot_handler.handle_message(user_id, "👍 1")
        
        # Feedback should be logged
        mock_sheets_client.log_feedback.assert_called()
        assert "thanks" in feedback_response.lower() or "recorded" in feedback_response.lower()
    
    @pytest.mark.asyncio
    async def test_feedback_fails_after_session_timeout(self, bot_handler, mock_sheets_client):
        """Test that feedback fails gracefully after session timeout."""
        user_id = "test_user_feedback_expired"
        
        # Search for songs
        await bot_handler.handle_message(user_id, "find songs on worship")
        
        # 61 minutes later, try to provide feedback - should fail gracefully
        with patch('src.davidbot.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=61)
            
            feedback_response = await bot_handler.handle_message(user_id, "👍 1")
        
        # Feedback should not be logged
        mock_sheets_client.log_feedback.assert_not_called()
        assert "search first" in feedback_response.lower() or "expired" in feedback_response.lower()