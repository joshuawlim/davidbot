"""Bot handler for Telegram integration."""

import re
import logging
import asyncio
import ssl
from datetime import datetime
from typing import Optional, List, Union
import aiohttp

from .models import FeedbackEvent
from .database_recommendation_engine import create_recommendation_engine
from .response_formatter import ResponseFormatter
from .session_manager import SessionManager
from .database import get_db_session, MessageLogRepository, FeedbackRepository, SongRepository, Song


logger = logging.getLogger(__name__)


class BotHandler:
    """Main bot handler class that integrates all components."""
    
    def __init__(self):
        """Initialize bot handler with dependencies."""
        self.recommendation_engine = create_recommendation_engine()
        self.response_formatter = ResponseFormatter()
        self.session_manager = SessionManager()
        
        # Log recommendation engine status
        if hasattr(self.recommendation_engine, 'health_check'):
            health = self.recommendation_engine.health_check()
            logger.info(f"Recommendation engine status: {health.get('status', 'unknown')} "
                       f"({health.get('song_count', 0)} songs, {health.get('theme_count', 0)} themes)")
    
    async def handle_message(self, user_id: str, message: str) -> Union[str, List[str]]:
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
            if isinstance(response, list):
                # For multiple messages, log as combined for now
                combined_response = "\n---\n".join(response)
                await self._log_message(user_id, message_type, message, combined_response)
            else:
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
        """Check if message is feedback (👍 emoji reaction or text)."""
        message_cleaned = message.strip()
        return (message_cleaned.startswith('👍') or 
                message_cleaned == '👍' or
                'thumbs up' in message_cleaned.lower())
    
    async def _handle_search(self, user_id: str, message: str) -> List[str]:
        """Handle song search requests.""" 
        # Search for songs
        search_result = self.recommendation_engine.search(message)
        
        if not search_result:
            return ["No songs found for your search. Try different terms like 'surrender', 'worship', or 'grace'."]
        
        # Update user session
        self.session_manager.create_or_update_session(user_id, search_result)
        
        # Format response as individual messages
        return self.response_formatter.format_individual_songs(search_result)
    
    async def _handle_more_request(self, user_id: str, message: str) -> List[str]:
        """Handle requests for more songs."""
        # Check if user ever had a session (even if expired)
        had_session_before = user_id in self.session_manager.sessions
        
        # Get current session (will return None if expired)
        session = self.session_manager.get_session(user_id)
        
        if not session or not session.last_search:
            # Distinguish between "never searched" and "session expired"
            if had_session_before:
                return [self.response_formatter.format_session_expired_message()]
            else:
                return [self.response_formatter.format_no_previous_search_message()]
        
        # Search for more songs, excluding already returned ones
        search_result = self.recommendation_engine.search(
            f"find songs on {session.last_search.theme}",
            excluded_songs=session.returned_songs
        )
        
        if not search_result or not search_result.songs:
            return [f"No more songs found for '{session.last_search.theme}'."]
        
        # Update session with new songs
        new_song_titles = [song.title for song in search_result.songs]
        self.session_manager.add_returned_songs_to_session(user_id, new_song_titles)
        self.session_manager.update_session_activity(user_id)
        
        # Format response as individual messages
        return self.response_formatter.format_individual_songs(search_result)
    
    async def _handle_feedback(self, user_id: str, message: str) -> str:
        """Handle user feedback on songs."""
        # Parse feedback message to extract song position
        import re
        
        # Check if user has active session with songs
        session = self.session_manager.get_session(user_id)
        if not session or not session.last_search:
            return self.response_formatter.format_no_feedback_context_message()
        
        # Extract song position from message like "👍 1", "👍 2", etc.
        message_clean = message.strip()
        position_match = re.search(r'👍\s*(\d+)', message_clean)
        
        if position_match:
            # Specific song feedback
            song_position = int(position_match.group(1))
            
            # Validate position (1-based, should be within number of returned songs)
            num_songs = len(session.last_search.songs) if session.last_search else 0
            if song_position < 1 or song_position > num_songs:
                return self.response_formatter.format_invalid_feedback_message()
            
            # Get song title for the specified position (convert to 0-based index)
            song_title = session.last_search.songs[song_position - 1].title
        else:
            # No position specified - this should be invalid per test requirements
            # Only numbered feedback (👍 1, 👍 2, 👍 3) should be valid
            return self.response_formatter.format_invalid_feedback_message()
        
        # Create feedback event
        feedback_event = FeedbackEvent(
            user_id=user_id,
            song_position=song_position,
            feedback_type="thumbs_up", 
            timestamp=datetime.now(),
            song_title=song_title
        )
        
        # Log feedback (graceful failure)
        await self._log_feedback(feedback_event)
        
        # Update session activity
        self.session_manager.update_session_activity(user_id)
        
        # Return confirmation (song_position is guaranteed to be > 0 at this point)
        return self.response_formatter.format_feedback_confirmation(song_position)
    
    async def _log_message(self, user_id: str, message_type: str, message_content: str, response_content: str) -> None:
        """Log message interaction to database."""
        try:
            with get_db_session() as session:
                message_repo = MessageLogRepository(session)
                log_data = {
                    'user_id': user_id,
                    'message_type': message_type,
                    'message_content': message_content,
                    'response_content': response_content,
                    'timestamp': datetime.now()
                }
                message_repo.create(log_data)
        except Exception as e:
            logger.error(f"Failed to log message: {e}")
            # Graceful degradation - don't let logging failures affect user experience
    
    async def _log_feedback(self, feedback_event: FeedbackEvent) -> None:
        """Log feedback event to database."""
        try:
            with get_db_session() as session:
                feedback_repo = FeedbackRepository(session)
                song_repo = SongRepository(session)
                
                # Find the song by title to get song_id
                # feedback_event.song_title contains just the title from session
                song_title = feedback_event.song_title
                song = session.query(Song).filter(Song.title == song_title).first()
                
                if song:
                    feedback_data = {
                        'timestamp': feedback_event.timestamp,
                        'user_id': feedback_event.user_id,
                        'song_id': song.song_id,
                        'action': feedback_event.feedback_type,
                        'context_keywords': '[]',  # Empty for now, could be enhanced later
                        'search_params': '{}'  # Empty for now, could be enhanced later
                    }
                    feedback_repo.create(feedback_data)
                else:
                    logger.warning(f"Could not find song for feedback: {feedback_event.song_title}")
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
            # Graceful degradation - don't let logging failures affect user experience

    async def start_polling(self, telegram_token: str) -> None:
        """Start Telegram long polling to receive and handle messages."""
        api_url = f"https://api.telegram.org/bot{telegram_token}"
        offset = 0
        
        logger.info("Starting Telegram long polling...")
        
        # Create SSL context - disable verification for development/corporate networks
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create connector with SSL handling
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            while True:
                try:
                    # Get updates using long polling
                    async with session.get(
                        f"{api_url}/getUpdates",
                        params={"offset": offset, "timeout": 30}
                    ) as response:
                        if response.status != 200:
                            logger.error(f"Failed to get updates: {response.status}")
                            await asyncio.sleep(5)
                            continue
                        
                        data = await response.json()
                        
                        if not data.get("ok"):
                            logger.error(f"Telegram API error: {data}")
                            await asyncio.sleep(5)
                            continue
                        
                        updates = data.get("result", [])
                        
                        for update in updates:
                            offset = max(offset, update["update_id"] + 1)
                            
                            # Process message updates
                            if "message" in update and "text" in update["message"]:
                                message = update["message"]
                                user_id = str(message["from"]["id"])
                                chat_id = message["chat"]["id"]
                                text = message["text"]
                                
                                logger.info(f"Received message from {user_id}: {text}")
                                
                                # Handle the message
                                response = await self.handle_message(user_id, text)
                                
                                # Send response(s) back to user
                                if isinstance(response, list):
                                    # Send individual messages for search results
                                    for message_text in response:
                                        await self._send_message(session, api_url, chat_id, message_text)
                                else:
                                    # Send single message for other responses
                                    await self._send_message(session, api_url, chat_id, response)
                
                except asyncio.CancelledError:
                    logger.info("Polling cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    await asyncio.sleep(5)
    
    async def _send_message(self, session: aiohttp.ClientSession, api_url: str, chat_id: int, text: str) -> None:
        """Send a message via Telegram API."""
        try:
            async with session.post(
                f"{api_url}/sendMessage",
                json={
                    "chat_id": chat_id, 
                    "text": text,
                    "link_preview_options": {"is_disabled": True}
                }
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to send message: {response.status}")
                else:
                    logger.info("Message sent successfully")
        except Exception as e:
            logger.error(f"Error sending message: {e}")