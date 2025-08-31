"""Tests for enhanced bot handler with natural language processing."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.davidbot.enhanced_bot_handler import EnhancedBotHandler, ConversationContext
from src.davidbot.llm_query_parser import ParsedQuery, MockLLMQueryParser
from src.davidbot.models import Song, SearchResult


class TestConversationContext:
    """Test conversation context management."""
    
    def test_update_and_get_context(self):
        """Test basic context operations."""
        context_manager = ConversationContext()
        
        # Update context
        context_data = {'last_themes': ['worship', 'praise'], 'intent': 'search'}
        context_manager.update_context('user123', context_data)
        
        # Retrieve context
        retrieved = context_manager.get_context('user123')
        assert retrieved['last_themes'] == ['worship', 'praise']
        assert retrieved['intent'] == 'search'
        assert 'last_updated' in retrieved
    
    def test_context_expiry(self):
        """Test context expiry after TTL."""
        context_manager = ConversationContext()
        context_manager.ttl_minutes = 0  # Immediate expiry for testing
        
        context_data = {'test': 'data'}
        context_manager.update_context('user123', context_data)
        
        # Should be expired immediately
        retrieved = context_manager.get_context('user123')
        assert retrieved is None
    
    def test_clear_context(self):
        """Test manual context clearing."""
        context_manager = ConversationContext()
        context_manager.update_context('user123', {'test': 'data'})
        
        # Clear and verify
        context_manager.clear_context('user123')
        retrieved = context_manager.get_context('user123')
        assert retrieved is None


class TestEnhancedBotHandler:
    """Test enhanced bot handler functionality."""
    
    @pytest.fixture
    def mock_bot_handler(self):
        """Create bot handler with mocked dependencies."""
        with patch('src.davidbot.enhanced_bot_handler.create_recommendation_engine'):
            with patch('src.davidbot.enhanced_bot_handler.get_db_session'):
                handler = EnhancedBotHandler(use_mock_llm=True)
                
                # Mock the engines
                handler.database_engine = Mock()
                handler.enhanced_engine = Mock()
                handler.response_formatter = Mock()
                handler.session_manager = Mock()
                
                return handler
    
    @pytest.mark.asyncio
    async def test_natural_language_search(self, mock_bot_handler):
        """Test natural language search processing."""
        # Setup mock query parser response
        parsed_query = ParsedQuery(
            themes=['celebration', 'joy'],
            bpm_min=120,
            intent='search',
            confidence=0.9,
            raw_query='upbeat songs for celebration'
        )
        mock_bot_handler.query_parser.parse = AsyncMock(return_value=parsed_query)
        
        # Setup mock search result
        mock_songs = [
            Mock(title='Joy of the Lord', artist='Rend Collective', key='G', bpm=125),
            Mock(title='Good Grace', artist='Hillsong United', key='A', bpm=130)
        ]
        mock_result = SearchResult(songs=mock_songs, matched_term='celebration', theme='celebration')
        mock_bot_handler.enhanced_engine.search_with_parsed_query.return_value = mock_result
        
        # Setup session manager
        mock_bot_handler.session_manager.get_session.return_value = None
        mock_bot_handler.session_manager.create_or_update_session = Mock()
        
        # Setup response formatter
        mock_bot_handler.response_formatter.format_individual_songs.return_value = [
            'Joy of the Lord — Rend Collective | Key G | 125 BPM',
            'Good Grace — Hillsong United | Key A | 130 BPM'
        ]
        
        # Mock logging
        mock_bot_handler._log_enhanced_message = AsyncMock()
        
        # Test the search
        response = await mock_bot_handler.handle_message('user123', 'upbeat songs for celebration')
        
        # Verify results
        assert isinstance(response, list)
        assert len(response) >= 2
        assert 'Joy of the Lord' in response[0] or 'Joy of the Lord' in response[1]
        
        # Verify LLM parser was called
        mock_bot_handler.query_parser.parse.assert_called_once()
        
        # Verify enhanced engine was called
        mock_bot_handler.enhanced_engine.search_with_parsed_query.assert_called_once()
        args = mock_bot_handler.enhanced_engine.search_with_parsed_query.call_args[0]
        assert args[0].themes == ['celebration', 'joy']
        assert args[0].bpm_min == 120
    
    @pytest.mark.asyncio
    async def test_conversational_feedback(self, mock_bot_handler):
        """Test enhanced feedback understanding."""
        # Setup session with songs
        mock_session = Mock()
        mock_session.last_search = Mock()
        mock_session.last_search.songs = [
            Mock(title='Amazing Grace'),
            Mock(title='How Great Thou Art'),
            Mock(title='Holy Spirit')
        ]
        mock_bot_handler.session_manager.get_session.return_value = mock_session
        mock_bot_handler.session_manager.update_session_activity = Mock()
        
        # Mock feedback logging
        mock_bot_handler._log_feedback = AsyncMock()
        
        # Mock query parser for feedback intent
        parsed_query = ParsedQuery(
            themes=[],
            intent='feedback', 
            confidence=0.8,
            raw_query='the second one was perfect'
        )
        mock_bot_handler.query_parser.parse = AsyncMock(return_value=parsed_query)
        mock_bot_handler._log_enhanced_message = AsyncMock()
        
        # Test natural feedback understanding
        response = await mock_bot_handler.handle_message('user123', 'the second one was perfect')
        
        # Verify feedback was processed
        assert 'How Great Thou Art' in response
        assert 'Thanks!' in response or 'noted' in response.lower()
        
        # Verify feedback was logged
        mock_bot_handler._log_feedback.assert_called_once()
        feedback_event = mock_bot_handler._log_feedback.call_args[0][0]
        assert feedback_event.song_position == 2
        assert feedback_event.song_title == 'How Great Thou Art'
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, mock_bot_handler):
        """Test 'songs like X' functionality."""
        # Setup parsed query for similarity search
        parsed_query = ParsedQuery(
            themes=['grace'],
            similarity_song='Amazing Grace',
            intent='search',
            confidence=0.85,
            raw_query='songs like Amazing Grace'
        )
        mock_bot_handler.query_parser.parse = AsyncMock(return_value=parsed_query)
        
        # Setup mock similar songs
        mock_songs = [
            Mock(title='Grace to Grace', artist='Hillsong United'),
            Mock(title='Grace Like Rain', artist='Todd Agnew')
        ]
        mock_result = SearchResult(songs=mock_songs, matched_term='similar to Amazing Grace', theme='grace')
        mock_bot_handler.enhanced_engine.search_with_parsed_query.return_value = mock_result
        
        # Setup other mocks
        mock_bot_handler.session_manager.get_session.return_value = None
        mock_bot_handler.session_manager.create_or_update_session = Mock()
        mock_bot_handler.response_formatter.format_individual_songs.return_value = [
            'Grace to Grace — Hillsong United',
            'Grace Like Rain — Todd Agnew'
        ]
        mock_bot_handler._log_enhanced_message = AsyncMock()
        
        # Test similarity search
        response = await mock_bot_handler.handle_message('user123', 'songs like Amazing Grace')
        
        # Verify similarity search was processed
        assert isinstance(response, list)
        mock_bot_handler.enhanced_engine.search_with_parsed_query.assert_called_once()
        
        # Verify parsed query had similarity_song set
        args = mock_bot_handler.enhanced_engine.search_with_parsed_query.call_args[0]
        assert args[0].similarity_song == 'Amazing Grace'
    
    @pytest.mark.asyncio
    async def test_context_aware_more_request(self, mock_bot_handler):
        """Test 'more' requests with conversation context."""
        # Setup conversation context
        mock_bot_handler.conversation_context.update_context('user123', {
            'last_themes': ['worship', 'praise'],
            'last_intent': 'search'
        })
        
        # Setup parsed query for 'more'
        parsed_query = ParsedQuery(
            themes=[],
            intent='more',
            confidence=0.9,
            raw_query='more'
        )
        mock_bot_handler.query_parser.parse = AsyncMock(return_value=parsed_query)
        
        # Setup session manager (no active session)
        mock_bot_handler.session_manager.get_session.return_value = None
        
        # Setup enhanced engine for context-based search
        mock_songs = [Mock(title='Forever', artist='Kari Jobe')]
        mock_result = SearchResult(songs=mock_songs, matched_term='worship, praise', theme='worship')
        mock_bot_handler.enhanced_engine.search_with_parsed_query.return_value = mock_result
        
        # Setup other mocks
        mock_bot_handler.session_manager.create_or_update_session = Mock()
        mock_bot_handler.response_formatter.format_individual_songs.return_value = ['Forever — Kari Jobe']
        mock_bot_handler._log_enhanced_message = AsyncMock()
        
        # Test context-aware more request
        response = await mock_bot_handler.handle_message('user123', 'more')
        
        # Verify context was used
        assert isinstance(response, list)
        mock_bot_handler.enhanced_engine.search_with_parsed_query.assert_called()
        
        # Should have reconstructed search from context
        args = mock_bot_handler.enhanced_engine.search_with_parsed_query.call_args[0]
        assert 'worship' in args[0].themes or 'praise' in args[0].themes
    
    @pytest.mark.asyncio
    async def test_fallback_on_low_confidence(self, mock_bot_handler):
        """Test fallback behavior for low confidence queries."""
        # Setup low confidence parsed query
        parsed_query = ParsedQuery(
            themes=[],
            intent='unknown',
            confidence=0.2,
            raw_query='asdjklasdjkl'
        )
        mock_bot_handler.query_parser.parse = AsyncMock(return_value=parsed_query)
        mock_bot_handler._log_enhanced_message = AsyncMock()
        
        # Test low confidence handling
        response = await mock_bot_handler.handle_message('user123', 'asdjklasdjkl')
        
        # Should provide helpful guidance
        assert isinstance(response, str)
        assert 'not sure' in response.lower() or 'try something like' in response.lower()
        assert 'find songs' in response or 'surrender' in response
    
    @pytest.mark.asyncio
    async def test_ministry_context_responses(self, mock_bot_handler):
        """Test worship leader personality in responses."""
        # Setup contemplative query
        parsed_query = ParsedQuery(
            themes=['surrender', 'grace'],
            mood='contemplative',
            intent='search',
            confidence=0.9,
            raw_query='slow songs for altar call'
        )
        mock_bot_handler.query_parser.parse = AsyncMock(return_value=parsed_query)
        
        # Setup mock results
        mock_songs = [Mock(title='Surrender', artist='Hillsong United')]
        mock_result = SearchResult(songs=mock_songs, matched_term='surrender', theme='surrender')
        mock_bot_handler.enhanced_engine.search_with_parsed_query.return_value = mock_result
        
        # Setup other mocks
        mock_bot_handler.session_manager.get_session.return_value = None
        mock_bot_handler.session_manager.create_or_update_session = Mock()
        mock_bot_handler.response_formatter.format_individual_songs.return_value = [
            'Surrender — Hillsong United | Key A | 72 BPM'
        ]
        mock_bot_handler._log_enhanced_message = AsyncMock()
        
        # Test ministry-focused response
        response = await mock_bot_handler.handle_message('user123', 'slow songs for altar call')
        
        # Should include ministry context
        assert isinstance(response, list)
        # First message should be contextual intro
        assert any('ministry' in msg.lower() or 'perfect for' in msg.lower() for msg in response)
    
    def test_bpm_filtering(self, mock_bot_handler):
        """Test BPM range filtering."""
        # Import the actual filtering method from enhanced engine
        from src.davidbot.enhanced_recommendation_engine import EnhancedRecommendationEngine
        from src.davidbot.database_recommendation_engine import DatabaseRecommendationEngine
        
        # Create real enhanced engine for testing filtering
        db_engine = Mock()
        enhanced_engine = EnhancedRecommendationEngine(db_engine)
        
        # Create mock songs with different BPMs
        songs = [
            Mock(bpm=65, title='Slow Song'),
            Mock(bpm=85, title='Medium Song'),
            Mock(bpm=125, title='Fast Song'),
            Mock(bpm=None, title='No BPM Song')
        ]
        
        # Test slow filter (max 85)
        filtered = enhanced_engine._filter_by_bpm(songs, None, 85)
        titles = [song.title for song in filtered]
        assert 'Slow Song' in titles
        assert 'Medium Song' in titles
        assert 'Fast Song' not in titles
        assert 'No BPM Song' not in titles
        
        # Test fast filter (min 120)
        filtered = enhanced_engine._filter_by_bpm(songs, 120, None)
        titles = [song.title for song in filtered]
        assert 'Fast Song' in titles
        assert 'Slow Song' not in titles
        assert 'Medium Song' not in titles


class TestQueryParsing:
    """Test LLM query parsing functionality."""
    
    @pytest.mark.asyncio
    async def test_mock_parser_basic_patterns(self):
        """Test mock parser handles basic patterns."""
        parser = MockLLMQueryParser()
        
        # Test worship query
        result = await parser.parse('find songs on worship')
        assert 'worship' in result.themes
        assert result.intent == 'search'
        
        # Test upbeat query
        result = await parser.parse('upbeat celebration songs')
        assert 'joy' in result.themes or 'celebration' in result.themes
        assert result.bpm_min == 120
        
        # Test slow query
        result = await parser.parse('slow songs for prayer')
        assert result.bpm_max == 85


if __name__ == '__main__':
    pytest.main([__file__, '-v'])