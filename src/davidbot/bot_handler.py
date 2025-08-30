"""Bot handler for Telegram integration."""

import re
import logging
from datetime import datetime
from typing import Optional

from .models import MessageLog, FeedbackEvent
from .recommendation_engine import RecommendationEngine  
from .response_formatter import ResponseFormatter
from .session_manager import SessionManager
from .sheets_client import SheetsClient


logger = logging.getLogger(__name__)


class BotHandler:
    """Main bot handler class that integrates all components."""
    
    def __init__(self, sheets_client: Optional[SheetsClient] = None):
        """Initialize bot handler with dependencies."""
        self.recommendation_engine = RecommendationEngine()
        self.response_formatter = ResponseFormatter()
        self.session_manager = SessionManager()
        self.sheets_client = sheets_client or SheetsClient()
    
    async def handle_message(self, user_id: str, message: str) -> str:
        """Handle incoming messages from users."""
        try:
            # Determine message type and route to appropriate handler
            message_lower = message.lower().strip()
            
            if self._is_search_query(message_lower):
                response = await self._handle_search(user_id, message)
                message_type = "search"
            elif message_lower == "more":
                response = await self._handle_more_request(user_id, message)
                message_type = "more"
            elif self._is_feedback(message):
                response = await self._handle_feedback(user_id, message)
                message_type = "feedback"
            else:
                response = "I can help you find songs. Try: 'find songs on surrender' or say 'more' for additional songs."
                message_type = "unknown"
            
            # Log the interaction (graceful failure)
            await self._log_message(user_id, message_type, message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message from {user_id}: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def _is_search_query(self, message: str) -> bool:
        """Check if message is a song search query."""
        search_patterns = [
            "find songs",
            "search for songs", 
            "songs on",
            "songs about",
            "songs with"
        ]
        return any(pattern in message for pattern in search_patterns)
    
    def _is_feedback(self, message: str) -> bool:
        """Check if message is feedback (👍 followed by number)."""
        return message.strip().startswith('👍')
    
    async def _handle_search(self, user_id: str, message: str) -> str:
        """Handle song search requests.""" 
        # Search for songs
        search_result = self.recommendation_engine.search(message)
        
        if not search_result:
            return "No songs found for your search. Try different terms like 'surrender', 'worship', or 'grace'."
        
        # Update user session
        self.session_manager.create_or_update_session(user_id, search_result)
        
        # Format response
        return self.response_formatter.format_search_result(search_result)
    
    async def _handle_more_request(self, user_id: str, message: str) -> str:
        """Handle requests for more songs."""
        # Get current session
        session = self.session_manager.get_session(user_id)
        
        if not session or not session.last_search:
            return self.response_formatter.format_no_previous_search_message()
        
        # Search for more songs, excluding already returned ones
        search_result = self.recommendation_engine.search(
            f"find songs on {session.last_search.theme}",
            excluded_songs=session.returned_songs
        )
        
        if not search_result or not search_result.songs:
            return f"No more songs found for '{session.last_search.theme}'."
        
        # Update session with new songs
        new_song_titles = [song.title for song in search_result.songs]
        self.session_manager.add_returned_songs_to_session(user_id, new_song_titles)
        self.session_manager.update_session_activity(user_id)
        
        # Format response
        return self.response_formatter.format_search_result(search_result)
    
    async def _handle_feedback(self, user_id: str, message: str) -> str:
        """Handle user feedback on songs."""
        # Extract song position from feedback
        match = re.match(r'👍\s*([123])', message.strip())
        if not match:
            return self.response_formatter.format_invalid_feedback_message()
        
        song_position = int(match.group(1))
        
        # Check if user has active session with songs
        session = self.session_manager.get_session(user_id)
        if not session or not session.last_search:
            return self.response_formatter.format_no_feedback_context_message()
        
        # Determine which song user is providing feedback on
        if song_position > len(session.last_search.songs):
            return self.response_formatter.format_invalid_feedback_message()
        
        song = session.last_search.songs[song_position - 1]
        
        # Create feedback event
        feedback_event = FeedbackEvent(
            user_id=user_id,
            song_position=song_position,
            feedback_type="thumbs_up",
            timestamp=datetime.now(),
            song_title=song.title
        )
        
        # Log feedback (graceful failure)
        await self._log_feedback(feedback_event)
        
        # Update session activity
        self.session_manager.update_session_activity(user_id)
        
        return self.response_formatter.format_feedback_confirmation(song_position)
    
    async def _log_message(self, user_id: str, message_type: str, message_content: str, response_content: str) -> None:
        """Log message interaction to sheets."""
        try:
            message_log = MessageLog(
                user_id=user_id,
                message_type=message_type, 
                message_content=message_content,
                response_content=response_content,
                timestamp=datetime.now()
            )
            await self.sheets_client.log_message(message_log)
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
            # Graceful degradation - don't let logging failures affect user experience
    
    async def _log_feedback(self, feedback_event: FeedbackEvent) -> None:
        """Log feedback event to sheets."""
        try:
            await self.sheets_client.log_feedback(feedback_event)
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
            # Graceful degradation - don't let logging failures affect user experience