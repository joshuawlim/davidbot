"""LLM-powered query parser for natural language song search."""

import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuery:
    """Structured representation of a parsed user query."""
    themes: List[str]
    bpm_min: Optional[int] = None
    bpm_max: Optional[int] = None
    key_preference: Optional[str] = None
    mood: Optional[str] = None
    intent: str = "search"
    similarity_song: Optional[str] = None
    exclude_recent: bool = False
    confidence: float = 0.0
    raw_query: str = ""


class LLMQueryParser:
    """Parses natural language queries using Ollama gpt-oss model."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Initialize LLM query parser with Ollama."""
        self.ollama_url = ollama_url
        self.model_name = None  # Will be auto-detected
        self.system_prompt = self._create_system_prompt()
        self._available_models = []
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for query parsing with worship leader personality."""
        return """You are David, an experienced worship leader's assistant who understands the heart of worship ministry. Parse user queries with wisdom and discernment for the house of God.

MINISTRY CONTEXT:
- You serve worship leaders preparing for services, altar calls, and ministry moments
- Common worship themes: surrender, worship, praise, grace, love, peace, hope, faith, joy, redemption, salvation, healing, breakthrough, presence, holy spirit
- BPM guidance: slow/contemplative (60-85) for altar calls and ministry, moderate (86-120) for worship, upbeat (121-160+) for praise and celebration
- Musical keys: A, Bb, B, C, C#, D, Eb, E, F, F#, G, Ab (consider congregation's vocal range)
- "Altar call" = slow, contemplative, surrender/response themes that invite people to draw near to God

WORSHIP LEADER QUERY PATTERNS:
- "upbeat songs for celebration" → themes: ["celebration", "joy"], bpm_min: 120
- "slow songs about grace" → themes: ["grace", "mercy"], bpm_max: 85  
- "something like Amazing Grace" → similarity_song: "Amazing Grace"
- "songs we haven't used lately" → exclude_recent: true
- "praise songs in G for our congregation" → themes: ["praise"], key_preference: "G"
- "need something faster" → increase BPM for energy
- "bring it down slower" → decrease BPM for ministry moments
- "songs for salvation altar call" → themes: ["salvation", "surrender"], bpm_max: 85
- "celebration songs for baptism Sunday" → themes: ["celebration", "new life"], bpm_min: 120

MINISTRY SENSITIVITY:
- "Altar call" language = preparation for God's presence and response
- "Ministry moment" = time for healing, prayer, surrender
- "Celebration" = praise for God's goodness, testimonies, breakthrough
- Be generous with theme matching - the Spirit moves through many expressions
- Default to heart-preparation: when in doubt, choose songs that invite people closer to Jesus

CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no extra text.

REQUIRED JSON FORMAT:
{
    "themes": ["theme1", "theme2"],
    "bpm_min": null,
    "bpm_max": null, 
    "key_preference": null,
    "mood": "upbeat|moderate|slow|contemplative|ministry",
    "intent": "search|more|feedback|unknown",
    "similarity_song": null,
    "exclude_recent": false,
    "confidence": 0.95
}

PARSING RULES:
- Always return valid JSON only - never add explanations
- Include related worship concepts: "healing" includes "restoration", "breakthrough", "freedom"
- Map heart language: "broken" → "surrender", "celebration" → "joy", "thanksgiving" → "gratitude"
- Extract song titles from "like [Title]" or "similar to [Title]" patterns
- Recognize ministry urgency: "need songs now" = high confidence, immediate suggestions
- If unsure, use confidence: 0.5 and intent: "unknown"
"""

    async def _get_best_model(self) -> str:
        """Get the best available model for query parsing."""
        if self.model_name and self.model_name in self._available_models:
            return self.model_name
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags", timeout=aiohttp.ClientTimeout(total=3)) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        self._available_models = models
                        
                        # Preference order for worship song parsing (prioritize structured output)
                        preferred_models = [
                            "mistral-small3.1:latest",  # Better at JSON structured output
                            "qwen2.5:3b-instruct", 
                            "llama3.2:3b",
                            "gpt-oss:latest",
                            "gemma3:12b"
                        ]
                        
                        for preferred in preferred_models:
                            if preferred in models:
                                self.model_name = preferred
                                logger.info(f"Using model: {self.model_name}")
                                return self.model_name
                        
                        # Fallback to first available
                        if models:
                            self.model_name = models[0]
                            logger.info(f"Using fallback model: {self.model_name}")
                            return self.model_name
        except Exception as e:
            logger.error(f"Failed to detect available models: {e}")
        
        # Final fallback
        self.model_name = "gpt-oss:latest"
        return self.model_name

    async def parse(self, query: str, context: Optional[Dict] = None) -> ParsedQuery:
        """Parse natural language query into structured parameters."""
        start_time = datetime.now()
        
        try:
            # Get best available model
            model = await self._get_best_model()
            
            # Add context information if available
            prompt = query
            if context:
                # Filter context to only include JSON-serializable data
                safe_context = {}
                for key, value in context.items():
                    if key not in ['last_updated']:  # Skip datetime objects
                        if isinstance(value, (str, int, float, bool, list, dict)):
                            safe_context[key] = value
                        else:
                            safe_context[key] = str(value)
                
                if safe_context:
                    prompt = f"Previous context: {json.dumps(safe_context)}\nCurrent query: {query}"
            
            # Prepare Ollama API request
            payload = {
                "model": model,
                "prompt": f"{self.system_prompt}\n\nUser: {prompt}\n\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 200,  # Reduced for faster responses
                    "top_k": 20,
                    "top_p": 0.9
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)  # Faster timeout for better UX
                ) as response:
                    if response.status != 200:
                        logger.error(f"Ollama API error: {response.status}")
                        return self._create_fallback_query(query)
                    
                    response_data = await response.json()
                    response_text = response_data.get("response", "").strip()
            
            # Handle potential markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            parsed_data = json.loads(response_text)
            
            # Create ParsedQuery object
            parsed_query = ParsedQuery(
                themes=parsed_data.get("themes", []),
                bpm_min=parsed_data.get("bpm_min"),
                bpm_max=parsed_data.get("bpm_max"),
                key_preference=parsed_data.get("key_preference"),
                mood=parsed_data.get("mood"),
                intent=parsed_data.get("intent", "search"),
                similarity_song=parsed_data.get("similarity_song"),
                exclude_recent=parsed_data.get("exclude_recent", False),
                confidence=parsed_data.get("confidence", 0.0),
                raw_query=query
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"LLM query parsed in {processing_time:.0f}ms: {query} → {len(parsed_query.themes)} themes")
            
            return parsed_query
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {response_text}")
            return self._create_fallback_query(query)
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return self._create_fallback_query(query)
    
    def _create_fallback_query(self, query: str) -> ParsedQuery:
        """Create fallback query when LLM parsing fails."""
        # Simple keyword extraction as fallback
        query_lower = query.lower()
        themes = []
        
        # Basic theme detection
        theme_keywords = {
            'surrender': ['surrender', 'yield', 'give up'],
            'worship': ['worship', 'praise', 'adore'],
            'grace': ['grace', 'mercy', 'forgiveness'],
            'love': ['love', 'beloved'],
            'peace': ['peace', 'calm', 'rest'],
            'joy': ['joy', 'celebration', 'happy'],
            'faith': ['faith', 'trust', 'believe'],
            'hope': ['hope', 'future'],
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                themes.append(theme)
        
        # Extract basic BPM hints
        bpm_min, bpm_max = None, None
        if 'fast' in query_lower or 'upbeat' in query_lower:
            bpm_min = 120
        elif 'slow' in query_lower or 'contemplative' in query_lower:
            bpm_max = 85
        
        return ParsedQuery(
            themes=themes if themes else ['worship'],  # Default theme
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            confidence=0.5,  # Low confidence for fallback
            raw_query=query
        )


class MockLLMQueryParser:
    """Mock parser for testing without API calls."""
    
    async def parse(self, query: str, context: Optional[Dict] = None) -> ParsedQuery:
        """Mock parsing for testing."""
        query_lower = query.lower()
        
        # Check for feedback patterns first
        if ('second' in query_lower and 'perfect' in query_lower) or \
           ('👍' in query) or \
           ('thumbs up' in query_lower) or \
           ('loved' in query_lower):
            return ParsedQuery(
                themes=[],
                intent='feedback',
                confidence=0.9,
                raw_query=query
            )
        
        # Check for 'more' requests
        if query_lower.strip() == 'more':
            return ParsedQuery(
                themes=[],
                intent='more',
                confidence=0.95,
                raw_query=query
            )
        
        # Simple rule-based parsing for search
        themes = []
        bpm_min, bpm_max = None, None
        
        if 'surrender' in query_lower:
            themes.append('surrender')
        if 'worship' in query_lower or 'praise' in query_lower:
            themes.append('worship')
        if 'celebration' in query_lower:
            themes.append('joy')
        if 'grace' in query_lower:
            themes.append('grace')
        
        if 'upbeat' in query_lower or 'fast' in query_lower:
            bpm_min = 120
        elif 'slow' in query_lower:
            bpm_max = 85
        
        return ParsedQuery(
            themes=themes if themes else ['worship'],
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            intent='search',
            confidence=0.8,
            raw_query=query
        )