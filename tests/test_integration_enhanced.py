"""Integration tests for enhanced bot functionality."""

import pytest
import asyncio
from src.davidbot.enhanced_bot_handler import create_enhanced_bot_handler


class TestEnhancedBotIntegration:
    """Integration tests for the full enhanced bot pipeline."""
    
    @pytest.mark.asyncio
    async def test_mock_llm_integration(self):
        """Test enhanced bot with mock LLM (no API calls)."""
        # Create enhanced bot handler with mock LLM
        bot_handler = create_enhanced_bot_handler(use_mock_llm=True)
        
        # Test natural language search
        response = await bot_handler.handle_message('test_user', 'find songs on worship')
        assert isinstance(response, list)
        assert len(response) > 0
        
        # Verify songs were returned
        assert any('worship' in str(msg).lower() or 'praise' in str(msg).lower() for msg in response)
    
    @pytest.mark.asyncio
    async def test_enhanced_feedback_flow(self):
        """Test complete feedback flow with enhanced understanding."""
        bot_handler = create_enhanced_bot_handler(use_mock_llm=True)
        
        # First, search for songs
        search_response = await bot_handler.handle_message('test_user2', 'find songs on surrender')
        assert isinstance(search_response, list)
        assert len(search_response) > 0
        
        # Then provide feedback
        feedback_response = await bot_handler.handle_message('test_user2', 'the second one was perfect')
        assert isinstance(feedback_response, str)
        assert 'thanks' in feedback_response.lower() or 'noted' in feedback_response.lower()
    
    @pytest.mark.asyncio
    async def test_conversational_context(self):
        """Test conversational context across multiple messages."""
        bot_handler = create_enhanced_bot_handler(use_mock_llm=True)
        user_id = 'test_user3'
        
        # Initial search
        response1 = await bot_handler.handle_message(user_id, 'find songs on grace')
        assert isinstance(response1, list)
        
        # Request more with context
        response2 = await bot_handler.handle_message(user_id, 'more')
        
        # Should work based on previous context
        assert isinstance(response2, list) or 'no more songs' in str(response2).lower()
    
    def test_bot_handler_factory(self):
        """Test factory function creates correct handler type."""
        # Without API key, should use mock
        handler1 = create_enhanced_bot_handler(use_mock_llm=True)
        assert handler1.query_parser.__class__.__name__ == 'MockLLMQueryParser'
        
        # With fake API key but mock flag, should still use mock  
        handler2 = create_enhanced_bot_handler(openai_api_key='fake-key', use_mock_llm=True)
        assert handler2.query_parser.__class__.__name__ == 'MockLLMQueryParser'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])