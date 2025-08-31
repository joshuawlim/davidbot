"""Conversational response generator that gives DavidBot natural personality."""

import json
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import SearchResult, Song as BotSong
from .llm_query_parser import ParsedQuery

logger = logging.getLogger(__name__)


class ConversationalResponder:
    """Generates natural, personality-driven responses using LLM."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", use_mock: bool = False):
        """Initialize conversational responder."""
        self.ollama_url = ollama_url
        self.use_mock = use_mock
        self.model_name = None
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self) -> str:
        """Create system prompt for natural conversation generation."""
        return """You are David, a warm and experienced worship leader's assistant with deep ministry heart. Your role is to help worship leaders find the perfect songs for their services with genuine care and spiritual sensitivity.

PERSONALITY TRAITS:
- Kind, helpful, and professional
- Understands worship context without being overly spiritual
- Speaks clearly and directly
- Focuses on practical song recommendations
- Acknowledges requests without excessive enthusiasm

RESPONSE STYLE:
- Concise and to the point
- Friendly but not overly familiar
- Acknowledge what they asked for simply
- Avoid repetitive phrases or excessive adjectives
- Keep responses brief and actionable

SONG PRESENTATION:
- Present songs clearly and practically
- Include relevant musical details
- Minimal commentary unless specifically helpful
- Focus on facts rather than emotional language

FEEDBACK HANDLING:
- Simple acknowledgment of their preference
- Reference song names when appropriate
- Keep responses brief and professional
- Thank them for the feedback without overdoing it

RESPONSE FORMAT:
Always respond with a JSON object containing:
{
    "intro_message": "Natural conversational introduction to the song list",
    "song_presentations": [
        {
            "song_title": "Song Title", 
            "artist": "Artist Name",
            "ministry_note": "Brief natural comment about why this song fits their request"
        }
    ],
    "closing_message": "Natural wrap-up that invites feedback or offers more help"
}

EXAMPLES OF APPROPRIATE LANGUAGE:
- "Here are songs in G for you"
- "These should work for celebration"
- "Good for altar calls"
- "Key of G will work well"
- Brief, practical observations

Remember: Be helpful and concise. Focus on practical song recommendations without excessive personality."""

    async def generate_search_response(self, search_result: SearchResult, parsed_query: ParsedQuery, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate natural conversational response for search results."""
        
        if self.use_mock:
            return self._mock_search_response(search_result, parsed_query)
            
        try:
            # Prepare context for the LLM
            context = {
                "user_request": parsed_query.raw_query,
                "themes": parsed_query.themes,
                "key_preference": parsed_query.key_preference,
                "bpm_range": f"{parsed_query.bpm_min or 'any'}-{parsed_query.bpm_max or 'any'}",
                "mood": parsed_query.mood,
                "song_count": len(search_result.songs),
                "songs": [
                    {
                        "title": song.title,
                        "artist": song.artist, 
                        "key": song.key,
                        "bpm": song.bpm,
                        "tags": song.tags[:3],  # Top 3 tags to avoid overloading
                        "url": song.url
                    }
                    for song in search_result.songs
                ]
            }
            
            prompt = f"""
User asked: "{parsed_query.raw_query}"

Context: {json.dumps(context, indent=2)}

Generate a natural, warm response that:
1. Acknowledges their specific request naturally
2. Presents the songs with ministry context and personal touches
3. Shows understanding of worship leading needs
4. Invites natural feedback

Response must be valid JSON only - no additional text.
"""

            # Get response from LLM
            response_data = await self._call_ollama(prompt)
            
            if response_data:
                return response_data
            else:
                # Fallback to mock response
                logger.warning("LLM response failed, using mock response")
                return self._mock_search_response(search_result, parsed_query)
                
        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            return self._mock_search_response(search_result, parsed_query)
    
    async def generate_feedback_response(self, song_title: str, feedback_type: str, position: int) -> str:
        """Generate natural response to user feedback."""
        
        if self.use_mock:
            return self._mock_feedback_response(song_title, feedback_type)
            
        try:
            prompt = f"""
User gave feedback: {feedback_type} on song "{song_title}" (position {position})

Generate a natural, warm response that:
- Acknowledges the specific song by name
- Shows you understand their taste/preference  
- Responds appropriately to positive/negative feedback
- Maintains encouraging worship leader tone

Respond with just the message text (no JSON, no quotes).
"""
            
            response = await self._call_ollama_simple(prompt)
            return response or self._mock_feedback_response(song_title, feedback_type)
            
        except Exception as e:
            logger.error(f"Error generating feedback response: {e}")
            return self._mock_feedback_response(song_title, feedback_type)
    
    async def _call_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Ollama API for structured JSON response."""
        try:
            model = await self._get_best_model()
            
            payload = {
                "model": model,
                "prompt": f"{self.system_prompt}\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.7,  # More creative for personality
                    "num_predict": 500,
                    "top_k": 40,
                    "top_p": 0.9
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        return None
                    
                    response_data = await response.json()
                    response_text = response_data.get("response", "").strip()
                    
                    # Clean potential markdown formatting
                    if response_text.startswith("```json"):
                        response_text = response_text.replace("```json", "").replace("```", "").strip()
                    
                    return json.loads(response_text)
                    
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return None
    
    async def _call_ollama_simple(self, prompt: str) -> Optional[str]:
        """Call Ollama API for simple text response."""
        try:
            model = await self._get_best_model()
            
            payload = {
                "model": model,
                "prompt": f"You are David, a warm worship leader's assistant. {prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.6,
                    "num_predict": 100
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return None
                    
                    response_data = await response.json()
                    return response_data.get("response", "").strip()
                    
        except Exception as e:
            logger.error(f"Simple Ollama call failed: {e}")
            return None
    
    async def _get_best_model(self) -> str:
        """Get the best available model for conversation."""
        if self.model_name:
            return self.model_name
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags", timeout=aiohttp.ClientTimeout(total=3)) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        
                        # Prefer models good at conversation (fastest first)
                        preferred = [
                            "qwen2.5:3b-instruct",
                            "mistral-small3.1:latest", 
                            "llama3.2:3b",
                            "gpt-oss:latest"
                        ]
                        
                        for model in preferred:
                            if model in models:
                                self.model_name = model
                                return model
                        
                        if models:
                            self.model_name = models[0]
                            return models[0]
        except Exception:
            pass
            
        self.model_name = "gpt-oss:latest"
        return self.model_name
    
    def _mock_search_response(self, search_result: SearchResult, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Generate mock conversational response when LLM unavailable."""
        
        # Brief intro based on request
        if parsed_query.key_preference:
            intro = f"Songs in {parsed_query.key_preference}:"
        elif parsed_query.bpm_max and parsed_query.bpm_max <= 85:
            intro = "Slower songs for ministry:"
        elif parsed_query.bpm_min and parsed_query.bpm_min >= 120:
            intro = "Upbeat songs:"
        elif parsed_query.themes:
            theme_str = ', '.join(parsed_query.themes[:2])
            intro = f"Songs about {theme_str}:"
        else:
            intro = "Song options:"
        
        # Song presentations with brief notes
        song_presentations = []
        ministry_notes = [
            "Good congregational response",
            "Right energy level", 
            "Strong lyrics",
            "Builds well",
            "Good atmosphere",
            "Flows nicely"
        ]
        
        for i, song in enumerate(search_result.songs):
            song_presentations.append({
                "song_title": song.title,
                "artist": song.artist,
                "ministry_note": ministry_notes[i % len(ministry_notes)]
            })
        
        # Brief closing
        closing = "Let me know if you need more options."
        
        return {
            "intro_message": intro,
            "song_presentations": song_presentations,
            "closing_message": closing
        }
    
    def _mock_feedback_response(self, song_title: str, feedback_type: str) -> str:
        """Generate mock feedback response."""
        if feedback_type == "thumbs_up":
            responses = [
                f"Good to know '{song_title}' worked well.",
                f"Thanks, '{song_title}' is a solid choice.",
                f"Glad '{song_title}' fits your needs.",
                f"'{song_title}' noted as a good match."
            ]
        else:
            responses = [
                f"Thanks for the feedback on '{song_title}'.",
                f"Noted about '{song_title}', thanks.",
                f"Got it, '{song_title}' wasn't the right fit.",
                f"Thanks, I'll remember that about '{song_title}'."
            ]
        
        import random
        return random.choice(responses)


def create_conversational_responder(ollama_url: str = "http://localhost:11434", use_mock: bool = False) -> ConversationalResponder:
    """Factory function to create conversational responder."""
    return ConversationalResponder(ollama_url, use_mock)