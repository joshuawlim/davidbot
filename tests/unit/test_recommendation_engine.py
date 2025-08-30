"""Unit tests for recommendation engine."""

import pytest
from src.davidbot.recommendation_engine import RecommendationEngine
from src.davidbot.models import Song


class TestRecommendationEngine:
    """Test the recommendation engine functionality."""
    
    @pytest.fixture
    def engine(self):
        """Create recommendation engine instance."""
        return RecommendationEngine()
    
    def test_search_finds_surrender_songs(self, engine):
        """Test that surrender queries return surrender-themed songs."""
        result = engine.search("find songs on surrender")
        
        assert result is not None
        assert len(result.songs) == 3
        assert result.matched_term == "surrender"
        assert result.theme == "surrender"
        
        for song in result.songs:
            assert "surrender" in song.search_terms
    
    def test_search_excludes_already_returned_songs(self, engine):
        """Test that excluded songs are not returned."""
        # First search
        first_result = engine.search("find songs on worship")
        first_titles = [song.title for song in first_result.songs]
        
        # Second search excluding first results
        second_result = engine.search("find songs on worship", excluded_songs=first_titles)
        second_titles = [song.title for song in second_result.songs]
        
        # No overlap between results
        assert len(set(first_titles) & set(second_titles)) == 0
    
    def test_search_returns_none_for_unknown_term(self, engine):
        """Test that unknown search terms return None."""
        result = engine.search("find songs about quantum physics")
        assert result is None
    
    def test_search_case_insensitive(self, engine):
        """Test that search is case insensitive."""
        result1 = engine.search("find songs on SURRENDER")
        result2 = engine.search("find songs on surrender")
        
        assert result1.matched_term == result2.matched_term
        assert len(result1.songs) == len(result2.songs)