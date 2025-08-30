"""Data models for DavidBot."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Song:
    """Represents a song with metadata."""
    title: str
    artist: str
    key: str
    bpm: int
    tags: List[str]
    url: str
    search_terms: List[str]  # Terms this song matches


@dataclass
class SearchResult:
    """Result of a song search."""
    songs: List[Song]
    matched_term: str
    theme: str


@dataclass
class UserSession:
    """User session with context and timing."""
    user_id: str
    last_search: Optional[SearchResult]
    last_activity: datetime
    returned_songs: List[str]  # Track which songs were already returned
    
    
@dataclass
class FeedbackEvent:
    """User feedback event."""
    user_id: str
    song_position: int
    feedback_type: str  # "thumbs_up"
    timestamp: datetime
    song_title: Optional[str] = None
    
    
@dataclass
class MessageLog:
    """Log entry for all interactions."""
    user_id: str
    message_type: str  # "search", "more", "feedback"
    message_content: str
    response_content: str
    timestamp: datetime