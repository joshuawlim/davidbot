"""Session manager with 60-minute TTL."""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from .models import UserSession, SearchResult


class SessionManager:
    """Manages user sessions with 60-minute TTL."""
    
    def __init__(self):
        """Initialize with empty session store.""" 
        self.sessions: Dict[str, UserSession] = {}
        self.session_ttl_minutes = 60
    
    def get_session(self, user_id: str) -> Optional[UserSession]:
        """Get user session if it exists and hasn't expired."""
        if user_id not in self.sessions:
            return None
            
        session = self.sessions[user_id]
        
        # Check if session has expired
        if self._is_session_expired(session):
            del self.sessions[user_id]
            return None
            
        return session
    
    def create_or_update_session(self, user_id: str, search_result: Optional[SearchResult] = None) -> UserSession:
        """Create new session or update existing one.""" 
        now = datetime.now()
        
        if user_id in self.sessions:
            # Update existing session
            session = self.sessions[user_id]
            session.last_activity = now
            
            if search_result:
                session.last_search = search_result
                # Reset returned songs for new search
                session.returned_songs = [song.title for song in search_result.songs]
        else:
            # Create new session
            returned_songs = [song.title for song in search_result.songs] if search_result else []
            session = UserSession(
                user_id=user_id,
                last_search=search_result,
                last_activity=now,
                returned_songs=returned_songs
            )
            self.sessions[user_id] = session
            
        return session
    
    def update_session_activity(self, user_id: str) -> Optional[UserSession]:
        """Update session activity timestamp."""
        session = self.get_session(user_id)
        if session:
            session.last_activity = datetime.now()
        return session
    
    def add_returned_songs_to_session(self, user_id: str, song_titles: List[str]) -> None:
        """Add song titles to the list of already returned songs.""" 
        session = self.get_session(user_id)
        if session:
            session.returned_songs.extend(song_titles)
    
    def _is_session_expired(self, session: UserSession) -> bool:
        """Check if session has expired (60+ minutes of inactivity)."""
        now = datetime.now()
        expiry_time = session.last_activity + timedelta(minutes=self.session_ttl_minutes)
        return now >= expiry_time
    
    def cleanup_expired_sessions(self) -> None:
        """Remove all expired sessions from memory."""
        expired_user_ids = []
        
        for user_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_user_ids.append(user_id)
        
        for user_id in expired_user_ids:
            del self.sessions[user_id]