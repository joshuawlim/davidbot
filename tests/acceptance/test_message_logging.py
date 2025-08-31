"""Acceptance tests for message logging functionality.

Tests Acceptance Criteria 6:
All interactions logged to MessageLog sheet
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.davidbot.bot_handler import BotHandler


class TestMessageLoggingAcceptance:
    """Test the message logging acceptance criteria."""
    
    @pytest.fixture
    def mock_sheets_client(self):
        """Mock sheets client that records all logging calls."""
        mock_client = AsyncMock()
        mock_client.log_message.return_value = True
        mock_client.log_feedback.return_value = True
        return mock_client
    
    @pytest.fixture
    def bot_handler(self, mock_sheets_client):
        """Create bot handler with mocked dependencies."""
        return BotHandler(sheets_client=mock_sheets_client)
    
    @pytest.mark.asyncio
    async def test_search_interactions_logged_to_message_log(self, bot_handler, mock_sheets_client):
        """
        ACCEPTANCE CRITERIA 6:
        All interactions logged to MessageLog sheet
        """
        user_id = "test_user_logging_123"
        
        # When: User performs song search
        await bot_handler.handle_message(user_id, "find songs on surrender")
        
        # Then: Interaction is logged to MessageLog
        mock_sheets_client.log_message.assert_called()
        
        # Verify the logged message structure
        call_args = mock_sheets_client.log_message.call_args[0]
        message_log = call_args[0]
        
        assert message_log.user_id == user_id
        assert message_log.message_type == "search"
        assert message_log.message_content == "find songs on surrender"
        assert "surrender" in message_log.response_content
        assert message_log.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_more_command_interactions_logged(self, bot_handler, mock_sheets_client):
        """Test that 'more' command interactions are logged."""
        user_id = "test_user_logging_456"
        
        # Setup: Initial search 
        await bot_handler.handle_message(user_id, "find songs on worship")
        mock_sheets_client.log_message.reset_mock()  # Clear previous calls
        
        # When: User requests more songs
        await bot_handler.handle_message(user_id, "more")
        
        # Then: More command is logged
        mock_sheets_client.log_message.assert_called()
        
        call_args = mock_sheets_client.log_message.call_args[0] 
        message_log = call_args[0]
        
        assert message_log.user_id == user_id
        assert message_log.message_type == "more"
        assert message_log.message_content == "more"
        assert "worship" in message_log.response_content  # Response should contain songs
    
    @pytest.mark.asyncio
    async def test_feedback_interactions_logged(self, bot_handler, mock_sheets_client):
        """Test that feedback interactions are logged to MessageLog."""
        user_id = "test_user_logging_789"
        
        # Setup: Search for songs
        await bot_handler.handle_message(user_id, "find songs on grace")
        mock_sheets_client.log_message.reset_mock()
        
        # When: User provides feedback
        await bot_handler.handle_message(user_id, "👍 1")
        
        # Then: Feedback interaction is logged to MessageLog
        mock_sheets_client.log_message.assert_called()
        
        call_args = mock_sheets_client.log_message.call_args[0]
        message_log = call_args[0]
        
        assert message_log.user_id == user_id
        assert message_log.message_type == "feedback"
        assert message_log.message_content == "👍 1"
        assert "thanks" in message_log.response_content.lower() or "recorded" in message_log.response_content.lower()
    
    @pytest.mark.asyncio
    async def test_all_message_types_have_distinct_logging(self, bot_handler, mock_sheets_client):
        """Test that different message types are logged with correct categorization."""
        user_id = "test_user_message_types"
        
        # Search message
        await bot_handler.handle_message(user_id, "find songs on peace")
        search_call = mock_sheets_client.log_message.call_args[0][0]
        assert search_call.message_type == "search"
        
        # More message
        await bot_handler.handle_message(user_id, "more") 
        more_call = mock_sheets_client.log_message.call_args[0][0]
        assert more_call.message_type == "more"
        
        # Feedback message
        await bot_handler.handle_message(user_id, "👍 1")
        feedback_call = mock_sheets_client.log_message.call_args[0][0]
        assert feedback_call.message_type == "feedback"
    
    @pytest.mark.asyncio
    async def test_error_responses_are_logged(self, bot_handler, mock_sheets_client):
        """Test that error responses are also logged to MessageLog.""" 
        user_id = "test_user_error_logging"
        
        # When: User sends invalid command (more without prior search)
        await bot_handler.handle_message(user_id, "more")
        
        # Then: Error response is logged
        mock_sheets_client.log_message.assert_called()
        
        call_args = mock_sheets_client.log_message.call_args[0]
        message_log = call_args[0]
        
        assert message_log.user_id == user_id
        assert message_log.message_type == "more"
        assert "previous search" in message_log.response_content.lower() or "search first" in message_log.response_content.lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_user_messages_logged_separately(self, bot_handler, mock_sheets_client):
        """Test that messages from different users are logged separately."""
        user1_id = "test_user1_concurrent"
        user2_id = "test_user2_concurrent"
        
        # Both users send messages
        await bot_handler.handle_message(user1_id, "find songs on joy")
        await bot_handler.handle_message(user2_id, "find songs on hope")
        
        # Verify both were logged with correct user IDs
        assert mock_sheets_client.log_message.call_count == 2
        
        # Check that the calls had different user IDs
        all_calls = mock_sheets_client.log_message.call_args_list
        user_ids_logged = [call[0][0].user_id for call in all_calls]
        
        assert user1_id in user_ids_logged
        assert user2_id in user_ids_logged
    
    @pytest.mark.asyncio
    async def test_message_logging_includes_timestamps(self, bot_handler, mock_sheets_client):
        """Test that all logged messages include accurate timestamps."""
        user_id = "test_user_timestamps"
        
        start_time = datetime.now()
        
        # Send message
        await bot_handler.handle_message(user_id, "find songs on faith")
        
        end_time = datetime.now()
        
        # Verify timestamp is within expected range
        call_args = mock_sheets_client.log_message.call_args[0]
        message_log = call_args[0]
        
        assert start_time <= message_log.timestamp <= end_time
    
    @pytest.mark.asyncio
    async def test_response_content_matches_user_response(self, bot_handler, mock_sheets_client):
        """Test that logged response content matches what user actually received."""
        user_id = "test_user_response_match"
        
        # When: User searches for songs
        actual_response = await bot_handler.handle_message(user_id, "find songs on love")
        
        # Then: Logged response matches actual response
        call_args = mock_sheets_client.log_message.call_args[0]
        message_log = call_args[0]
        
        # For list responses, logging combines them with separator
        if isinstance(actual_response, list):
            expected_logged_content = "\n---\n".join(actual_response)
            assert message_log.response_content == expected_logged_content
        else:
            assert message_log.response_content == actual_response