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
        await bot_handler.handle_message(user_id, "find songs on hope")
        
        # When: User requests more within 60 minutes (simulate time passing but < 60 min)
        with patch('src.davidbot.session_manager.datetime') as mock_datetime:
            # Simulate 30 minutes later
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=30)
            
            more_response = await bot_handler.handle_message(user_id, "more")
        
        # Then: Context is preserved and more songs returned
        lines = more_response.strip().split('\n')
        assert len(lines) == 3
        assert "matched: 'hope'" in more_response
    
    @pytest.mark.asyncio  
    async def test_session_expires_after_60_minutes(self, bot_handler):
        """Test that session context expires after exactly 60 minutes."""
        user_id = "test_user_session_456"
        
        # Given: User performs initial search  
        await bot_handler.handle_message(user_id, "find songs on faith")
        
        # When: User requests more after 60+ minutes
        with patch('src.davidbot.session_manager.datetime') as mock_datetime:
            # Simulate 61 minutes later
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=61)
            
            more_response = await bot_handler.handle_message(user_id, "more")
        
        # Then: Session has expired, more command fails gracefully
        assert "previous search" in more_response.lower() or "expired" in more_response.lower()
    
    @pytest.mark.asyncio
    async def test_session_activity_updates_expiry_timer(self, bot_handler):
        """Test that any activity resets the 60-minute timer."""
        user_id = "test_user_session_789"
        
        # Initial search
        await bot_handler.handle_message(user_id, "find songs on joy")
        
        # Activity after 30 minutes - should reset timer
        with patch('src.davidbot.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=30)
            await bot_handler.handle_message(user_id, "more")
        
        # Another 50 minutes pass (total 80 min from initial, but only 50 from last activity)
        with patch('src.davidbot.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=80)
            
            # Should still work because last activity was only 50 minutes ago
            more_response = await bot_handler.handle_message(user_id, "more")
        
        lines = more_response.strip().split('\n')
        assert len(lines) == 3  # Session should still be active
    
    @pytest.mark.asyncio
    async def test_concurrent_user_sessions_are_independent(self, bot_handler):
        """Test that different users have independent session timers."""
        user1_id = "test_user1_session"
        user2_id = "test_user2_session" 
        
        # User 1 searches
        await bot_handler.handle_message(user1_id, "find songs on peace")
        
        # 30 minutes later, User 2 searches
        with patch('src.davidbot.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=30)
            await bot_handler.handle_message(user2_id, "find songs on love")
        
        # 70 minutes from start (40 minutes after User 2's search)
        with patch('src.davidbot.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=70)
            
            # User 1's session should be expired (70 min > 60)
            user1_response = await bot_handler.handle_message(user1_id, "more")
            assert "previous search" in user1_response.lower() or "expired" in user1_response.lower()
            
            # User 2's session should still be active (40 min < 60)
            user2_response = await bot_handler.handle_message(user2_id, "more")
            lines = user2_response.strip().split('\n')
            assert len(lines) == 3
    
    @pytest.mark.asyncio
    async def test_feedback_works_within_session_timeout(self, bot_handler, mock_sheets_client):
        """Test that feedback logging works within the session timeout."""
        user_id = "test_user_feedback_session"
        
        # Search for songs
        await bot_handler.handle_message(user_id, "find songs on grace")
        
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