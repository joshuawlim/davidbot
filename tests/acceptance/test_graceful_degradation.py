"""Acceptance tests for graceful degradation.

Tests Acceptance Criteria 5:
Google Sheets failures don't block user responses (graceful degradation)
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.davidbot.bot_handler import BotHandler


class TestGracefulDegradationAcceptance:
    """Test graceful degradation when Google Sheets fails."""
    
    @pytest.fixture
    def failing_sheets_client(self):
        """Mock sheets client that always fails."""
        mock_client = AsyncMock()
        mock_client.log_message.side_effect = Exception("Sheets API Error")
        mock_client.log_feedback.side_effect = Exception("Sheets API Error") 
        return mock_client
    
    @pytest.fixture
    def bot_handler_with_failing_sheets(self, failing_sheets_client):
        """Create bot handler with failing sheets client."""
        return BotHandler(sheets_client=failing_sheets_client)
    
    @pytest.mark.asyncio
    async def test_song_search_works_when_sheets_logging_fails(self, bot_handler_with_failing_sheets):
        """
        ACCEPTANCE CRITERIA 5:
        Google Sheets failures don't block user responses (graceful degradation)
        """
        user_id = "test_user_degradation_123"
        
        # When: User searches for songs while sheets logging fails
        response = await bot_handler_with_failing_sheets.handle_message(user_id, "find songs on hope")
        
        # Then: User still gets song recommendations despite logging failure
        lines = response.strip().split('\n')
        assert len(lines) == 3, f"Expected 3 songs despite sheets failure, got {len(lines)}"
        
        # Verify PRD format maintained
        for line in lines:
            assert " — " in line and " | Key " in line and " BPM | " in line
            assert "matched: 'hope'" in line
    
    @pytest.mark.asyncio
    async def test_more_command_works_when_sheets_logging_fails(self, bot_handler_with_failing_sheets):
        """Test 'more' command works even when sheets logging fails."""
        user_id = "test_user_degradation_456"
        
        # Initial search (sheets will fail but shouldn't block response)
        await bot_handler_with_failing_sheets.handle_message(user_id, "find songs on peace")
        
        # More command should still work
        more_response = await bot_handler_with_failing_sheets.handle_message(user_id, "more")
        lines = more_response.strip().split('\n')
        
        assert len(lines) == 3
        assert "matched: 'peace'" in more_response
    
    @pytest.mark.asyncio  
    async def test_feedback_graceful_when_sheets_logging_fails(self, bot_handler_with_failing_sheets):
        """Test feedback provides helpful response even when sheets logging fails."""
        user_id = "test_user_degradation_789"
        
        # Search for songs first
        await bot_handler_with_failing_sheets.handle_message(user_id, "find songs on worship")
        
        # Provide feedback - logging will fail but user should get response
        feedback_response = await bot_handler_with_failing_sheets.handle_message(user_id, "👍 1")
        
        # User should get acknowledgment even if logging failed
        assert feedback_response != ""
        # Should indicate issue but not crash
        assert ("thanks" in feedback_response.lower() or 
                "received" in feedback_response.lower() or
                "noted" in feedback_response.lower())
    
    @pytest.fixture
    def intermittent_sheets_client(self):
        """Mock sheets client that fails intermittently."""
        mock_client = AsyncMock()
        
        # Set up call counts to simulate intermittent failures
        mock_client.call_count = 0
        
        def failing_log_message(*args, **kwargs):
            mock_client.call_count += 1
            if mock_client.call_count % 3 == 0:  # Fail every 3rd call
                raise Exception("Intermittent Sheets failure")
            return True
            
        mock_client.log_message.side_effect = failing_log_message
        mock_client.log_feedback.return_value = True
        return mock_client
    
    @pytest.mark.asyncio
    async def test_system_recovers_from_intermittent_sheets_failures(self, intermittent_sheets_client):
        """Test system continues working despite intermittent sheets failures."""
        bot_handler = BotHandler(sheets_client=intermittent_sheets_client)
        user_id = "test_user_intermittent"
        
        # Multiple operations - some will fail sheets logging, some won't
        responses = []
        for i in range(5):
            response = await bot_handler.handle_message(user_id, f"find songs on joy")
            responses.append(response)
            
        # All responses should be valid despite some logging failures
        for response in responses:
            lines = response.strip().split('\n')
            assert len(lines) == 3
            assert "matched: 'joy'" in response
    
    @pytest.mark.asyncio
    async def test_bot_handler_has_error_boundaries(self, failing_sheets_client):
        """Test that bot handler has proper error boundaries."""
        bot_handler = BotHandler(sheets_client=failing_sheets_client)
        user_id = "test_user_boundaries"
        
        # Even if sheets client throws exceptions, bot should not crash
        try:
            response = await bot_handler.handle_message(user_id, "find songs on grace")
            # Should get valid response
            assert response != ""
            assert "grace" in response.lower()
        except Exception as e:
            # Should not propagate sheets exceptions to user
            pytest.fail(f"Bot handler should not let sheets exceptions propagate: {e}")
    
    @pytest.mark.asyncio
    async def test_logging_failure_does_not_affect_session_state(self, failing_sheets_client):
        """Test that logging failures don't corrupt session state."""
        bot_handler = BotHandler(sheets_client=failing_sheets_client)
        user_id = "test_user_session_integrity"
        
        # Initial search (logging will fail)
        await bot_handler.handle_message(user_id, "find songs on love")
        
        # Session state should still be maintained for 'more' command
        more_response = await bot_handler.handle_message(user_id, "more")
        
        lines = more_response.strip().split('\n') 
        assert len(lines) == 3
        assert "matched: 'love'" in more_response