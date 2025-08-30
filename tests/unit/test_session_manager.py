"""Unit tests for session manager."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.davidbot.session_manager import SessionManager
from src.davidbot.models import Song, SearchResult


class TestSessionManager:
    """Test the session manager functionality."""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager instance."""
        return SessionManager()
    
    @pytest.fixture
    def sample_search_result(self):
        """Create sample search result for testing."""
        songs = [
            Song("Test Song 1", "Artist 1", "G", 72, ["test"], "http://test1.com", ["test"]),
            Song("Test Song 2", "Artist 2", "F", 84, ["test"], "http://test2.com", ["test"])
        ]
        return SearchResult(songs=songs, matched_term="test", theme="test")
    
    def test_create_new_session(self, session_manager, sample_search_result):
        """Test creating a new user session."""
        user_id = "test_user_123"
        
        session = session_manager.create_or_update_session(user_id, sample_search_result)
        
        assert session.user_id == user_id
        assert session.last_search == sample_search_result
        assert len(session.returned_songs) == 2
        assert "Test Song 1" in session.returned_songs
        assert "Test Song 2" in session.returned_songs
    
    def test_get_nonexistent_session_returns_none(self, session_manager):
        """Test getting session that doesn't exist returns None."""
        session = session_manager.get_session("nonexistent_user")
        assert session is None
    
    def test_update_session_activity(self, session_manager, sample_search_result):
        """Test updating session activity timestamp."""
        user_id = "test_user_456"
        
        # Create session
        original_session = session_manager.create_or_update_session(user_id, sample_search_result)
        original_time = original_session.last_activity
        
        # Update activity
        updated_session = session_manager.update_session_activity(user_id)
        
        assert updated_session is not None
        assert updated_session.last_activity >= original_time
    
    def test_add_returned_songs_to_session(self, session_manager, sample_search_result):
        """Test adding new songs to session's returned songs list."""
        user_id = "test_user_789"
        
        # Create session
        session_manager.create_or_update_session(user_id, sample_search_result)
        
        # Add more songs
        new_songs = ["Test Song 3", "Test Song 4"]
        session_manager.add_returned_songs_to_session(user_id, new_songs)
        
        # Verify songs were added
        session = session_manager.get_session(user_id)
        assert "Test Song 3" in session.returned_songs
        assert "Test Song 4" in session.returned_songs
        assert len(session.returned_songs) == 4  # Original 2 + new 2
    
    def test_session_expiry_logic(self, session_manager, sample_search_result):
        """Test session expiry based on TTL."""
        user_id = "test_user_expiry"
        
        # Create session
        session_manager.create_or_update_session(user_id, sample_search_result)
        
        # Verify session exists
        assert session_manager.get_session(user_id) is not None
        
        # Mock time to simulate expiry
        with patch.object(session_manager.sessions[user_id], 'last_activity', 
                          datetime.now() - timedelta(minutes=61)):
            # Session should now be expired
            expired_session = session_manager.get_session(user_id)
            assert expired_session is None
            
        # Verify session was removed from store
        assert user_id not in session_manager.sessions