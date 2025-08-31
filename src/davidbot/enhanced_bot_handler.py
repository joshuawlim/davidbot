"""Enhanced bot handler with natural language processing and conversational context."""

import os
import ssl
import logging
import asyncio
import aiohttp
from typing import Optional, List, Union, Dict, Any
from datetime import datetime, timedelta

from .llm_query_parser import LLMQueryParser, MockLLMQueryParser, ParsedQuery
from .enhanced_recommendation_engine import EnhancedRecommendationEngine
from .database_recommendation_engine import create_recommendation_engine
from .response_formatter import ResponseFormatter
from .session_manager import SessionManager
from .models import FeedbackEvent
from .database import get_db_session, MessageLogRepository, FeedbackRepository, SongRepository, Song

logger = logging.getLogger(__name__)


class ConversationContext:
    """Manages conversational context across messages."""
    
    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.ttl_minutes = 60  # Context expires after 60 minutes
    
    def update_context(self, user_id: str, context_data: Dict[str, Any]):
        """Update conversation context for a user."""
        self.contexts[user_id] = {
            **context_data,
            'last_updated': datetime.now()
        }
    
    def get_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current conversation context for a user."""
        if user_id not in self.contexts:
            return None
        
        context = self.contexts[user_id]
        if datetime.now() - context['last_updated'] > timedelta(minutes=self.ttl_minutes):
            del self.contexts[user_id]
            return None
        
        return context
    
    def clear_context(self, user_id: str):
        """Clear conversation context for a user."""
        self.contexts.pop(user_id, None)


class EnhancedBotHandler:
    """Enhanced bot handler with natural language processing and conversational intelligence."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", use_mock_llm: bool = False):
        """Initialize enhanced bot handler."""
        # Core components
        self.database_engine = create_recommendation_engine()
        self.enhanced_engine = EnhancedRecommendationEngine(self.database_engine)
        self.response_formatter = ResponseFormatter()
        self.session_manager = SessionManager()
        self.conversation_context = ConversationContext()
        self.shutdown_requested = False
        
        # LLM setup
        if use_mock_llm:
            logger.info("Using mock LLM parser (no API calls)")
            self.query_parser = MockLLMQueryParser()
        else:
            logger.info("Using Ollama LLM parser with gpt-oss:latest")
            self.query_parser = LLMQueryParser(ollama_url)
        
        # Log status
        health = self.enhanced_engine.health_check()
        logger.info(f"Enhanced bot handler initialized - {health.get('song_count', 0)} songs, "
                   f"{health.get('theme_count', 0)} themes")
    
    def shutdown(self):
        """Request graceful shutdown of the bot handler."""
        logger.info("Shutdown requested for enhanced bot handler")
        self.shutdown_requested = True
    
    async def handle_message(self, user_id: str, message: str) -> Union[str, List[str]]:
        """Handle incoming messages with natural language processing."""
        try:
            start_time = datetime.now()
            
            # Pre-process: Handle greetings and commands before LLM parsing
            # This ensures /start and other greetings are caught immediately
            if self._is_greeting(message):
                response = await self._handle_greeting(user_id, message)
                message_type = "greeting"
                parsed_query = None  # No need to parse greetings
            else:
                # Get conversation context
                context = self.conversation_context.get_context(user_id)
                
                # Parse the message using LLM
                parsed_query = await self.query_parser.parse(message, context)
                
                logger.info(f"Parsed query - intent: {parsed_query.intent}, themes: {parsed_query.themes}, "
                           f"confidence: {parsed_query.confidence}")
                
                # Route based on intent
                if parsed_query.intent == "search":
                    response = await self._handle_natural_search(user_id, parsed_query)
                    message_type = "search"
                elif parsed_query.intent == "more":
                    response = await self._handle_more_request(user_id, parsed_query)
                    message_type = "more"
                elif parsed_query.intent == "feedback":
                    response = await self._handle_feedback(user_id, message)
                    message_type = "feedback"
                elif self._is_direct_feedback(message):
                    # Fallback feedback detection
                    response = await self._handle_feedback(user_id, message)
                    message_type = "feedback"
                else:
                    response = await self._handle_unknown_query(user_id, parsed_query)
                    message_type = "unknown"
            
            # Update conversation context (only if we have a parsed query)
            if parsed_query:
                self._update_conversation_context(user_id, parsed_query, response)
            
            # Log the interaction
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_enhanced_message(user_id, message_type, message, response, 
                                           parsed_query, processing_time)
            
            logger.info(f"Message processed in {processing_time:.0f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error handling enhanced message from {user_id}: {e}")
            return "Sorry, I encountered an error processing your request. Please try again."
    
    async def _handle_natural_search(self, user_id: str, parsed_query: ParsedQuery) -> List[str]:
        """Handle natural language search requests."""
        # Get excluded songs from session
        session = self.session_manager.get_session(user_id)
        excluded_songs = session.returned_songs if session else []
        
        # Search using enhanced engine
        search_result = self.enhanced_engine.search_with_parsed_query(parsed_query, excluded_songs)
        
        if not search_result or not search_result.songs:
            # Try fallback with more general themes
            if parsed_query.themes:
                fallback_query = f"find songs on {' '.join(parsed_query.themes[:2])}"
                search_result = self.database_engine.search(fallback_query, excluded_songs)
        
        if not search_result or not search_result.songs:
            return [self._create_no_results_message(parsed_query)]
        
        # Update user session
        self.session_manager.create_or_update_session(user_id, search_result)
        
        # Format response with worship leader context
        return self._format_enhanced_response(search_result, parsed_query)
    
    async def _handle_more_request(self, user_id: str, parsed_query: ParsedQuery) -> List[str]:
        """Handle requests for more songs with context awareness."""
        session = self.session_manager.get_session(user_id)
        
        if not session or not session.last_search:
            context = self.conversation_context.get_context(user_id)
            if context and context.get('last_themes'):
                # Use conversation context to recreate search
                parsed_query.themes = context['last_themes']
                return await self._handle_natural_search(user_id, parsed_query)
            else:
                return ["I don't have a previous search to build on. Try something like 'find songs on worship'."]
        
        # Continue with previous search context
        more_result = self.enhanced_engine.search_with_parsed_query(
            ParsedQuery(
                themes=session.last_search.theme.split(', '),
                raw_query=parsed_query.raw_query
            ),
            excluded_songs=session.returned_songs
        )
        
        if not more_result or not more_result.songs:
            return [f"No more songs found for '{session.last_search.theme}'."]
        
        # Update session
        new_song_titles = [song.title for song in more_result.songs]
        self.session_manager.add_returned_songs_to_session(user_id, new_song_titles)
        self.session_manager.update_session_activity(user_id)
        
        return self.response_formatter.format_individual_songs(more_result)
    
    async def _handle_feedback(self, user_id: str, message: str) -> str:
        """Handle feedback with enhanced context awareness."""
        # Use original feedback handling for now
        # TODO: Could enhance with LLM understanding of "that second one was perfect"
        import re
        
        session = self.session_manager.get_session(user_id)
        if not session or not session.last_search:
            return "I need to search for songs first before I can record feedback."
        
        # Enhanced feedback parsing
        message_clean = message.strip().lower()
        
        # Handle natural feedback like "the second one" or "song 2"
        patterns = [
            r'👍\s*(\d+)',  # "👍 2"
            r'(?:the\s+)?(?:second|2nd|third|3rd|first|1st)\s+(?:one|song)',  # "the second one"
            r'(?:song|number)\s*(\d+)',  # "song 2"
        ]
        
        position = None
        for pattern in patterns:
            match = re.search(pattern, message_clean)
            if match:
                if 'second' in message_clean or '2nd' in message_clean:
                    position = 2
                elif 'third' in message_clean or '3rd' in message_clean:
                    position = 3
                elif 'first' in message_clean or '1st' in message_clean:
                    position = 1
                elif match.groups():
                    position = int(match.group(1))
                break
        
        if not position:
            return "Please specify which song you liked (e.g., '👍 2' or 'the second one was perfect')."
        
        # Validate position
        num_songs = len(session.last_search.songs) if session.last_search else 0
        if position < 1 or position > num_songs:
            return f"Please choose a number between 1 and {num_songs}."
        
        # Create feedback event
        song_title = session.last_search.songs[position - 1].title
        feedback_event = FeedbackEvent(
            user_id=user_id,
            song_position=position,
            feedback_type="thumbs_up",
            timestamp=datetime.now(),
            song_title=song_title
        )
        
        # Log feedback
        await self._log_feedback(feedback_event)
        
        # Update session activity
        self.session_manager.update_session_activity(user_id)
        
        return f"Thanks! I've noted that you liked '{song_title}'. This helps me learn your preferences."
    
    async def _handle_unknown_query(self, user_id: str, parsed_query: ParsedQuery) -> str:
        """Handle queries that couldn't be understood."""
        if parsed_query.confidence < 0.3:
            return (
                "I'm not sure what you're looking for. Try something like:\n"
                "• 'Find songs on surrender'\n"
                "• 'Upbeat songs for celebration'\n"
                "• 'Songs like Amazing Grace'\n"
                "• 'More songs' (after a search)"
            )
        else:
            # Try to be helpful based on what we understood
            if parsed_query.themes:
                return f"I understood you're looking for songs about {', '.join(parsed_query.themes)}, but I need a clearer request. Try 'find songs on {parsed_query.themes[0]}'."
            else:
                return "Could you rephrase that? I help find worship songs - try 'find songs on [theme]'."
    
    def _update_conversation_context(self, user_id: str, parsed_query: ParsedQuery, response: Union[str, List[str]]):
        """Update conversation context based on interaction."""
        context_data = {
            'last_themes': parsed_query.themes,
            'last_intent': parsed_query.intent,
            'last_query': parsed_query.raw_query,
            'response_type': 'list' if isinstance(response, list) else 'string'
        }
        
        if parsed_query.bpm_min or parsed_query.bpm_max:
            context_data['bpm_preference'] = {
                'min': parsed_query.bpm_min,
                'max': parsed_query.bpm_max
            }
        
        self.conversation_context.update_context(user_id, context_data)
    
    def _is_direct_feedback(self, message: str) -> bool:
        """Check if message is direct feedback (emoji or explicit)."""
        message_cleaned = message.strip().lower()
        return (message_cleaned.startswith('👍') or 
                message_cleaned == '👍' or
                'thumbs up' in message_cleaned or
                'perfect' in message_cleaned or
                'loved' in message_cleaned)
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting."""
        message_cleaned = message.strip().lower()
        
        # Exact greeting matches
        exact_greetings = [
            'hi', 'hello', 'hey', 'hiya', 'howdy', 'greetings',
            'hi davidbot', 'hello davidbot', 'hey davidbot',
            'good morning', 'good afternoon', 'good evening',
            'start', '/start', 'begin'
        ]
        
        # Check for exact matches first
        if message_cleaned in exact_greetings:
            return True
            
        # Check if it starts with a greeting and is short (likely just a greeting)
        words = message_cleaned.split()
        if len(words) <= 2:
            greeting_starters = ['hi', 'hello', 'hey', 'hiya', 'howdy']
            if any(message_cleaned.startswith(starter) for starter in greeting_starters):
                return True
        
        # Check for "good [time]" patterns specifically
        if len(words) == 2 and words[0] == 'good' and words[1] in ['morning', 'afternoon', 'evening', 'night']:
            return True
            
        return False
    
    async def _handle_greeting(self, user_id: str, message: str) -> str:
        """Handle greeting messages with warm, ministry-focused welcome."""
        # Vary responses to keep it conversational
        import random
        
        welcoming_intros = [
            "Hello! I'm DavidBot, an MD assistant. 🎵",
            "Hi there! 🙏",  
            "Hey! I'm here to help you find songs from the list. ✨",
            "Welcome! I'm David - think of me as your worship planning companion. 🎶",
            "Hello! Got a question? 🕊️"
        ]
        
        capability_explanations = [
            "I can help you find songs in natural language - just tell me what you're looking for:",
            "Here's how I can serve your ministry:",
            "I'm equipped to help you find songs for any worship moment:",
            "Let me share what I can do for your worship planning:",
        ]
        
        examples = [
            "• \"Find slow songs about surrender for altar call\"",
            "• \"I need upbeat celebration songs for baptism Sunday\"", 
            "• \"Songs like Amazing Grace but more contemporary\"",
            "• \"Show me songs on God's love in the key of G\"",
            "• \"What do you have for youth service - something energetic?\"",
            "• \"I need ministry songs under 80 BPM for healing prayer\""
        ]
        
        # Build response
        intro = random.choice(welcoming_intros)
        explanation = random.choice(capability_explanations)
        
        # Select 3 random examples
        selected_examples = random.sample(examples, 3)
        examples_text = "\n".join(selected_examples)
        
        response = f"""{intro}

{explanation}

{examples_text}

I understand ministry context, BPM preferences, keys, and can suggest songs for specific moments like altar calls, celebration, or quiet worship. I also learn from your feedback to get better at helping you!

What kind of songs are you looking for today?"""
        
        return response
    
    def _create_no_results_message(self, parsed_query: ParsedQuery) -> str:
        """Create helpful no-results message with adjacent theme suggestions."""
        if parsed_query.themes:
            themes_str = ', '.join(parsed_query.themes[:2])
            
            # Map themes to adjacent/related themes for better suggestions
            theme_suggestions = {
                'joy': ['celebration', 'praise', 'thanksgiving'],
                'peace': ['rest', 'comfort', 'calm'],
                'love': ['grace', 'mercy', 'compassion'],
                'strength': ['power', 'courage', 'victory'],
                'healing': ['restoration', 'breakthrough', 'hope'],
                'faith': ['trust', 'confidence', 'hope'],
                'hope': ['faith', 'trust', 'future'],
                'salvation': ['redemption', 'grace', 'cross'],
                'worship': ['praise', 'adoration', 'reverence'],
                'praise': ['worship', 'celebration', 'thanksgiving']
            }
            
            # Find suggestions for the first theme
            first_theme = parsed_query.themes[0].lower()
            suggestions = theme_suggestions.get(first_theme, ['worship', 'praise', 'grace'])
            suggestions_str = ', '.join(suggestions)
            
            return (f"I couldn't find any songs about {themes_str}. "
                   f"Here are some suggestions on {suggestions_str} - does that help?")
        else:
            return "No songs found. Try something like 'find songs on surrender' or 'worship songs'."
    
    def _format_enhanced_response(self, search_result, parsed_query: ParsedQuery) -> List[str]:
        """Format response with worship leader ministry context."""
        # Use existing formatter as base
        responses = self.response_formatter.format_individual_songs(search_result)
        
        # Add intro that acknowledges what the user actually searched for
        intro = self._get_search_acknowledgment_intro(parsed_query, search_result)
        if intro:
            responses.insert(0, intro)
        
        return responses
    
    def _get_ministry_intro(self, parsed_query: ParsedQuery) -> Optional[str]:
        """Generate ministry-appropriate intro based on query context."""
        themes = [theme.lower() for theme in parsed_query.themes]
        mood = parsed_query.mood
        
        # Altar call / Ministry moments
        if mood in ["contemplative", "ministry"] or any(t in ["surrender", "grace", "mercy", "healing", "salvation", "repentance"] for t in themes):
            return "For this season of ministry:"
        
        # Celebration / Praise
        elif mood == "upbeat" or any(t in ["celebration", "joy", "praise", "victory", "breakthrough", "testimony"] for t in themes):
            return "These songs invite celebration:"
        
        # Worship / Adoration
        elif any(t in ["worship", "adoration", "holy", "presence", "majesty", "glory"] for t in themes):
            return "To draw near in worship:"
        
        # Faith building / Encouragement  
        elif any(t in ["faith", "trust", "hope", "strength", "courage", "overcome"] for t in themes):
            return "Songs that build faith:"
        
        # Love / Relationship with God
        elif any(t in ["love", "beloved", "intimacy", "friend", "father"] for t in themes):
            return "Songs of God's love:"
        
        # Default for general searches
        elif len(themes) > 0:
            return f"Songs for your search on {', '.join(themes[:2])}:"
        
        return None
    
    def _get_search_acknowledgment_intro(self, parsed_query: ParsedQuery, search_result) -> Optional[str]:
        """Generate intro that acknowledges what the user actually searched for."""
        if not parsed_query.themes:
            return None
            
        # Get the actual themes the user searched for
        user_themes = parsed_query.themes
        themes_text = ', '.join(user_themes)
        
        # Check if we found songs for their search
        if search_result and search_result.songs:
            # We found songs for their search
            if len(user_themes) == 1:
                return f"Here are some songs about {user_themes[0]}:"
            else:
                return f"Here are some songs about {themes_text}:"
        else:
            # We didn't find exact matches - this is handled by no_results flow
            return None
    
    async def _log_enhanced_message(self, user_id: str, message_type: str, message_content: str,
                                   response_content: Union[str, List[str]], parsed_query: Optional[ParsedQuery],
                                   processing_time: float) -> None:
        """Log enhanced message with LLM parsing metadata."""
        try:
            with get_db_session() as session:
                message_repo = MessageLogRepository(session)
                
                # Prepare metadata (handle None parsed_query for greetings)
                if parsed_query:
                    llm_metadata = {
                        'themes': parsed_query.themes,
                        'intent': parsed_query.intent,
                        'confidence': parsed_query.confidence,
                        'bpm_range': f"{parsed_query.bpm_min or ''}-{parsed_query.bpm_max or ''}",
                        'processing_time_ms': processing_time
                    }
                else:
                    # For greetings and commands that bypass LLM parsing
                    llm_metadata = {
                        'themes': [],
                        'intent': message_type,
                        'confidence': 1.0,
                        'bpm_range': '',
                        'processing_time_ms': processing_time
                    }
                
                # Format response content
                if isinstance(response_content, list):
                    combined_response = "\n---\n".join(response_content)
                else:
                    combined_response = response_content
                
                log_data = {
                    'user_id': user_id,
                    'message_type': message_type,
                    'message_content': message_content,
                    'response_content': combined_response,
                    'timestamp': datetime.now(),
                    'session_context': str(llm_metadata)  # Store LLM metadata as JSON string
                }
                message_repo.create(log_data)
                
        except Exception as e:
            logger.error(f"Failed to log enhanced message: {e}")
    
    async def _log_feedback(self, feedback_event: FeedbackEvent) -> None:
        """Log feedback event (reuse from original handler)."""
        try:
            with get_db_session() as session:
                feedback_repo = FeedbackRepository(session)
                song = session.query(Song).filter(Song.title == feedback_event.song_title).first()
                
                if song:
                    feedback_data = {
                        'timestamp': feedback_event.timestamp,
                        'user_id': feedback_event.user_id,
                        'song_id': song.song_id,
                        'action': feedback_event.feedback_type,
                        'context_keywords': '[]',
                        'search_params': '{}'
                    }
                    feedback_repo.create(feedback_data)
                else:
                    logger.warning(f"Could not find song for feedback: {feedback_event.song_title}")
                    
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
    
    async def start_polling(self, telegram_token: str) -> None:
        """Start Telegram long polling to receive and handle messages."""
        api_url = f"https://api.telegram.org/bot{telegram_token}"
        offset = 0
        
        logger.info("Starting Telegram long polling with enhanced bot handler...")
        
        # Create SSL context - disable verification for development/corporate networks
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create connector with SSL handling
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            while not self.shutdown_requested:
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
                                
                                # Handle the message with enhanced processing
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
                    logger.info("Enhanced polling cancelled")
                    self.shutdown_requested = True
                    break
                except Exception as e:
                    logger.error(f"Error in enhanced polling loop: {e}")
                    await asyncio.sleep(5)
            
            logger.info("Enhanced bot handler polling stopped gracefully")
    
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
                    logger.info("Enhanced message sent successfully")
        except Exception as e:
            logger.error(f"Error sending enhanced message: {e}")


# Factory function for backward compatibility
def create_enhanced_bot_handler(ollama_url: str = "http://localhost:11434", use_mock_llm: bool = False) -> EnhancedBotHandler:
    """Factory function to create enhanced bot handler."""
    return EnhancedBotHandler(ollama_url, use_mock_llm)