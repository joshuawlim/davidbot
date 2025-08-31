#!/usr/bin/env python3
"""Test script to verify conversational response formatting."""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from davidbot.enhanced_bot_handler import EnhancedBotHandler

async def test_search_formatting():
    """Test that search results use new formatting."""
    print("🧪 Testing Search Response Formatting")
    print("=" * 50)
    
    # Create bot handler with mock LLM to avoid Ollama dependency
    bot = EnhancedBotHandler(use_mock_llm=True)
    
    # Test search
    test_user = "test_user_123"
    search_query = "find songs on joy"
    
    print(f"Query: '{search_query}'")
    print("Response:")
    
    response = await bot.handle_message(test_user, search_query)
    
    if isinstance(response, list):
        for i, message in enumerate(response, 1):
            print(f"\n[Message {i}]")
            print(message)
    else:
        print(response)
    
    print("\n" + "=" * 50)
    print("✅ Test completed - check if chorus/bridge snippets are included")

if __name__ == "__main__":
    asyncio.run(test_search_formatting())