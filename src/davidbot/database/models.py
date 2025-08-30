"""SQLAlchemy models for DavidBot database."""

from sqlalchemy import Column, Integer, String, Text, Boolean, REAL, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from typing import List, Dict, Optional

Base = declarative_base()


class Song(Base):
    """Song metadata table."""
    __tablename__ = 'songs'
    
    song_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    original_key = Column(String, nullable=False)
    bpm = Column(Integer)
    boy_keys = Column(Text)  # JSON array: ["G", "A", "Bb"]
    girl_keys = Column(Text)  # JSON array: ["F", "G", "Ab"]
    tags = Column(Text)  # JSON array: ["surrender", "worship"]
    resource_link = Column(Text)
    ccli_number = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    lyrics = relationship("Lyrics", back_populates="song", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="song")
    themes = relationship("ThemeMapping", back_populates="song", cascade="all, delete-orphan")
    usage_history = relationship("SongUsage", back_populates="song", cascade="all, delete-orphan")
    
    @property
    def boy_keys_list(self) -> List[str]:
        """Get boy keys as list."""
        return json.loads(self.boy_keys) if self.boy_keys else []
    
    @boy_keys_list.setter
    def boy_keys_list(self, keys: List[str]):
        """Set boy keys from list."""
        self.boy_keys = json.dumps(keys)
    
    @property
    def girl_keys_list(self) -> List[str]:
        """Get girl keys as list."""
        return json.loads(self.girl_keys) if self.girl_keys else []
    
    @girl_keys_list.setter
    def girl_keys_list(self, keys: List[str]):
        """Set girl keys from list."""
        self.girl_keys = json.dumps(keys)
    
    @property
    def tags_list(self) -> List[str]:
        """Get tags as list."""
        return json.loads(self.tags) if self.tags else []
    
    @tags_list.setter
    def tags_list(self, tags: List[str]):
        """Set tags from list."""
        self.tags = json.dumps(tags)

    def __repr__(self) -> str:
        return f"<Song(id={self.song_id}, title='{self.title}', artist='{self.artist}')>"


class Lyrics(Base):
    """Song lyrics table with key sections."""
    __tablename__ = 'lyrics'
    
    lyrics_id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(Integer, ForeignKey('songs.song_id'), nullable=False)
    first_line = Column(Text)  # Opening line of the song
    chorus = Column(Text)      # Main chorus section
    bridge = Column(Text)      # Bridge section
    language = Column(String, default='en')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    song = relationship("Song", back_populates="lyrics")
    
    @property
    def combined_content(self) -> str:
        """Get all lyrical content combined for search purposes."""
        content_parts = []
        if self.first_line:
            content_parts.append(self.first_line)
        if self.chorus:
            content_parts.append(self.chorus)
        if self.bridge:
            content_parts.append(self.bridge)
        return " | ".join(content_parts)
    
    def __repr__(self) -> str:
        return f"<Lyrics(id={self.lyrics_id}, song_id={self.song_id}, sections={bool(self.first_line or self.chorus or self.bridge)})>"


class UserFeedback(Base):
    """User feedback and interaction tracking."""
    __tablename__ = 'user_feedback'
    
    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    user_id = Column(String, nullable=False)
    session_id = Column(String)
    song_id = Column(Integer, ForeignKey('songs.song_id'), nullable=False)
    action = Column(String, nullable=False)  # 'thumbs_up', 'thumbs_down', 'used'
    context_keywords = Column(Text)  # JSON array of search terms
    search_params = Column(Text)  # JSON: original search query context
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    song = relationship("Song", back_populates="feedback")
    
    @property
    def context_keywords_list(self) -> List[str]:
        """Get context keywords as list."""
        return json.loads(self.context_keywords) if self.context_keywords else []
    
    @context_keywords_list.setter
    def context_keywords_list(self, keywords: List[str]):
        """Set context keywords from list."""
        self.context_keywords = json.dumps(keywords)
    
    @property
    def search_params_dict(self) -> Dict:
        """Get search params as dictionary."""
        return json.loads(self.search_params) if self.search_params else {}
    
    @search_params_dict.setter
    def search_params_dict(self, params: Dict):
        """Set search params from dictionary."""
        self.search_params = json.dumps(params)

    def __repr__(self) -> str:
        return f"<UserFeedback(id={self.feedback_id}, user_id='{self.user_id}', action='{self.action}')>"


class SongUsage(Base):
    """Track song usage at church for familiarity scoring."""
    __tablename__ = 'song_usage'
    
    usage_id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(Integer, ForeignKey('songs.song_id'), nullable=False)
    used_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    service_type = Column(String, default='worship')  # 'worship', 'youth', 'special', etc.
    notes = Column(String)  # Optional context: "altar call", "opening", etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    song = relationship("Song", back_populates="usage_history")
    
    def __repr__(self) -> str:
        return f"<SongUsage(id={self.usage_id}, song_id={self.song_id}, date={self.used_date.strftime('%Y-%m-%d')})>"


class ThemeMapping(Base):
    """Song theme/tag mappings for semantic search."""
    __tablename__ = 'theme_mappings'
    
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(Integer, ForeignKey('songs.song_id'), nullable=False)
    theme_name = Column(String, nullable=False)
    confidence_score = Column(REAL, default=1.0)  # For ML-based themes later
    source = Column(String, default='manual')  # 'manual', 'ml', 'user_feedback'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    song = relationship("Song", back_populates="themes")

    def __repr__(self) -> str:
        return f"<ThemeMapping(id={self.mapping_id}, song_id={self.song_id}, theme='{self.theme_name}')>"


class MessageLog(Base):
    """Log all bot interactions for analytics."""
    __tablename__ = 'message_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(String, nullable=False)  # Hashed for privacy
    message_type = Column(String, nullable=False)  # 'search', 'more', 'feedback', 'unknown'
    message_content = Column(Text, nullable=False)  # User's message
    response_content = Column(Text, nullable=False)  # Bot's response
    session_context = Column(Text)  # JSON: session state for analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<MessageLog(id={self.log_id}, user_id='{self.user_id}', type='{self.message_type}')>"